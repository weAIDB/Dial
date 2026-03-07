# knowledge_process/tide_rule.py
# Converts official documentation from any dialect into Rule + Functional dialect knowledge.
# Three phases: (1) Functional matching, (2) Rule-based matching, (3) Residual dialect scanning.
# Template dialect (e.g. MySQL) provides structure; source dialect (e.g. DuckDB, PostgreSQL)
# is the target. Output: @dialect2sql@ blocks for Rule_based_dialect/ and Functional_dialect/.
# Configure TEMPLATE_DIALECT, SOURCE_DIALECT, paths, and LLM in CONFIG.

import os
from pathlib import Path
from typing import List, Set
import torch
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
    "template_func_path": os.environ.get("TIDE_TEMPLATE_FUNC_PATH", ""),
    "template_rule_path": os.environ.get("TIDE_TEMPLATE_RULE_PATH", ""),
    "source_path": os.environ.get("TIDE_SOURCE_PATH", ""),
    "output_func_path": os.environ.get("TIDE_OUTPUT_FUNC_PATH", ""),
    "output_rule_path": os.environ.get("TIDE_OUTPUT_RULE_PATH", ""),
    "embedding_model_path": os.environ.get("TIDE_EMBEDDING_MODEL", ""),
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


def wrap_block(content: str) -> str:
    """Format block with @dialect2sql@ delimiters."""
    return f"@dialect2sql@\n{content}\n@dialect2sql@"


def main():
    td = CONFIG["template_dialect"]
    sd = CONFIG["source_dialect"]
    print("Starting Three-Phase Dialect Knowledge Conversion...")
    print(f"Template: {td} -> Target: {sd}")

    client = OpenAI(api_key=CONFIG["api_key"], base_url=CONFIG["api_base"])

    def llm_phase1_functional(template: str, candidate: str) -> str:
        """Phase 1: Functional matching."""
        system = f"You are a Database Expert. Analyze if the {sd} syntax implements the SAME FUNCTION as the {td} template."
        user = f"""Task: Check if "{sd} Candidate" implements the SAME functional logic as "{td} Template".
1. IF NO MATCH: Output "NO_MATCH".
2. IF MATCH:
   - Generate a combined block.
   - MANDATORY: Copy "1. Common Scenarios for Using This Syntax in Natural Language Queries" from {td} verbatim.
   - MANDATORY: Copy "2. Relevant Function Description" from {td} verbatim.
   - Implementation: Summarize {sd} syntax. Remove generic fluff. Keep code examples.
   - Output plain text (no markdown blocks).

[{td} Template]
{template}

[{sd} Candidate]
{candidate}
"""
        try:
            r = client.chat.completions.create(
                model=CONFIG["model_name"],
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.1,
            )
            return r.choices[0].message.content.strip()
        except Exception:
            return "NO_MATCH"

    def llm_phase2_rule(template: str, candidate: str) -> str:
        """Phase 2: Rule-based matching."""
        system = f"You are a Database Kernel Engineer. Compare {td} strict syntax rules with {sd}."
        user = f"""Task: Compare "{td} Rule" with "{sd} Candidate".
1. Does the {sd} candidate discuss the SAME syntactic category (Quoting, Aliases, Literals, Data Types, etc.)?
2. IF NO MATCH: Output "NO_MATCH".
3. IF MATCH:
   - Title: Use the {td} Title.
   - Content: Explain the {sd} implementation.
   - CRITICAL: Highlight DIFFERENCES vs {td} (e.g. "Unlike {td}, {sd} allows...").
   - Provide {sd} syntax examples. Output plain text.

[{td} Rule]
{template}

[{sd} Candidate]
{candidate}
"""
        try:
            r = client.chat.completions.create(
                model=CONFIG["model_name"],
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.1,
            )
            return r.choices[0].message.content.strip()
        except Exception:
            return "NO_MATCH"

    def llm_phase3_residual(chunk: str) -> str:
        """Phase 3: Residual dialect scanning."""
        system = f"You are a Dialect Hunter. Find syntax where {sd} behaves DIFFERENTLY from other DBs."
        user = f"""Analyze this {sd} knowledge chunk.
Strictly determine if it describes a DIALECT DIFFERENCE or UNIQUE FEATURE vs standard SQL or other DBs ({td}, PostgreSQL).

KEEP if:
- It explicitly compares {sd} to others ("Unlike {td}...", "Standard SQL requires...").
- Or describes {sd}-specific behavior (e.g. 0-based vs 1-based indexing, casting rules).

SKIP if:
- Standard function description without dialect differences.

Output:
- If SKIP: Output exactly "SKIP".
- If KEEP: Title "Dialect Feature: [Name]", emphasize the DIFFERENCE, show syntax. Plain text.

[{sd} Chunk]
{chunk}
"""
        try:
            r = client.chat.completions.create(
                model=CONFIG["model_name"],
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.1,
            )
            return r.choices[0].message.content.strip()
        except Exception:
            return "SKIP"

    template_func = load_file(CONFIG["template_func_path"])
    template_rule = load_file(CONFIG["template_rule_path"])
    source_raw = load_file(CONFIG["source_path"])

    func_chunks = extract_chunks(template_func, "@dialect2sql@")
    rule_chunks = extract_chunks(template_rule, "@dialect2sql@")
    source_chunks = extract_chunks(source_raw, "@dialect2sql@")

    if not source_chunks:
        print(f"Error: Source knowledge empty or invalid: {CONFIG['source_path']}")
        return

    out_func = CONFIG["output_func_path"] or f"{sd.lower()}_functional.txt"
    out_rule = CONFIG["output_rule_path"] or f"{sd.lower()}_rule.txt"

    device = "cuda" if torch.cuda.is_available() else "cpu"
    embeddings = HuggingFaceEmbeddings(
        model_name=CONFIG["embedding_model_path"],
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True},
    )
    docs = [Document(page_content=c, metadata={"id": i}) for i, c in enumerate(source_chunks)]
    vector_store = Chroma.from_documents(
        docs, embeddings,
        collection_name=f"{sd.lower()}_tide",
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": CONFIG["top_k"]})
    used_ids: Set[int] = set()

    # Phase 1: Functional
    phase1 = []
    for i, template in enumerate(func_chunks):
        print(f"Phase1 ({i+1}/{len(func_chunks)})...", end="\r")
        for doc in retriever.invoke(template):
            res = llm_phase1_functional(template, doc.page_content)
            if "NO_MATCH" not in res:
                phase1.append(wrap_block(res))
                used_ids.add(doc.metadata["id"])
                break

    Path(out_func).parent.mkdir(parents=True, exist_ok=True)
    with open(out_func, "w", encoding="utf-8") as f:
        f.write("\n\n".join(phase1))
    print(f"Phase1 done: {len(phase1)} entries -> {out_func}")

    # Phase 2: Rule-based
    phase2 = []
    for i, template in enumerate(rule_chunks):
        print(f"Phase2 ({i+1}/{len(rule_chunks)})...", end="\r")
        for doc in retriever.invoke(template):
            res = llm_phase2_rule(template, doc.page_content)
            if "NO_MATCH" not in res:
                phase2.append(wrap_block(res))
                used_ids.add(doc.metadata["id"])
                break

    # Phase 3: Residual
    phase3 = []
    remaining = [i for i in range(len(source_chunks)) if i not in used_ids]
    for i, idx in enumerate(remaining):
        if len(source_chunks[idx]) < 50:
            continue
        print(f"Phase3 ({i+1}/{len(remaining)})...", end="\r")
        res = llm_phase3_residual(source_chunks[idx])
        if "SKIP" not in res:
            phase3.append(wrap_block(res))

    Path(out_rule).parent.mkdir(parents=True, exist_ok=True)
    with open(out_rule, "w", encoding="utf-8") as f:
        f.write("\n\n".join(phase2 + phase3))
    print(f"Phase2+3 done: {len(phase2)}+{len(phase3)} entries -> {out_rule}")
    print("Done.")


if __name__ == "__main__":
    main()
