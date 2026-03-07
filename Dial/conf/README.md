# Dial Configuration

Single place for pipeline and DB settings used by the Dial NL→SQL pipeline.

## settings.py

- **Base paths**: `BASE_DATA_DIR`, `SQLITE_DB_DIR`, `DUCKDB_DIR`
- **Pipeline I/O**: `PIPELINE_INPUT_JSON`, `NL_LQP_OUTPUT_JSON`, `DIALECT_AWARE_LQP_OUTPUT_JSON`, temp and cache dirs
- **RAG**: `RAG_KNOWLEDGE_ROOT`, `RAG_VECTOR_STORE_ROOT`, embedding model path
- **Translation**: Rules dirs, result paths, output dir
- **DB**: `DB_CONFIG` for MySQL, Postgres, SQL Server, Oracle, SQLite, DuckDB

Override any value with `DIAL_*` environment variables (e.g. `DIAL_BASE_DATA_DIR`, `DIAL_MYSQL_HOST`).
