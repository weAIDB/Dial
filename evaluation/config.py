# evaluation/config.py
# Database connection settings and pipeline task definitions for evaluation.
# Adjust paths, credentials, and task list per your environment.

import os
from pathlib import Path

# -----------------------------------------------------------------------------
# Database connection configuration
# -----------------------------------------------------------------------------
DB_CONFIG = {
    "mysql": {
        "host": "localhost",
        "user": "root",
        "password": "123456",
        "port": 3306,
    },
    "postgres": {
        "host": "localhost",
        "user": "postgres",
        "password": "123456",
        "port": 5432,
    },
    "sqlserver": {
        "driver": "{ODBC Driver 17 for SQL Server}",
        "host": "localhost",
        "user": "sa",
        "password": "Dialectsql123",
        "port": 1433,
    },
    "oracle": {
        "user": "SYSTEM",
        "password": "Dialectsql123",
        "dsn": "localhost:1521/ORCLPDB",
    },
    "sqlite_dir": "../../data/data-last/sqlite_databases/",
    "duckdb_dir": "../../data/data-last/duckdb_databases/",
}

# Target engines for execution (subset of mysql, postgres, sqlite, sqlserver, duckdb, oracle)
EXECUTE_ENGINES = ["postgres", "sqlserver", "oracle"]

# -----------------------------------------------------------------------------
# Pipeline tasks: list of {name, input_sql, output_exec}
# Each task runs Step1 (execute) -> Step2 (evaluate) -> Step3 (DFC)
# -----------------------------------------------------------------------------
PIPELINE_TASKS = [
    {"name": "010", "input_sql": "result/sqls_010.json", "output_exec": "result/result_010.json"},
    {"name": "011", "input_sql": "result/sqls_011.json", "output_exec": "result/result_011.json"},
    {"name": "100", "input_sql": "result/sqls_100.json", "output_exec": "result/result_100.json"},
    {"name": "110", "input_sql": "result/sqls_110.json", "output_exec": "result/result_110.json"},
]

# Path to gold reference file (expected format: list of items with question_id, result, gold_sql per engine)
GOLD_RESULT_FILE = "../../data/data-last/result.json"

# Output Excel path for the final summary report
FINAL_EXCEL_PATH = "test/result.xlsx"

# -----------------------------------------------------------------------------
# Ensure output directories exist
# -----------------------------------------------------------------------------
for task in PIPELINE_TASKS:
    dir_path = os.path.dirname(task["output_exec"])
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
if os.path.dirname(FINAL_EXCEL_PATH):
    os.makedirs(os.path.dirname(FINAL_EXCEL_PATH), exist_ok=True)
