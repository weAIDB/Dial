# knowledge_process/tide_functional_knowledge.py
# Converts official documentation from any dialect into the Functional dialect knowledge format.
# Matches template_dialect templates (e.g. MySQL) with source_dialect chunks (e.g. DuckDB, PostgreSQL)
# via vector retrieval; LLM merges matched content. Output: @dialect2sql@ blocks for Functional_dialect/.
# Configure TEMPLATE_DIALECT, SOURCE_DIALECT, paths, and LLM in CONFIG.

import os
from pathlib import Path
import torch
from typing import List
from openai import OpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# =============================================================================
# Configuration
# =============================================================================
CONFIG = {
    "template_dialect": os.environ.get("TIDE_TEMPLATE_DIALECT", "MySQL"),
    "source_dialect": os.environ.get("TIDE_SOURCE_DIALECT", "DuckDB"),
    "template_path": os.environ.get("TIDE_TEMPLATE_PATH", ""),
    "source_path": os.environ.get("TIDE_SOURCE_PATH", ""),
    "output_path": os.environ.get("TIDE_OUTPUT_PATH", ""),
    "embedding_model_path": os.environ.get("TIDE_EMBEDDING_MODEL", ""),
    "vector_store_path": os.environ.get("TIDE_VECTOR_STORE_PATH", "./chroma_knowledge_temp"),
    "api_base": os.environ.get("OPENAI_API_BASE", ""),
    "api_key": os.environ.get("OPENAI_API_KEY", ""),
    "model_name": os.environ.get("OPENAI_MODEL", ""),
    "top_k": int(os.environ.get("TIDE_TOP_K", "2")),
}


def extract_chunks(text: str, delimiter: str) -> List[str]:
    """Extract content between delimiters."""
    parts = text.split(delimiter)
    return [p.strip() for i, p in enumerate(parts) if i % 2 == 1 and p.strip()]


def load_file(path: str) -> str:
    """Load text file."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def main():
    print("Starting Functional Knowledge Conversion...")
    print(f"Template: {CONFIG['template_dialect']} -> Target: {CONFIG['source_dialect']}")

    template_path = CONFIG["template_path"]
    source_path = CONFIG["source_path"]
    output_path = CONFIG["output_path"]

    if not template_path or not os.path.isfile(template_path):
        print(f"Error: Template file not found: {template_path}")
        return
    if not source_path or not os.path.isfile(source_path):
        print(f"Error: Source knowledge file not found: {source_path}")
        return
    if not output_path:
        output_path = f"{CONFIG['source_dialect'].lower()}_functional.txt"

    template_chunks = extract_chunks(load_file(template_path), "@dialect2sql@")
    source_chunks = extract_chunks(load_file(source_path), "@dialect2sql@")

    if not source_chunks:
        print(f"Error: Source knowledge empty or invalid @dialect2sql@ format: {source_path}")
        return

    td = CONFIG["template_dialect"]
    sd = CONFIG["source_dialect"]
    client = OpenAI(api_key=CONFIG["api_key"], base_url=CONFIG["api_base"])

    def llm_match_and_merge(template: str, candidate: str) -> str:
        system = f"You are an expert in SQL dialects. Compare {td} template with {sd} candidate."
        user = f"""Task:
1. Determine if the "{sd} Candidate" implements the SAME functional logic as the "{td} Template".
2. IF NO MATCH: Output exactly: NO_MATCH
3. IF MATCH:
   - Generate a combined knowledge block.
   - Keep the Title from the {td} Template (or adapt for {sd}).
   - MANDATORY: Copy "1. Common Scenarios for Using This Syntax in Natural Language Queries" from {td} verbatim.
   - MANDATORY: Copy "2. Relevant Function Description" from {td} verbatim.
   - Implementation: Summarize {sd} syntax. Remove generic fluff. Keep code examples. Mark as {sd} syntax.
   - Output plain text (no markdown blocks).

[{td} Template]
{template}

[{sd} Candidate]
{candidate}

Generate the response:"""
        try:
            r = client.chat.completions.create(
                model=CONFIG["model_name"],
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.1,
            )
            return r.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM Error: {e}")
            return "NO_MATCH"

    device = "cuda" if torch.cuda.is_available() else "cpu"
    embeddings = HuggingFaceEmbeddings(
        model_name=CONFIG["embedding_model_path"],
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True},
    )
    docs = [Document(page_content=c, metadata={"id": i}) for i, c in enumerate(source_chunks)]
    vector_store = Chroma.from_documents(
        docs, embeddings,
        collection_name=f"{sd.lower()}_functional",
        persist_directory=CONFIG["vector_store_path"],
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": CONFIG["top_k"]})

    processed = []
    for idx, template in enumerate(template_chunks):
        title = template.split("\n")[0][:50].strip()
        print(f"[{idx+1}/{len(template_chunks)}] {title}...", end="\r")
        for doc in retriever.invoke(template):
            res = llm_match_and_merge(template, doc.page_content)
            if "NO_MATCH" not in res:
                processed.append(f"@dialect2sql@\n{res}\n@dialect2sql@")
                break

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(processed))
    print(f"\nDone. Saved {len(processed)} entries to {output_path}")


if __name__ == "__main__":
    main()
