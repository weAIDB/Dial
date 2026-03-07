# Dataset Migration Tool

Migrates SQLite databases to MySQL, PostgreSQL, SQL Server, and DuckDB. Designed to work with `duckdb_sqlite_databases.zip` and extend multi-dialect evaluation to five database engines.

## Overview

- **Source**: SQLite database files (e.g. from `duckdb_sqlite_databases.zip`)
- **Targets**: MySQL, PostgreSQL, SQL Server, DuckDB (Oracle requires additional implementation)
- **Features**: Smart migration (only essential rows for queries), optional reuse of existing databases, configurable per-engine enable/disable

## Quick Start

### 1. Extract `duckdb_sqlite_databases.zip`

After extraction you typically have:

```
duckdb_sqlite_databases/
├── sqlite_databases/
│   ├── {db_id_1}/
│   │   └── {db_id_1}.sqlite
│   ├── {db_id_2}/
│   │   └── {db_id_2}.sqlite
│   └── ...
└── duckdb_databases/   (optional; we can create from SQLite)
    └── ...
```

### 2. Configure Paths and Credentials

Edit `dataset/config.py`:

- **SQLITE_BASE_DIR**: Path to the `sqlite_databases/` directory (or use env `SQLITE_BASE_DIR`)
- **DUCKDB_STORAGE_PATH**: Where to store DuckDB files (empty = temp dir, cleaned after run)
- **DB_CONFIG**: Connection settings for MySQL, Postgres, SQL Server

Example:

```python
SQLITE_BASE_DIR = r"C:\path\to\duckdb_sqlite_databases\sqlite_databases"
DUCKDB_STORAGE_PATH = r"C:\path\to\duckdb_sqlite_databases\duckdb_databases"

DB_CONFIG = {
    "mysql": {"host": "localhost", "user": "root", "password": "123456", "port": 3306},
    "postgres": {"host": "localhost", "user": "postgres", "password": "123456", "port": 5432},
    "sqlserver": {"host": "localhost", "user": "sa", "password": "xxx", "port": 1433, "driver": "{ODBC Driver 17 for SQL Server}"},
}
```

Or use environment variables:

```bash
set SQLITE_BASE_DIR=C:\path\to\duckdb_sqlite_databases\sqlite_databases
set MYSQL_HOST=localhost
set PG_HOST=localhost
set SQLSERVER_HOST=localhost
```

### 3. Run Migration

From project root (recommended):

```bash
python run_migration.py
```

Or as module: `python -m dataset.run_migration`  
Or from this directory: `cd dataset` then `python run_migration.py`

## File Structure

| File | Purpose |
|------|---------|
| `config.py` | Data sources, DB credentials, migration targets, DuckDB path |
| `db_manager.py` | Migration logic: create databases, migrate tables from SQLite |
| `run_migration.py` | Entry point: discover DBs, call `DBManager.setup_and_migrate` |

## Data Sources

In `config.py`, `DATA_SOURCES` defines benchmark datasets:

- **json_files**: JSON files with items (`db_id`, `question`, SQL field)
- **sqlite_db_dir**: Override for SQLite DB directory (empty = use `SQLITE_BASE_DIR`)
- **field_mapping**: Maps source fields to standard names (`db_id`, `question`, `sqlite`)

For JSON with `gold_sql: {sqlite: "..."}`, use `"gold_sql": "sqlite"` in `field_mapping` to extract the SQL.

If no `json_files` are set, `run_migration` discovers `db_id`s from the SQLite directory structure.

## Migration Targets

Engines are enabled only if:

1. Listed in `MIGRATION_TARGETS` (default: `mysql`, `postgres`, `sqlserver`, `duckdb`)
2. `DB_CONFIG` has a non-empty `host` (or `dsn` for Oracle)

To skip an engine, remove it from `MIGRATION_TARGETS` or leave its `host` empty.

## Smart Migration

When `json_files` provide items with SQL, `DBManager`:

1. Runs each SQL on SQLite to find involved rows
2. Migrates only those rows plus extra up to `MIGRATION_ROW_LIMIT` per table
3. Reduces migration time and storage for large databases

## Configuration Reference

| Config | Description |
|--------|-------------|
| `SQLITE_BASE_DIR` | Base path for SQLite files |
| `MIGRATION_TARGETS` | List of engines to migrate to |
| `MIGRATION_ROW_LIMIT` | Max extra rows per table (default: 50) |
| `REUSE_EXISTING_DB` | Skip creation if DB exists (default: True) |
| `DUCKDB_STORAGE_PATH` | DuckDB output dir (empty = temp) |
| `CHECKPOINT_INTERVAL` | Save intermediate results every N DBs (default: 50) |

## Output

- `output/final_benchmark.json`: `{"migrated": [...], "failed": [...], "total": N}`
- Checkpoint files: `output/checkpoint_migrated_*.json` when `CHECKPOINT_INTERVAL` is set

## Extending to Oracle

`db_manager.py` currently supports MySQL, Postgres, SQL Server, DuckDB. Adding Oracle requires:

1. Oracle driver (e.g. `oracledb`)
2. Admin engine for `CREATE TABLESPACE/USER` or schema creation
3. Migration logic in `setup_and_migrate` and `teardown_database`
4. Include `oracle` in `MIGRATION_TARGETS` and configure `DB_CONFIG["oracle"]`
