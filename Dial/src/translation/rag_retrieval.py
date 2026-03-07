# rag_retrieval.py
import re
import os
import numpy as np
from .config import RULES_ROOT_DIR, FUNCTIONAL_ROOT_DIR, DB_TYPE_TO_RULE_FILE, MAGIC_SIMILARITY_THRESHOLD
from src.knowledge.rag_retriever import (
    embedding_model,
    HomyMarkerSplitter,
    format_retrieval_result,
)
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import TextLoader
from operator import itemgetter
from langchain_core.runnables import RunnablePassthrough


def secondary_rag_retrieval(question, error_msg, db_type, error_analysis=None):
    """
    Secondary RAG Retrieval (Enhanced Version)
    Features:
    1. Prioritize keywords from Error Analysis.
    2. Automatic fallback mechanism: If score_threshold retrieval fails, automatically switch back to normal retrieval to prevent crashes.
    """
    try:
        # === 1. Construct Intelligent Query ===
        if error_analysis and isinstance(error_analysis, dict):
            # Extract information
            inferred_reason = error_analysis.get("inferred_reason", "")
            keywords = error_analysis.get("suggested_keywords", [])
            error_code = error_analysis.get("error_code", "")
            
            # Place keywords at the front for higher weight
            keywords_str = " ".join(keywords) if keywords else ""
            
            # Query format: "Oracle ORA-01861 Implicit Conversion ... Reason: ..."
            retrieval_query = (
                f"{db_type} {error_code} {keywords_str} "
                f"Reason: {inferred_reason[:150]}"
            )
            print(f"   🔎 [RAG] Intelligent Retrieval Query: {retrieval_query}")
        else:
            # Fallback Query
            retrieval_query = f"{db_type} SQL Error: {error_msg[:200]}"
            print(f"   🔎 [RAG] Normal Retrieval Query: {retrieval_query}")

        # === 2. Load Specific Rule File ===
        # Note: We specifically load the rule file for this DB
        rule_filename = DB_TYPE_TO_RULE_FILE.get(db_type, f"{db_type}.txt")
        rule_file_path = os.path.join(RULES_ROOT_DIR, rule_filename)
        
        if not os.path.exists(rule_file_path):
            print(f"   ⚠️ Rule file does not exist: {rule_file_path}")
            return "No relevant syntax reference"

        loader = TextLoader(rule_file_path, encoding='utf-8')
        docs = loader.load()
        if not docs:
            return "No relevant syntax reference"

        # === 3. Build Temporary Vector Index ===
        text_splitter = HomyMarkerSplitter()
        split_docs = text_splitter.split_documents(docs)
        
        # Use temporary Chroma instance (not persisted, only for this retrieval)
        temp_vector_store = Chroma.from_documents(
            documents=split_docs,
            embedding=embedding_model,
            collection_name=f"temp_rag_{os.getpid()}_{np.random.randint(0,1000)}" # Random name to avoid conflict
        )

        # === 4. Retriever Configuration (Core Fix: Automatic Fallback) ===
        retriever = None
        
        # Strategy A: Try preferred plan (Similarity retrieval with threshold)
        try:
            # Some older versions of LangChain/Chroma might not support search_type="similarity_score_threshold"
            retriever = temp_vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={"score_threshold": 0.5, "k": 2}
            )
        except Exception:
            retriever = None

        # Strategy B: Fallback plan (Normal KNN retrieval)
        if retriever is None:
            # print("   ⚠️ Configuration Fallback: Using normal K-NN retrieval...")
            retriever = temp_vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 4}
            )

        # === 5. Execute Retrieval Chain ===
        chain = (
            {"question": RunnablePassthrough()}
            | RunnablePassthrough.assign(context=itemgetter("question") | retriever)
            | format_retrieval_result
            | StrOutputParser()
        )

        # Execute invoke and catch runtime parameter errors
        try:
            retrieval_result = chain.invoke(retrieval_query)
        except Exception as e:
            # If runtime error contains score_threshold (usually LangChain passing through to Chroma)
            if "score_threshold" in str(e) or "unexpected keyword" in str(e):
                print("   ⚠️ Runtime Fallback: Parameter not supported detected, retrying normal retrieval...")
                fallback_retriever = temp_vector_store.as_retriever(search_kwargs={"k": 4})
                chain_fallback = (
                    {"question": RunnablePassthrough()}
                    | RunnablePassthrough.assign(context=itemgetter("question") | fallback_retriever)
                    | format_retrieval_result
                    | StrOutputParser()
                )
                retrieval_result = chain_fallback.invoke(retrieval_query)
            else:
                raise e # Throw other unknown errors

        # === 6. Result Cleanup and Processing ===
        # Try to clean up temporary Collection
        try:
            temp_vector_store.delete_collection()
        except:
            pass

        # Null check processing for results
        if "No relevant content retrieved" in retrieval_result:
            if error_analysis:
                # If intelligent Query finds nothing, try searching with original error (Fallback)
                print("   ⚠️ Intelligent retrieval missed, attempting original error retrieval...")
                try:
                    fallback_res = chain.invoke(f"{db_type} {error_msg[:100]}")
                    if "No relevant content retrieved" not in fallback_res:
                        retrieval_result = fallback_res
                except:
                    pass

        # Format output (take top 2)
        chunk_pattern = r'=== Relevant Chunk (\d+): (.*?) ===\n([\s\S]*?)(?=\n=== |$)'
        matches = re.findall(chunk_pattern, retrieval_result, re.DOTALL)
        
        formatted_chunks = []
        for i, (_, title, content) in enumerate(matches[:2], 1):
            content = content.strip()
            if len(content) > 1500: content = content[:11500] + "..."
            formatted_chunks.append(f"=== Reference Solution {i}: {title} ===\n{content}")

        if not formatted_chunks:
            return "=== Relevant Syntax Reference ===\nNo relevant content retrieved."
            
        return "\n\n".join(formatted_chunks)

    except Exception as e:
        print(f"   ⚠️ Secondary Retrieval Critical Error: {str(e)[:100]}")
        # Return friendly error message, do not interrupt main flow
        return f"=== Relevant Syntax Reference ===\n(Retrieval system temporarily unavailable, suggest fixing based on the following diagnosis: {error_analysis.get('inferred_reason', 'Unknown') if error_analysis else error_msg[:100]})"

# Helper functions remain unchanged
def calculate_cosine_similarity(text1, text2):
    try:
        vec1 = embedding_model.embed_query(text1)
        vec2 = embedding_model.embed_query(text2)
        dot_product = np.dot(vec1, vec2)
        norm_a = np.linalg.norm(vec1)
        norm_b = np.linalg.norm(vec2)
        return dot_product / (norm_a * norm_b) if norm_a * norm_b != 0 else 0.0
    except:
        return 0.0

def save_magic_guideline(guideline_text, nl2_rewrite, db_type):
    if not guideline_text: return
    similarity = calculate_cosine_similarity(guideline_text, nl2_rewrite)
    target_dir = FUNCTIONAL_ROOT_DIR if similarity >= MAGIC_SIMILARITY_THRESHOLD else RULES_ROOT_DIR
    filename = DB_TYPE_TO_RULE_FILE.get(db_type, f"{db_type}.txt")
    file_path = os.path.join(target_dir, filename)
    try:
        if not os.path.exists(target_dir): os.makedirs(target_dir)
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write("\n\n" + guideline_text)
    except:
        pass