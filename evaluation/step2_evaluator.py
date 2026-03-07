# evaluation/step2_evaluator.py
# Step 2: Evaluate execution correctness by comparing predicted vs gold results.
# Score: 0 = not executable, 1 = executable but wrong, 2 = correct.

import math
import pandas as pd
from collections import defaultdict
from typing import List, Dict

from common_utils import logger, load_json


# -----------------------------------------------------------------------------
# Comparison helpers (Spider2-Lite style)
# -----------------------------------------------------------------------------
def vectors_match(v1: List, v2: List, tol: float = 1e-2, ignore_order: bool = True) -> bool:
    """Compare two column vectors; optionally ignore row order."""
    if ignore_order:
        key_func = lambda x: (x is None, str(x), isinstance(x, (int, float)))
        try:
            v1 = sorted(v1, key=key_func)
            v2 = sorted(v2, key=key_func)
        except Exception:
            pass
    if len(v1) != len(v2):
        return False
    for a, b in zip(v1, v2):
        a_isna = pd.isna(a)
        b_isna = pd.isna(b)
        if hasattr(a_isna, "any"):
            a_isna = a_isna.any()
        if hasattr(b_isna, "any"):
            b_isna = b_isna.any()
        if a_isna and b_isna:
            continue
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if not math.isclose(float(a), float(b), abs_tol=tol):
                return False
        elif a != b:
            return False
    return True


def compare_pandas_table(pred_data: List[List], gold_data: List[List]) -> bool:
    """Compare tables by transposing and matching column vectors."""
    try:
        df_pred = pd.DataFrame(pred_data)
        df_gold = pd.DataFrame(gold_data)
    except Exception:
        return False
    if df_pred.empty and df_gold.empty:
        return True
    if len(df_pred) != len(df_gold):
        return False
    if df_pred.shape[1] < df_gold.shape[1]:
        return False
    t_gold = df_gold.transpose().values.tolist()
    t_pred = df_pred.transpose().values.tolist()
    for gold_col in t_gold:
        if not any(vectors_match(gold_col, pred_col) for pred_col in t_pred):
            return False
    return True


# -----------------------------------------------------------------------------
# Evaluation scores per engine
# -----------------------------------------------------------------------------
def get_evaluation_scores(pred_file: str, gold_file: str) -> Dict[str, Dict[str, int]]:
    """
    Returns: { engine: { qid: score } }
    Score: 0 = not executable, 1 = executable but wrong, 2 = correct.
    """
    logger.info("[Step 2] Evaluating: %s", pred_file)
    preds = load_json(pred_file)
    golds = load_json(gold_file)
    if not preds or not golds:
        logger.warning("Prediction or gold data is empty.")
        return {}

    gold_map = {str(item["question_id"]): item for item in golds if item.get("question_id")}
    pred_map = defaultdict(dict)
    for item in preds:
        qid = str(item.get("question_id"))
        engine = item.get("engine")
        if qid and engine:
            pred_map[engine][qid] = item

    all_scores = {}
    for engine, engine_preds in pred_map.items():
        scores = {}
        count_2 = 0
        count_1_or_2 = 0
        total = 0
        common_qids = set(engine_preds.keys()) & set(gold_map.keys())

        for qid in common_qids:
            total += 1
            pred_item = engine_preds[qid]
            gold_item = gold_map[qid]
            p_res = pred_item.get("result", {})
            g_res = gold_item.get("result", {})

            if p_res.get("status") != "success":
                score = 0
            else:
                same = compare_pandas_table(
                    p_res.get("data", []),
                    g_res.get("data", []),
                )
                score = 2 if same else 1
            scores[qid] = score
            if score == 2:
                count_2 += 1
                count_1_or_2 += 1
            elif score == 1:
                count_1_or_2 += 1

        acc = (count_2 / total * 100) if total > 0 else 0
        exec_rate = (count_1_or_2 / total * 100) if total > 0 else 0
        logger.info(
            "[Step 2] %s | Correct: %s (%.2f%%) | Executable: %s (%.2f%%) | Total: %s",
            engine, count_2, acc, count_1_or_2, exec_rate, total,
        )
        all_scores[engine] = scores
    return all_scores
