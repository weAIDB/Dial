# src/knowledge/rag_retriever.py
# HINT-KB: Multi-dialect RAG over Rule_based_dialect and Functional_dialect knowledge.
# Provides MultiDBDocumentRetriever, embedding_model, DialectMarkerSplitter, format_retrieval_result
# for both primary (nl2rag) and secondary (error-driven) retrieval.

from operator import itemgetter
from pathlib import Path
from typing import List, Dict

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.document_loaders import TextLoader
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import TextSplitter

import sys
_DIAL_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_DIAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_DIAL_ROOT))
from conf import RAG_KNOWLEDGE_ROOT, RAG_VECTOR_STORE_ROOT, RAG_EMBEDDING_MODEL_PATH, DB_TYPE_TO_RULE_FILE


class DialectMarkerSplitter(TextSplitter):
    """Split dialect knowledge by @dialect2sql@ marker; first line of each chunk as title."""

    def split_text(self, text: str) -> List[str]:
        doc = Document(page_content=text, metadata={})
        split_docs = self.split_documents([doc])
        return [d.page_content for d in split_docs]

    def split_documents(self, documents: List[Document]) -> List[Document]:
        split_docs = []
        for doc in documents:
            chunks = [c.strip() for c in doc.page_content.split("@dialect2sql@") if c.strip()]
            for chunk in chunks:
                lines = [line.strip() for line in chunk.splitlines() if line.strip()]
                title = lines[0] if lines else "No Title"
                split_docs.append(Document(
                    page_content=chunk,
                    metadata={
                        **doc.metadata,
                        "title": title,
                        "source": doc.metadata.get("source", "Unknown Source"),
                    },
                ))
        return split_docs


HomyMarkerSplitter = DialectMarkerSplitter

DB_TYPE_MAPPING = {k: v for k, v in DB_TYPE_TO_RULE_FILE.items()}


def _get_embedding_model():
    return HuggingFaceEmbeddings(
        model_name=RAG_EMBEDDING_MODEL_PATH,
        model_kwargs={
            "device": "cuda" if __import__("torch").cuda.is_available() else "cpu",
            "trust_remote_code": True,
        },
        encode_kwargs={"normalize_embeddings": True},
    )


embedding_model = _get_embedding_model()
text_splitter = DialectMarkerSplitter()


def format_retrieval_result(result: dict) -> str:
    """Format retrieved chunks for prompt injection."""
    context_docs = result.get("context", [])
    if not context_docs:
        return "No relevant content retrieved"
    formatted = []
    for i, doc in enumerate(context_docs, 1):
        title = doc.metadata.get("title", "No Title")
        content = doc.page_content
        truncated = content[:12700] + "..." if len(content) > 12700 else content
        formatted.append(f"=== Relevant Chunk {i}: {title} ===\n{truncated}")
    return "\n\n".join(formatted)


class MultiDBDocumentRetriever:
    """Per-database vector stores over dialect rule files; retrieves from all DBs for a query."""

    def __init__(self, knowledge_root: Path = None, vector_store_root: Path = None):
        self.knowledge_root = knowledge_root or RAG_KNOWLEDGE_ROOT
        self.vector_store_root = Path(vector_store_root or RAG_VECTOR_STORE_ROOT)
        self.embedding_model = embedding_model
        self.text_splitter = text_splitter
        self.db_retrievers: Dict[str, Chroma] = {}
        self._init_vector_stores()

    def _init_vector_stores(self):
        for db_type, filename in DB_TYPE_MAPPING.items():
            db_vector_dir = self.vector_store_root / db_type
            db_vector_dir.mkdir(parents=True, exist_ok=True)
            vector_store = Chroma(
                embedding_function=self.embedding_model,
                persist_directory=str(db_vector_dir),
            )
            retriever = vector_store.as_retriever(search_kwargs={"k": 5})
            self.db_retrievers[db_type] = retriever
            self._load_db_documents(db_type, filename, vector_store)

    def _load_db_documents(self, db_type: str, filename: str, vector_store: Chroma):
        file_path = Path(self.knowledge_root) / filename
        if not file_path.exists():
            print(f"Warning: {db_type} knowledge file not found: {file_path}")
            return
        try:
            count = vector_store._collection.count()
        except Exception:
            count = 0
        if count > 0:
            print(f"{db_type} vector store already has {count} chunks, skipping load")
            return
        loader = TextLoader(str(file_path), encoding="utf-8")
        docs = loader.load()
        split_docs = self.text_splitter.split_documents(docs)
        vector_store.add_documents(split_docs)
        print(f"{db_type} loaded {len(split_docs)} chunks")

    def retrieve_from_all_dbs(self, query: str) -> Dict[str, str]:
        """Retrieve from each DB vector store; return dict DB -> formatted string."""
        all_results = {}
        for db_type, retriever in self.db_retrievers.items():
            single_chain = (
                {"question": RunnablePassthrough()}
                | RunnablePassthrough.assign(context=itemgetter("question") | retriever)
                | format_retrieval_result
                | StrOutputParser()
            )
            result = single_chain.invoke(query)
            all_results[db_type] = result
        return all_results
