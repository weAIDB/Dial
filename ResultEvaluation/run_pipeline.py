import os
import pandas as pd
from collections import OrderedDict

from config import (
    DB_CONFIG,
    PIPELINE_TASKS,
    FINAL_EXCEL_PATH,
    GOLD_RESULT_FILE,
    EXECUTE_ENGINES
)
from step1_executor import run_execution
from step2_evaluator import get_evaluation_scores
from common_utils import logger


def main():
    logger.info("=== 开始执行自动化评估流程 ===")

    # 最终结果：
    # {
    #   (task_name, engine): { qid: score }
    # }
    all_scores_data = OrderedDict()

    for task in PIPELINE_TASKS:
        task_name = task['name']
        input_sql = task['input_sql']
        output_base = task['output_exec']  # 基础路径，如 ../result.json

        logger.info(f"\n>>> 处理任务: {task_name}")

        # 遍历引擎，分开执行与评估
        for engine in EXECUTE_ENGINES:
            # 1. 构造带后缀的文件名，例如 result_mysql.json
            name_part, ext_part = os.path.splitext(output_base)
            engine_output_file = f"{name_part}_{engine}{ext_part}"

            # 2. 修改 Step 1 调用：只执行当前 engine (需要配合 step1_executor 的修改)
            success = run_execution(input_sql, engine_output_file, DB_CONFIG, target_engine=engine)

            if not success:
                logger.warning(f"引擎 {engine} 执行失败，跳过")
                continue

            # 3. 修改 Step 2 调用：读取刚刚生成的特定引擎文件
            if not os.path.exists(GOLD_RESULT_FILE):
                logger.error(f"标准答案不存在: {GOLD_RESULT_FILE}")
                continue

            engine_scores = get_evaluation_scores(
                pred_file=engine_output_file,
                gold_file=GOLD_RESULT_FILE
            )

            # 合并结果
            for eng, scores in engine_scores.items():
                all_scores_data[(task_name, eng)] = scores

    if not all_scores_data:
        logger.warning("没有任何评估结果，流程结束")
        return

    # ===== Step 3: 生成 Excel =====
    logger.info(f"\n>>> 正在生成最终 Excel: {FINAL_EXCEL_PATH}")

    # 行索引：(task, engine)
    df = pd.DataFrame.from_dict(all_scores_data, orient='index')

    df.index = pd.MultiIndex.from_tuples(
        df.index, names=['task', 'engine']
    )

    # ===== 统计列 =====
    correct_count = (df == 2).sum(axis=1)
    executable_count = (df >= 1).sum(axis=1)

    df['Correct_Count(2)'] = correct_count
    df['Executable_Count(1+2)'] = executable_count

    # ===== 列排序：QID 在前，统计在后 =====
    stat_cols = ['Correct_Count(2)', 'Executable_Count(1+2)']
    qid_cols = [c for c in df.columns if c not in stat_cols]

    def qid_sort_key(x):
        try:
            return int(x)
        except Exception:
            return str(x)

    qid_cols.sort(key=qid_sort_key)

    df = df[qid_cols + stat_cols]

    # 确保目录存在
    os.makedirs(os.path.dirname(FINAL_EXCEL_PATH), exist_ok=True)

    df.to_excel(FINAL_EXCEL_PATH)
    logger.info(f"Excel 报表已保存至: {FINAL_EXCEL_PATH}")

    logger.info("\n=== 流程结束 ===")


if __name__ == "__main__":
    main()
