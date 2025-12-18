import pandas as pd
import math
from collections import defaultdict
from typing import List, Dict, Any
from common_utils import logger, load_json


def vectors_match(v1: List, v2: List, tol=1e-2, ignore_order=True) -> bool:
    """Spider2-Lite 核心逻辑：列向量对比"""
    if ignore_order:
        key_func = lambda x: (x is None, str(x), isinstance(x, (int, float)))
        try:
            v1 = sorted(v1, key=key_func)
            v2 = sorted(v2, key=key_func)
        except Exception:
            pass  # 如果排序失败，尝试直接对比

    if len(v1) != len(v2): return False
    for a, b in zip(v1, v2):
        if pd.isna(a) and pd.isna(b):
            continue
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if not math.isclose(float(a), float(b), abs_tol=tol): return False
        elif a != b:
            return False
    return True


def compare_pandas_table(pred_data: List[List], gold_data: List[List]) -> bool:
    """转置表格，按列无序对比"""
    try:
        df_pred = pd.DataFrame(pred_data)
        df_gold = pd.DataFrame(gold_data)
    except Exception:
        return False

    if df_pred.empty and df_gold.empty: return True
    if len(df_pred) != len(df_gold): return False  # 行数必须一致
    if df_pred.shape[1] < df_gold.shape[1]: return False  # 列数不能少于标准答案

    t_gold = df_gold.transpose().values.tolist()
    t_pred = df_pred.transpose().values.tolist()

    for gold_col in t_gold:
        if not any(vectors_match(gold_col, pred_col) for pred_col in t_pred):
            return False
    return True


def get_evaluation_scores(pred_file: str, gold_file: str) ->  Dict[str, Dict[str, int]]:
    """
    返回结构:
    {
        engine: {
            qid: score
        }
    }

    score:
        0 = 不可执行
        1 = 可执行但结果不一致
        2 = 完全正确
    """
    logger.info(f"[Step 2] 正在评估: {pred_file}")

    preds = load_json(pred_file)
    golds = load_json(gold_file)

    if not preds or not golds:
        logger.warning("预测结果或标准答案为空")
        return {}

    # ===== 标准答案：只按 question_id =====
    gold_map = {
        str(item['question_id']): item
        for item in golds
        if item.get('question_id')
    }

    # ===== 预测结果：按 engine + question_id =====
    pred_map = defaultdict(dict)
    for item in preds:
        qid = str(item.get('question_id'))
        engine = item.get('engine')
        if qid and engine:
            pred_map[engine][qid] = item

    all_scores: Dict[str, Dict[str, int]] = {}

    # ===== 按方言逐个评估 =====
    for engine, engine_preds in pred_map.items():
        logger.info(f"[Step 2] 评估方言: {engine}")

        scores = {}

        count_2 = 0
        count_1_or_2 = 0
        total = 0

        common_qids = set(engine_preds.keys()) & set(gold_map.keys())

        for qid in common_qids:
            total += 1

            pred_item = engine_preds[qid]
            gold_item = gold_map[qid]

            p_res = pred_item.get('result', {})
            g_res = gold_item.get('result', {})

            if p_res.get('status') != 'success':
                score = 0
            else:
                same = compare_pandas_table(
                    p_res.get('data', []),
                    g_res.get('data', [])
                )
                score = 2 if same else 1

            scores[qid] = score

            if score == 2:
                count_2 += 1
                count_1_or_2 += 1
            elif score == 1:
                count_1_or_2 += 1

            # 计算百分比，确保 total 不为 0
            acc = (count_2 / total * 100) if total > 0 else 0
            exec_rate = (count_1_or_2 / total * 100) if total > 0 else 0

            logger.info(
                f"[Step 2] {engine} | "
                f"正确: {count_2} ({acc:.2f}%) | "
                f"可执行: {count_1_or_2} ({exec_rate:.2f}%) | "
                f"总数: {total}"
            )

        all_scores[engine] = scores

    return all_scores