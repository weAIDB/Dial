# Knowledge Process: Dialect Knowledge Base Generator

Converts official documentation from **any** dialect/source into the dialect knowledge format used by Dial. Supports DuckDB, PostgreSQL, MySQL, SQL Server, Oracle, and any other dialect whose docs follow a similar structure.

## Overview

The pipeline has three stages:

1. **knowledge_create.py**: Extract and format docs from official sources (Git repos or local dirs) into `@dialect2sql@`-delimited blocks.
2. **tide_functional_knowledge.py**: Match template dialect (e.g. MySQL) templates with source dialect chunks via vector retrieval; LLM merges matched content → Functional dialect knowledge.
3. **tide_rule.py**: Three-phase conversion: Functional matching, Rule-based matching, Residual dialect scanning → Rule + Functional dialect knowledge.

## Quick Start

### 1. Extract Docs (knowledge_create.py)

From **Git** (e.g. DuckDB docs):

```bash
set KNOWLEDGE_TARGET_DIALECT=DuckDB
set KNOWLEDGE_SOURCE_TYPE=git
set KNOWLEDGE_WORK_DIR=C:\work
set KNOWLEDGE_GIT_REPO_URL=https://github.com/duckdb/duckdb-web
set KNOWLEDGE_LOCAL_REPO_NAME=duckdb-web
set KNOWLEDGE_OUTPUT_FILENAME=duckdb_extracted.txt
python knowledge_process/knowledge_create.py
```

From **local** docs directory (e.g. PostgreSQL):

```bash
set KNOWLEDGE_TARGET_DIALECT=PostgreSQL
set KNOWLEDGE_SOURCE_TYPE=local
set KNOWLEDGE_LOCAL_DOCS_PATH=C:\path\to\postgresql\doc\src\sgml
set KNOWLEDGE_OUTPUT_PATH=C:\output\postgresql_extracted.txt
python knowledge_process/knowledge_create.py
```

### 2. Convert to Functional Knowledge (tide_functional_knowledge.py)

```bash
set TIDE_TEMPLATE_DIALECT=MySQL
set TIDE_SOURCE_DIALECT=DuckDB
set TIDE_TEMPLATE_PATH=path/to/Functional_dialect/MySQL.txt
set TIDE_SOURCE_PATH=path/to/duckdb_extracted.txt
set TIDE_OUTPUT_PATH=path/to/Functional_dialect/duckdb.txt
set TIDE_EMBEDDING_MODEL=path/to/bge-large-en-v1.5
set OPENAI_API_BASE=...
set OPENAI_API_KEY=...
set OPENAI_MODEL=...
python knowledge_process/tide_functional_knowledge.py
```

### 3. Convert to Rule + Functional (tide_rule.py)

```bash
set TIDE_TEMPLATE_DIALECT=MySQL
set TIDE_SOURCE_DIALECT=DuckDB
set TIDE_TEMPLATE_FUNC_PATH=path/to/Functional_dialect/MySQL.txt
set TIDE_TEMPLATE_RULE_PATH=path/to/Rule_based_dialect/MySQL.txt
set TIDE_SOURCE_PATH=path/to/duckdb_extracted.txt
set TIDE_OUTPUT_FUNC_PATH=path/to/Functional_dialect/duckdb.txt
set TIDE_OUTPUT_RULE_PATH=path/to/Rule_based_dialect/duckdb.txt
set TIDE_EMBEDDING_MODEL=...
python knowledge_process/tide_rule.py
```

## File Structure

| File | Purpose |
|------|---------|
| `knowledge_create.py` | Extract official docs (Git or local) into `@dialect2sql@` blocks |
| `tide_functional_knowledge.py` | Match template + source → Functional dialect knowledge |
| `tide_rule.py` | Three-phase: Functional + Rule-based + Residual → Rule + Functional knowledge |
| `README.md` | This file |

## Configuration

### knowledge_create.py

| Config / Env | Description |
|--------------|-------------|
| `TARGET_DIALECT` | Output dialect label (e.g. DuckDB, PostgreSQL) |
| `SOURCE_TYPE` | `git` or `local` |
| `WORK_DIR`, `GIT_REPO_URL`, `LOCAL_REPO_NAME` | For `SOURCE_TYPE=git` |
| `LOCAL_DOCS_PATH` | For `SOURCE_TYPE=local` |
| `OUTPUT_FILENAME` / `OUTPUT_PATH` | Output file path |

### tide_functional_knowledge.py / tide_rule.py

| Config / Env | Description |
|--------------|-------------|
| `TEMPLATE_DIALECT` | Reference dialect (e.g. MySQL) |
| `SOURCE_DIALECT` | Target dialect from docs (e.g. DuckDB, PostgreSQL) |
| `TEMPLATE_*_PATH`, `SOURCE_PATH`, `OUTPUT_*_PATH` | Paths |
| `EMBEDDING_MODEL`, `OPENAI_*` | LLM and embedding model |

## Output Format

All outputs use `@dialect2sql@` delimiters between blocks. Place generated files in:

- `Dial/src/knowledge/knowledge/Functional_dialect/{dialect}.txt`
- `Dial/src/knowledge/knowledge/Rule_based_dialect/{dialect}.txt`

for use by the RAG retriever in the Dial pipeline.
