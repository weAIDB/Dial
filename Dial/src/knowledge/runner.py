# src/knowledge/runner.py
# Run RAG retrieval on tagged NL-LQP output for each target dialect.
# Uses final_NL_{dialect}.NL-LQP as query, saves per-dialect result JSON for translation.

import json
import shutil
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm

import sys
_DIAL_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_DIAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_DIAL_ROOT))
from conf import (
    DIALECT_AWARE_LQP_OUTPUT_JSON,
    RAG_OUTPUT_BASE_DIR,
    RESULT_JSON_PATH,
    TARGET_DIALECTS,
)
from src.knowledge.rag_retriever import MultiDBDocumentRetriever


def load_input_data(file_path: str, target_dialect: str) -> List[Dict]:
    """Load combined LQP JSON; return items that have final_NL_{target_dialect} with NL-LQP."""
    path = Path(file_path)
    if not path.exists():
        print(f"Warning: File does not exist: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("Input JSON must be an array")
        return []
    target_key = f"final_NL_{target_dialect}"
    valid_data = [
        item for item in data
        if isinstance(item, dict)
        and isinstance(item.get(target_key), dict)
        and "NL-LQP" in item.get(target_key, {})
    ]
    print(f"[{target_dialect}] Valid items: {len(valid_data)}/{len(data)}")
    return valid_data


def process_rag_for_dialect(
    retriever: MultiDBDocumentRetriever,
    input_data: List[Dict],
    target_dialect: str,
) -> List[Dict]:
    """Run RAG for each item using final_NL_{dialect}.NL-LQP as query."""
    results = []
    target_key = f"final_NL_{target_dialect}"
    for item in tqdm(input_data, desc=f"RAG {target_dialect}"):
        try:
            final_nl_obj = item.get(target_key, {})
            nl_lqp_text = final_nl_obj.get("NL-LQP", "") or ""
            if not isinstance(nl_lqp_text, str):
                nl_lqp_text = str(nl_lqp_text)
            if nl_lqp_text.strip():
                db_retrieval_results = retriever.retrieve_from_all_dbs(nl_lqp_text)
            else:
                db_retrieval_results = {
                    db: "Error: Empty NL-LQP Query"
                    for db in ["MySQL", "Oracle", "PostgreSQL", "SQL Server", "SQLite"]
                }
            results.append({
                "question_id": item.get("question_id"),
                "db_id": item.get("db_id", ""),
                "question": item.get("question", ""),
                "dialect_type": target_dialect,
                "used_query_source": f"{target_key}['NL-LQP']",
                "nl2_rewrite": nl_lqp_text,
                "steps_count": final_nl_obj.get("Steps Count", {}),
                "difficulty": item.get("hardness", item.get("difficulty", "")),
                "true_tables_columns": item.get("true_tables_columns", ""),
                "retrieval_results": db_retrieval_results,
            })
        except Exception as e:
            print(f"Item {item.get('question_id')} failed: {e}")
            results.append({
                "question_id": item.get("question_id"),
                "question": item.get("question", ""),
                "nl2_rewrite": "ERROR",
                "retrieval_results": {},
                "error": str(e),
            })
    return results


def run_all_dialects(
    input_json: str = None,
    output_dir: Path = None,
    target_dialects: List[str] = None,
) -> List[Path]:
    """Run RAG for each target dialect; save one JSON per dialect."""
    input_json = input_json or DIALECT_AWARE_LQP_OUTPUT_JSON
    output_dir = Path(output_dir or RAG_OUTPUT_BASE_DIR)
    target_dialects = target_dialects or TARGET_DIALECTS
    print("Initializing multi-DB retriever...")
    retriever = MultiDBDocumentRetriever()
    output_paths = []
    for dialect in target_dialects:
        input_data = load_input_data(input_json, dialect)
        if not input_data:
            continue
        results = process_rag_for_dialect(retriever, input_data, dialect)
        out_path = output_dir / f"{dialect}_lqp_rag_result.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Saved to {out_path.name}")
        output_paths.append(out_path)
    return output_paths


def merge_rag_results_to_single_file(
    result_files: List[Path],
    output_path: str = None,
    target_dialect: str = None,
) -> str:
    """Merge RAG results to output_path for translation input.

    If target_dialect is specified, uses only that dialect's result.
    Otherwise merges all dialects: each item has per_dialect data keyed by dialect.
    """
    output_path = output_path or RESULT_JSON_PATH
    if not result_files:
        return output_path
    out_dir = Path(output_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    if target_dialect:
        # Use single dialect: find matching file
        for pf in result_files:
            if pf.stem.startswith(f"{target_dialect}_"):
                with open(pf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return output_path
        # Fallback to first file if dialect not found
        shutil.copy(result_files[0], output_path)
        return output_path

    # Merge all dialects by question_id
    qid_to_item: Dict = {}
    dialect_to_key = {}  # file stem prefix -> dialect
    for pf in result_files:
        stem = pf.stem
        dialect = stem.replace("_lqp_rag_result", "") if "_lqp_rag_result" in stem else stem
        dialect_to_key[pf] = dialect
    for pf in result_files:
        dialect = dialect_to_key[pf]
        with open(pf, "r", encoding="utf-8") as f:
            items = json.load(f)
        for item in items:
            qid = item.get("question_id")
            if qid not in qid_to_item:
                qid_to_item[qid] = {
                    "question_id": qid,
                    "question": item.get("question", ""),
                    "db_id": item.get("db_id", ""),
                    "true_tables_columns": item.get("true_tables_columns", ""),
                    "difficulty": item.get("difficulty"),
                    "per_dialect": {},
                }
            qid_to_item[qid]["per_dialect"][dialect] = {
                "nl2_rewrite": item.get("nl2_rewrite", ""),
                "retrieval_results": item.get("retrieval_results", {}),
            }
    merged = list(qid_to_item.values())
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    return output_path


def main():
    output_paths = run_all_dialects()
    print("RAG retrieval done. Outputs:", [str(p) for p in output_paths])
    if output_paths:
        import os
        target_dialect = os.environ.get("DIAL_TRANSLATION_DIALECT", "").strip() or None
        merge_rag_results_to_single_file(
            output_paths, output_path=RESULT_JSON_PATH, target_dialect=target_dialect
        )
        print(f"Translation input: {RESULT_JSON_PATH}" + (f" (dialect={target_dialect})" if target_dialect else " (merged all dialects)"))


if __name__ == "__main__":
    main()
