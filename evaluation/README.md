# Evaluation Pipeline

Runs the evaluation workflow: execute generated SQL on target engines, compare to gold results, and compute Dialect Feature Coverage (DFC). Produces per-task per-engine metrics and a summary Excel report.

## Overview

- **Step 1** (`step1_executor.py`): Executes SQL on MySQL, PostgreSQL, SQLite, DuckDB, SQL Server, Oracle; writes execution results to JSON.
- **Step 2** (`step2_evaluator.py`): Compares predicted vs gold results; score 0 = not executable, 1 = executable but wrong, 2 = correct.
- **Step 3** (`step3_dfc.py`): Computes DFC per item (regex-based dialect feature coverage when score = 1).
- **Output**: Per-task per-engine JSON plus a summary Excel file.

## Quick Start

1. Set `evaluation/config.py`: `DB_CONFIG`, `EXECUTE_ENGINES`, `PIPELINE_TASKS` (input_sql / output_exec paths), `GOLD_RESULT_FILE`, `FINAL_EXCEL_PATH`.
2. Ensure gold result JSON and input SQL JSON files exist for the configured tasks.
3. From project root:
   ```bash
   python run_evaluation.py
   ```
   Or from this folder: `python run_pipeline.py` or `python -m evaluation.run_pipeline`.

## File Structure

| File | Purpose |
|------|---------|
| `config.py` | DB config, pipeline tasks, gold file path, Excel path |
| `common_utils.py` | Logger, JSON load/save, custom encoder for DB types |
| `step1_executor.py` | Per-engine executors and `run_execution()` |
| `step2_evaluator.py` | `get_evaluation_scores()`, table comparison helpers |
| `step3_dfc.py` | `calculate_dfc_entry()`, feature extraction from rules |
| `rules.py` | Dialect classification rules (used by step3 and DFC.py) |
| `run_pipeline.py` | Main pipeline: Step1 → Step2 → Step3 → Excel |

## Configuration

- **EXECUTE_ENGINES**: Subset of `mysql`, `postgres`, `sqlite`, `sqlserver`, `duckdb`, `oracle`.
- **PIPELINE_TASKS**: List of `{name, input_sql, output_exec}`; paths relative to evaluation dir or absolute.
- **GOLD_RESULT_FILE**: JSON with gold results (question_id, result, gold_sql per engine).
- **FINAL_EXCEL_PATH**: Output Excel path for the summary table.

## Output

- One result JSON per task per engine (e.g. `result/result_010_postgres.json`) with `eval_score`, `dfc_score`, `dfc_details` per item.
- Summary Excel at `FINAL_EXCEL_PATH` with columns: Total, Correct_Count, Exec_Count, Accuracy(%), Executability(%), Avg_DFC(%).
