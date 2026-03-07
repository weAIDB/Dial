# Dial Pipeline (NL → LQP → RAG → SQL)

Core pipeline: generate dialect-agnostic NL-LQP, tag dialect-aware LQP, run RAG retrieval for dialect knowledge, and translate to SQL with execution and semantic verification.

## Overview

1. **Step 1** (`src/nl_lqp/generate_nl_lqp.py`): Generate NL-LQP from natural language and schema.
2. **Step 2** (`src/nl_lqp/tag_dialect_aware_lqp.py`): Tag dialect-sensitive operators and map to functional categories.
3. **Step 3** (`src/knowledge/runner.py`): RAG retrieval on tagged NL-LQP; output per-dialect files for translation.
4. **Step 4** (`src/translation/main.py`): Translation (rag2sql), execution check, and semantic validation with feedback iteration.

## Directory Structure

```
Dial/
├── conf/
│   └── settings.py      # Paths, DB config, LLM API, pipeline stages
├── src/
│   ├── nl_lqp/          # NL-LQP generation and dialect-aware tagging
│   ├── knowledge/       # RAG retriever, runner, dialect knowledge (Rule/Functional)
│   ├── schema/          # DDL fetcher
│   └── translation/     # rag2sql, execution, semantic check, result saving
├── run_dial_pipeline.py # Launcher for steps 1–4
└── README.md            # This file
```

## Configuration

All settings in `conf/settings.py` (or `DIAL_*` environment variables):

- **Paths**: `BASE_DATA_DIR`, `PIPELINE_INPUT_JSON`, `NL_LQP_OUTPUT_JSON`, `DIALECT_AWARE_LQP_OUTPUT_JSON`, RAG and translation output paths.
- **DB**: `DB_CONFIG` for MySQL, Postgres, SQL Server, Oracle, SQLite, DuckDB.
- **LLM / API**: Translation and optional services.

## Usage

From project root (recommended):

```bash
python run_dial_pipeline.py --steps 1,2,3,4
```

From this folder:

```bash
cd Dial
python run_dial_pipeline.py --step1 --step2 --step3 --step4
```

Options: `--steps 1,2,3,4` (default) or `--step1`, `--step2`, `--step3`, `--step4` for individual steps.

## Key Components

- **`run_dial_pipeline.py`**: Parses arguments and runs the selected steps (async for step1/step2).
- **`src/nl_lqp/`**: Async generation and tagging of LQP.
- **`src/knowledge/runner.py`**: Loads tagged LQP, runs RAG retrieval, writes per-dialect output.
- **`src/translation/main.py`**: Loads RAG output, calls LLM for SQL, runs execution and semantic checks, saves results.
