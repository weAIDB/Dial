# dataset/config.py
# Configuration for SQLite -> MySQL/PostgreSQL/SQL Server/DuckDB migration.
# Works with duckdb_sqlite_databases.zip: extract and set paths below.

import os
from pathlib import Path

# =============================================================================
# SOURCE DATA CONFIGURATION (duckdb_sqlite_databases.zip)
# =============================================================================
# After extracting duckdb_sqlite_databases.zip, you typically get:
#   sqlite_databases/     -> SQLite DB files ({db_id}/{db_id}.sqlite or {db_id}.sqlite)
#   duckdb_databases/     -> DuckDB DB files (optional, we can create from SQLite)
#
# Set SQLITE_BASE_DIR to the directory containing SQLite databases.
# Example (relative to dataset): ../data/duckdb_sqlite_databases/sqlite_databases
_DATASET_DIR = Path(__file__).resolve().parent
SQLITE_BASE_DIR = os.environ.get("SQLITE_BASE_DIR", str(_DATASET_DIR.parent / "data" / "sqlite_databases"))

# =============================================================================
# DATA SOURCES (benchmark datasets)
# =============================================================================
# Each source has:
#   - json_files: List of JSON files with items (db_id, question, sql/sqlite)
#   - sqlite_db_dir: Override for SQLite DB path (empty = use SQLITE_BASE_DIR)
#   - field_mapping: Maps source field names to standard names (db_id, question, sqlite)
#
# Standard item fields after mapping: db_id, question, sqlite (SQL as string)
#
DATA_SOURCES = {
    "DS-NL2SQL": {
        "json_files": [str(_DATASET_DIR / "DS-NL2SQL.json")],
        "sqlite_db_dir": SQLITE_BASE_DIR,
        "field_mapping": {"db_id": "db_id", "question": "question", "gold_sql": "sqlite"},  # gold_sql.sqlite extracted in run_migration
    },

}

# =============================================================================
# MIGRATION TARGETS
# =============================================================================
# Which databases to create and migrate data to.
# A target is enabled only if its DB_CONFIG has a non-empty host (or dsn for Oracle).
# Supported: "mysql", "postgres", "sqlserver", "duckdb"
# (Oracle support requires additional implementation in db_manager)
MIGRATION_TARGETS = ["mysql", "postgres", "sqlserver", "duckdb"]

# =============================================================================
# OUTPUT CONFIGURATION
# =============================================================================
OUTPUT_DIR = os.environ.get("MIGRATION_OUTPUT_DIR", "output")
FINAL_OUTPUT_PATH = None  # None = save to OUTPUT_DIR/final_benchmark.json
CHECKPOINT_INTERVAL = 50  # Save intermediate results every N databases

# Source dialect for input SQL
SOURCE_DIALECT = "sqlite"

# Target dialects for SQL translation (if used elsewhere)
TARGET_DIALECTS = ["mysql", "postgres", "sqlserver", "duckdb"]

# =============================================================================
# DATABASE CONNECTION CONFIGURATION
# =============================================================================
# Credentials can be overridden by environment variables.
# Leave host empty to skip that engine during migration.
DB_CONFIG = {
    "mysql": {
        "host": os.environ.get("MYSQL_HOST", "localhost"),
        "user": os.environ.get("MYSQL_USER", "root"),
        "password": os.environ.get("MYSQL_PASSWORD", "123456"),
        "port": int(os.environ.get("MYSQL_PORT", "3306")),
    },
    "postgres": {
        "host": os.environ.get("PG_HOST", "localhost"),
        "user": os.environ.get("PG_USER", "postgres"),
        "password": os.environ.get("PG_PASSWORD", "123456"),
        "port": int(os.environ.get("PG_PORT", "5432")),
    },
    "sqlserver": {
        "host": os.environ.get("SQLSERVER_HOST", "localhost"),
        "user": os.environ.get("SQLSERVER_USER", "sa"),
        "password": os.environ.get("SQLSERVER_PASSWORD", ""),
        "port": int(os.environ.get("SQLSERVER_PORT", "1433")),
        "driver": os.environ.get("SQLSERVER_DRIVER", "{ODBC Driver 17 for SQL Server}"),
    },
    "oracle": {
        "host": os.environ.get("ORACLE_HOST", ""),
        "user": os.environ.get("ORACLE_USER", "SYSTEM"),
        "password": os.environ.get("ORACLE_PASSWORD", ""),
        "port": int(os.environ.get("ORACLE_PORT", "1521")),
        "dsn": os.environ.get("ORACLE_DSN", "localhost:1521/ORCLPDB"),
    },
}

# =============================================================================
# DATA PROCESSING CONFIGURATION
# =============================================================================
# Additional rows to migrate per table beyond essential data (smart migration)
MIGRATION_ROW_LIMIT = 50
MAX_SETUP_ATTEMPTS = 3
EXECUTION_TIMEOUT = 60

# =============================================================================
# CONCURRENCY CONFIGURATION
# =============================================================================
MAX_WORKERS = 4
DB_POOL_SIZE = 5
DB_MAX_OVERFLOW = 2
DB_POOL_TIMEOUT = 30
DB_POOL_RECYCLE = 3600

# =============================================================================
# DUCKDB CONFIGURATION
# =============================================================================
# Path for DuckDB files. Empty = use temp dir (cleaned up after run).
# Set to a path (e.g. ./duckdb_databases) to keep files and align with
# duckdb_sqlite_databases.zip structure.
DUCKDB_STORAGE_PATH = os.environ.get("DUCKDB_STORAGE_PATH", "")

# =============================================================================
# DATABASE REUSE CONFIGURATION
# =============================================================================
# If True, skip creation/migration for databases that already exist
REUSE_EXISTING_DB = True
# If True, remove databases that produce no valid data
CLEANUP_EMPTY_DB = True
