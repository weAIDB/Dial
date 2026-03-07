# evaluation/run_pipeline.py
# Main pipeline: Step1 (execute SQL) -> Step2 (evaluate accuracy) -> Step3 (calculate DFC).
# Produces per-task per-engine results and a final Excel summary.

import os
import sys
from pathlib import Path

# Ensure evaluation package root is on path when run as script
_ev_root = Path(__file__).resolve().parent
if str(_ev_root) not in sys.path:
    sys.path.insert(0, str(_ev_root))

import pandas as pd
import numpy as np
from collections import OrderedDict

from config import (
    DB_CONFIG,
    PIPELINE_TASKS,
    FINAL_EXCEL_PATH,
    GOLD_RESULT_FILE,
    EXECUTE_ENGINES,
)
from common_utils import logger, load_json, save_json
from step1_executor import run_execution
from step2_evaluator import get_evaluation_scores
from step3_dfc import calculate_dfc_entry


def main():
    logger.info("=== Evaluation pipeline (Execute -> Evaluate -> DFC) ===")

    report_data = OrderedDict()
    if not os.path.exists(GOLD_RESULT_FILE):
        logger.error("Gold result file not found: %s", GOLD_RESULT_FILE)
        return

    raw_gold_data = load_json(GOLD_RESULT_FILE)
    gold_map = {str(item["question_id"]): item for item in raw_gold_data}

    for task in PIPELINE_TASKS:
        task_name = task["name"]
        input_sql_path = task["input_sql"]
        output_base = task["output_exec"]
        logger.info(">>> Processing task: %s", task_name)

        for engine in EXECUTE_ENGINES:
            name_part, ext_part = os.path.splitext(output_base)
            engine_output_file = f"{name_part}_{engine}{ext_part}"

            success = run_execution(
                input_sql_path,
                engine_output_file,
                DB_CONFIG,
                target_engine=engine,
            )
            if not success:
                logger.warning("[%s] Engine %s execution failed, skipping", task_name, engine)
                continue

            eval_scores = get_evaluation_scores(engine_output_file, GOLD_RESULT_FILE)
            logger.info("[Step 3] Computing DFC metrics: %s", engine)

            pred_data = load_json(engine_output_file)
            dfc_list = []

            for item in pred_data:
                qid = str(item.get("question_id"))
                score = eval_scores.get(engine, {}).get(qid, 0)
                pred_sql = item.get("generated_sql", "")
                gold_sql = item.get("gold_sql", "")

                if not gold_sql:
                    logger.warning("QID %s missing Gold SQL for engine %s", qid, engine)

                dfc_val, dfc_details = calculate_dfc_entry(gold_sql, pred_sql, engine, score)
                item["eval_score"] = score
                item["dfc_score"] = dfc_val
                item["dfc_details"] = dfc_details
                if dfc_val is not None:
                    dfc_list.append(dfc_val)

            save_json(pred_data, engine_output_file)

            scores_arr = list(eval_scores.get(engine, {}).values())
            total = len(scores_arr)
            correct_count = scores_arr.count(2)
            exec_count = total - scores_arr.count(0)
            avg_acc = (correct_count / total * 100) if total > 0 else 0
            avg_exec = (exec_count / total * 100) if total > 0 else 0
            avg_dfc = np.mean(dfc_list) if dfc_list else 0.0

            report_data[(task_name, engine)] = {
                "Total": total,
                "Correct_Count": correct_count,
                "Exec_Count": exec_count,
                "Accuracy(%)": avg_acc,
                "Executability(%)": avg_exec,
                "Avg_DFC(%)": avg_dfc,
            }
            logger.info("  -> Acc: %.2f%% | Exec: %.2f%% | DFC: %.2f%%", avg_acc, avg_exec, avg_dfc)

    if not report_data:
        logger.warning("No report data generated.")
        return

    logger.info(">>> Generating summary report: %s", FINAL_EXCEL_PATH)
    df = pd.DataFrame.from_dict(report_data, orient="index")
    df.index = pd.MultiIndex.from_tuples(df.index, names=["Task", "Engine"])
    cols_to_round = ["Accuracy(%)", "Executability(%)", "Avg_DFC(%)"]
    df[cols_to_round] = df[cols_to_round].round(2)
    os.makedirs(os.path.dirname(FINAL_EXCEL_PATH), exist_ok=True)
    df.to_excel(FINAL_EXCEL_PATH)
    logger.info("Pipeline completed.")


if __name__ == "__main__":
    main()
