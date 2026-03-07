# Dial: Multi-Dialect NL-to-SQL Pipeline and Evaluation

This repository contains the implementation for a multi-dialect natural language to SQL (NL2SQL) pipeline and evaluation framework. It supports generating dialect-agnostic logical query plans (LQP), tagging dialect-sensitive operators, RAG-based retrieval of dialect knowledge, and translation to SQL for multiple engines (MySQL, PostgreSQL, SQL Server, DuckDB, Oracle). The evaluation module runs generated SQL on target databases, scores accuracy and executability, and computes Dialect Feature Coverage (DFC).

The following sections detail the structure of the codebase, setup instructions, and how to run the pipeline, dataset migration, and evaluation.

## Overview

The project is organized into three main workflows:

1. **Dial pipeline** (`Dial/`): End-to-end NL → LQP → dialect-aware tagging → RAG retrieval → SQL translation with execution and semantic verification. It produces per-dialect SQL from natural language questions and schema.
2. **Dataset migration** (`dataset/`): Migrates SQLite databases (e.g. from `duckdb_sqlite_databases.zip`) to MySQL, PostgreSQL, SQL Server, and DuckDB so that the same schema and data are available on multiple engines for evaluation.
3. **Evaluation** (`evaluation/`): Executes generated SQL on target engines, compares results to gold answers, and computes accuracy, executability, and DFC; outputs per-task per-engine metrics and an Excel summary.

The main entry points are unified at the repository root: `run_dial_pipeline.py`, `run_migration.py`, and `run_evaluation.py`.

## Directory Structure

```
.
├── conf/                    # (optional; Dial uses Dial/conf)
├── dataset/
│   ├── config.py            # Data sources, DB credentials, migration targets
│   ├── db_manager.py        # SQLite → MySQL/Postgres/SQL Server/DuckDB migration
│   ├── run_migration.py     # Migration entry (also runnable via root run_migration.py)
│   ├── DS-NL2SQL.json       # Example benchmark JSON
│   └── README.md            # Dataset migration usage
├── evaluation/
│   ├── config.py            # DB config, pipeline tasks, gold result path
│   ├── common_utils.py      # Logging, JSON I/O, custom encoder
│   ├── step1_executor.py    # Per-engine SQL execution (MySQL, PG, SQLite, DuckDB, SQL Server, Oracle)
│   ├── step2_evaluator.py   # Accuracy scoring (0/1/2)
│   ├── step3_dfc.py         # DFC (Dialect Feature Coverage) per item
│   ├── rules.py             # Dialect classification rules for DFC
│   ├── run_pipeline.py      # Execute → Evaluate → DFC → Excel (also via root run_evaluation.py)
│   └── README.md            # Evaluation usage
├── Dial/
│   ├── conf/
│   │   └── settings.py      # Paths, DB config, LLM API, pipeline stages
│   ├── src/
│   │   ├── nl_lqp/          # NL-LQP generation and dialect-aware tagging
│   │   ├── knowledge/       # RAG retriever and runner (HINT-KB)
│   │   ├── schema/          # DDL fetcher
│   │   └── translation/     # rag2sql, execution check, semantic validation
│   ├── run_dial_pipeline.py # Step 1–4 launcher (also via root run_dial_pipeline.py)
│   └── README.md            # Dial pipeline usage
├── run_dial_pipeline.py     # Root launcher for Dial pipeline
├── run_migration.py         # Root launcher for dataset migration
├── run_evaluation.py        # Root launcher for evaluation pipeline
└── README.md                # This file
```

## Setup

### Dependencies

- This project requires Python 3.10+. You can set up the environment using `pip` to install the dependencies:
```bash
pip install -r requirements.txt
```

- For **Dial pipeline**: async HTTP, LLM API client, SQLAlchemy, DB drivers (pymysql, psycopg2, pyodbc, oracledb, duckdb, etc.), sqlglot (optional)
- For **dataset migration**: pandas, sqlalchemy, pymysql, psycopg2, pyodbc, duckdb, sqlite3
- For **evaluation**: pandas, numpy, openpyxl (Excel), tqdm, same DB drivers as above

Install DB and driver packages as needed for your target engines (MySQL, PostgreSQL, SQL Server, Oracle, DuckDB, SQLite).

### Data Preparation

1. **Dial pipeline**: Place input JSON (e.g. `filtered_Dialects.json`) and schema/DB paths as specified in `Dial/conf/settings.py`. Set `BASE_DATA_DIR`, `SQLITE_DB_DIR`, `DUCKDB_DIR`, and pipeline input/output paths (or use environment variables).
2. **Dataset migration**: Extract `duckdb_sqlite_databases.zip` and set `SQLITE_BASE_DIR` (or per-source `sqlite_db_dir`) in `dataset/config.py`. Configure `DB_CONFIG` for MySQL, Postgres, SQL Server.
3. **Evaluation**: Set `GOLD_RESULT_FILE`, `PIPELINE_TASKS` (input_sql / output_exec paths), and `EXECUTE_ENGINES` in `evaluation/config.py`. Ensure gold result JSON and generated SQL files exist.

## Configuration

- **Dial pipeline**: All paths and API/DB settings are in `Dial/conf/settings.py`. Use `DIAL_*` environment variables to override.
- **Dataset migration**: `dataset/config.py` defines `DATA_SOURCES`, `MIGRATION_TARGETS`, `DB_CONFIG`, `DUCKDB_STORAGE_PATH`, `REUSE_EXISTING_DB`, etc.
- **Evaluation**: `evaluation/config.py` defines `DB_CONFIG`, `EXECUTE_ENGINES`, `PIPELINE_TASKS`, `GOLD_RESULT_FILE`, `FINAL_EXCEL_PATH`.

## Usage

All three workflows can be started from the repository root.

### Run Dial pipeline (NL → LQP → RAG → SQL)

From the project root:

```bash
python run_dial_pipeline.py --steps 1,2,3,4
```

Or run specific steps:

```bash
python run_dial_pipeline.py --step1 --step2
python run_dial_pipeline.py --step3 --step4
```

Steps: 1 = Generate NL-LQP, 2 = Tag dialect-aware LQP, 3 = RAG retrieval, 4 = Translation and feedback iteration. Configure paths and API in `Dial/conf/settings.py`.

### Run dataset migration (SQLite → multi-engine)

From the project root:

```bash
python run_migration.py
```

Configure `SQLITE_BASE_DIR` and `DB_CONFIG` in `dataset/config.py` (or via environment variables). See `dataset/README.md` for details.

### Run evaluation (Execute → Evaluate → DFC)

From the project root:

```bash
python run_evaluation.py
```

This runs Step1 (execute SQL per engine), Step2 (accuracy evaluation), Step3 (DFC), and writes the summary Excel. Configure tasks and gold file in `evaluation/config.py`. See `evaluation/README.md` for details.

### Alternative entry points

- Dial pipeline from `Dial` folder: `cd Dial` then `python run_dial_pipeline.py`
- Migration from dataset package: `python -m dataset.run_migration`
- Evaluation from evaluation package: `python -m evaluation.run_pipeline`

## Key Code Components

- **`run_dial_pipeline.py` (root)**: Adds `Dial/` to `sys.path`, changes working directory to `Dial/`, and invokes `Dial/run_dial_pipeline.main()` so that steps 1–4 run with correct paths and imports.
- **`run_migration.py` (root)**: Adds project root to `sys.path` and calls `dataset.run_migration.main()` to discover DBs, find SQLite paths, and run `DBManager.setup_and_migrate()` for each.
- **`run_evaluation.py` (root)**: Adds project root to `sys.path` and calls `evaluation.run_pipeline.main()` to run the Execute → Evaluate → DFC pipeline and generate the Excel report.
- **`Dial/run_dial_pipeline.py`**: Parses `--steps` / `--step1` … `--step4`, and runs the corresponding modules (`generate_nl_lqp`, `tag_dialect_aware_lqp`, `runner`, `translation.main`).
- **`dataset/db_manager.py`**: Creates MySQL/Postgres/SQL Server databases and DuckDB files from SQLite; supports smart migration (essential rows) and reuse of existing DBs.
- **`evaluation/run_pipeline.py`**: Loads gold results and task configs; for each task and engine runs `step1_executor.run_execution`, `step2_evaluator.get_evaluation_scores`, and `step3_dfc.calculate_dfc_entry`; aggregates and writes Excel.

For more detail, see the README in each subfolder: `dataset/README.md`, `evaluation/README.md`, and `Dial/README.md`.
