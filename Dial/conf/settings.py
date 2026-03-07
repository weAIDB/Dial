# conf/settings.py
# Unified configuration for Dial: paths, DB connections, LLM API, pipeline stages.
# Adjust paths and credentials here or via environment variables.

import os
from pathlib import Path

# =============================================================================
# Base paths (data and outputs)
# =============================================================================
BASE_DATA_DIR = os.environ.get("DIAL_BASE_DATA_DIR", "")
SQLITE_DB_DIR = os.environ.get("DIAL_SQLITE_DB_DIR", os.path.join(BASE_DATA_DIR, "sqlite_databases"))
DUCKDB_DIR = os.environ.get("DIAL_DUCKDB_DIR", os.path.join(BASE_DATA_DIR, "duckdb_databases"))

# =============================================================================
# Pipeline file paths (order: schema linking -> generate NL-LQP -> tag -> RAG -> translation)
# =============================================================================
PIPELINE_INPUT_JSON = os.environ.get("DIAL_PIPELINE_INPUT_JSON", os.path.join(BASE_DATA_DIR, "filtered_Dialects.json"))
SCHEMA_LINKING_OUTPUT_JSON = os.environ.get("DIAL_SCHEMA_LINKING_OUTPUT_JSON", os.path.join(BASE_DATA_DIR, "pipeline_input_with_schema.json"))
NL_LQP_OUTPUT_JSON = os.environ.get("DIAL_NL_LQP_OUTPUT_JSON", os.path.join(BASE_DATA_DIR, "nl_lqp.json"))
DIALECT_AWARE_LQP_OUTPUT_JSON = os.environ.get("DIAL_DIALECT_AWARE_LQP_OUTPUT_JSON", os.path.join(BASE_DATA_DIR, "dialect_aware_lqp.json"))
PROMPT_CACHE_DIR = os.environ.get("DIAL_PROMPT_CACHE_DIR", os.path.join(BASE_DATA_DIR, "prompt_cache"))
TEMP_NL_LQP_DIR = os.environ.get("DIAL_TEMP_NL_LQP_DIR", os.path.join(BASE_DATA_DIR, "temp_nl_lqp"))
TEMP_DIALECT_AWARE_DIR = os.environ.get("DIAL_TEMP_DIALECT_AWARE_DIR", os.path.join(BASE_DATA_DIR, "temp_dialect_aware"))

# =============================================================================
# RAG / retrieval (nl2rag)
# =============================================================================
_DIAL_ROOT = Path(__file__).resolve().parent.parent
RAG_KNOWLEDGE_ROOT = Path(os.environ.get("DIAL_RAG_KNOWLEDGE_ROOT", str(_DIAL_ROOT / "src" / "knowledge" / "knowledge" / "Rule_based_dialect")))
RAG_VECTOR_STORE_ROOT = Path(os.environ.get("DIAL_RAG_VECTOR_STORE_ROOT", str(_DIAL_ROOT / "data" / "chroma_vector_stores")))
RAG_INPUT_BASE_DIR = Path(os.environ.get("DIAL_RAG_INPUT_BASE_DIR", str(BASE_DATA_DIR)))
RAG_OUTPUT_BASE_DIR = Path(os.environ.get("DIAL_RAG_OUTPUT_BASE_DIR", str(BASE_DATA_DIR)))
RAG_EMBEDDING_MODEL_PATH = os.environ.get("DIAL_RAG_EMBEDDING_MODEL_PATH", "BAAI/bge-large-en-v1.5")

# =============================================================================
# Translation (rag2sql) paths
# =============================================================================
RULES_ROOT_DIR = os.environ.get("DIAL_RULES_ROOT_DIR", str(_DIAL_ROOT / "src" / "knowledge" / "knowledge" / "Rule_based_dialect"))
FUNCTIONAL_ROOT_DIR = os.environ.get("DIAL_FUNCTIONAL_ROOT_DIR", str(_DIAL_ROOT / "src" / "knowledge" / "knowledge" / "Functional_dialect"))
RESULT_JSON_PATH = os.environ.get("DIAL_RESULT_JSON_PATH", os.path.join(BASE_DATA_DIR, "rag_input_with_retrieval.json"))
OUTPUT_DIR = os.environ.get("DIAL_OUTPUT_DIR", os.path.join(BASE_DATA_DIR, "rag2sql_output"))
JSON_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "rag2SQL_result.json")
FINAL_REPORT_PATH = os.path.join(OUTPUT_DIR, "final_sql_execution_report.json")
SEMANTIC_FAIL_LOG_PATH = os.path.join(OUTPUT_DIR, "semantic_validation_failures.json")

# =============================================================================
# Database connections (for schema extraction and translation execution)
# =============================================================================
DB_CONFIG = {
    "mysql": {
        "host": os.environ.get("DIAL_MYSQL_HOST", "localhost"),
        "user": os.environ.get("DIAL_MYSQL_USER", "root"),
        "password": os.environ.get("DIAL_MYSQL_PASSWORD", ""),
        "port": int(os.environ.get("DIAL_MYSQL_PORT", "3306")),
        "charset": "utf8mb4",
        "buffered": True,
        "autocommit": True,
        "connection_timeout": 30,
    },
    "postgres": {
        "host": os.environ.get("DIAL_PG_HOST", "localhost"),
        "user": os.environ.get("DIAL_PG_USER", "postgres"),
        "password": os.environ.get("DIAL_PG_PASSWORD", ""),
        "port": int(os.environ.get("DIAL_PG_PORT", "5432")),
    },
    "sqlserver": {
        "driver": os.environ.get("DIAL_SQLSERVER_DRIVER", "{ODBC Driver 17 for SQL Server}"),
        "host": os.environ.get("DIAL_SQLSERVER_HOST", "localhost"),
        "user": os.environ.get("DIAL_SQLSERVER_USER", "sa"),
        "password": os.environ.get("DIAL_SQLSERVER_PASSWORD", ""),
        "port": int(os.environ.get("DIAL_SQLSERVER_PORT", "1433")),
    },
    "oracle": {
        "user": os.environ.get("DIAL_ORACLE_USER", "system"),
        "password": os.environ.get("DIAL_ORACLE_PASSWORD", ""),
        "dsn": os.environ.get("DIAL_ORACLE_DSN", "localhost:1521/ORCLPDB"),
    },
    "sqlite_dir": os.environ.get("DIAL_SQLITE_DIR", SQLITE_DB_DIR),
    "duckdb_dir": os.environ.get("DIAL_DUCKDB_DIR", DUCKDB_DIR),
}

# Schema extractor (generate NL-LQP) uses this structure
GLOBAL_DB_CONFIG = {
    "PATHS": {
        "sqlite_db_dir": SQLITE_DB_DIR,
        "duckdb_dir": DUCKDB_DIR,
    },
    "DB_CONN": {
        "mysql": DB_CONFIG["mysql"],
        "postgres": DB_CONFIG["postgres"],
        "sqlserver": DB_CONFIG["sqlserver"],
        "oracle": DB_CONFIG["oracle"],
    },
}

# Rule file names per DB type (translation stage)
DB_TYPE_TO_RULE_FILE = {
    "MySQL": "MySQL.txt",
    "PostgreSQL": "PostgreSQL.txt",
    "SQLite": "SQLite.txt",
    "Oracle": "Oracle.txt",
    "SQL Server": "SQL Server.txt",
    "duckdb": "duckdb.txt",
}
SUPPORTED_DBS = list(DB_TYPE_TO_RULE_FILE.keys())

# =============================================================================
# LLM / API (OpenAI-compatible for generate NL-LQP, tag LQP, and translation)
# =============================================================================
OPENAI_API_KEY = os.environ.get("QIDIAN_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
OPENAI_BASE_URL = os.environ.get("QIDIAN_URL", os.environ.get("OPENAI_BASE_URL", ""))
OPENAI_MODEL_NAME = os.environ.get("DIAL_LLM_MODEL", "gpt-4o")

# Translation stage may use different env names
API_KEY = os.environ.get("DIAL_API_KEY", OPENAI_API_KEY)
API_BASE_URL = os.environ.get("DIAL_API_BASE_URL", OPENAI_BASE_URL)
MODEL_NAME = os.environ.get("DIAL_MODEL_NAME", OPENAI_MODEL_NAME)

# =============================================================================
# Schema linking (Step 0): dialect used to fetch full schema when true_tables_columns is missing
# =============================================================================
SCHEMA_LINKING_DIALECT = os.environ.get("DIAL_SCHEMA_LINKING_DIALECT", "sqlite").strip().lower()

# =============================================================================
# Execution and concurrency
# =============================================================================
TARGET_DIALECTS = os.environ.get("DIAL_TARGET_DIALECTS", "postgres,sqlserver,oracle").strip().split(",")
MAX_CONCURRENT_REQUESTS = int(os.environ.get("DIAL_MAX_CONCURRENT_REQUESTS", "10"))
SQL_EXECUTION_TIMEOUT = int(os.environ.get("DIAL_SQL_EXECUTION_TIMEOUT", "30"))
MAX_RETRY_COUNT = int(os.environ.get("DIAL_MAX_RETRY_COUNT", "1"))
MAGIC_SIMILARITY_THRESHOLD = float(os.environ.get("DIAL_MAGIC_SIMILARITY_THRESHOLD", "0.75"))

# =============================================================================
# Tagging (dialect-aware LQP): cascaded operator labeling and functional categories
# =============================================================================
CATEGORY_PRIORITY = {
    "Scalar Calculation & Transformation": 1,
    "Auxiliary & Fallback Operations": 2,
    "Result Organization & Selection": 3,
    "Aggregation & Grouping": 4,
    "Constraint & Filtering": 5,
    "Data Sourcing & Association": 6,
}

LEXICAL_TRIGGERS = [
    "extract", "regex", "cast", "convert", "format", "substring", "substr",
    "concat", "slice", "replace", "truncate", "trunc", "round", "percentile",
    "to_char", "to_date", "to_number", "to_timestamp", "to_json", "try_cast",
    "date", "time", "timestamp", "now", "curdate", "current_date", "curtime",
    "current_timestamp", "sysdate", "systimestamp", "getdate", "sysdatetime", "today",
    "year", "month", "day", "hour", "minute", "second", "quarter", "week",
    "dayofweek", "dayofyear", "dayname", "monthname",
    "datediff", "date_diff", "timestampdiff", "months_between", "age",
    "date_add", "date_sub", "add_months", "date_trunc", "time_bucket", "datefromparts",
    "substring_index", "split_part", "string_split", "string_split_regex",
    "regexp_extract", "regexp_substr", "regexp_replace", "regexp_matches",
    "instr", "contains", "starts_with", "ends_with", "length", "strlen", "position", "rpad",
    "limit", "top", "offset", "fetch", "rownum",
    "over", "partition", "row_number", "rank", "dense_rank",
    "lag", "lead", "ntile", "first_value", "last_value", "nth_value",
    "iif", "if", "case", "when", "decode",
    "coalesce", "ifnull", "isnull", "nullif", "nvl", "nvl2",
    "json_object", "json_array", "json_extract", "json_value", "openjson",
    "json_contains", "json_exists", "json_modify", "jsonb_set", "json_build_object",
    "json_set", "json_replace", "json_insert", "json_remove",
    "recursive", "with", "connect by", "prior", "lateral", "apply",
    "group_concat", "listagg", "string_agg",
]

SENSITIVE_DATA_TYPES = [
    "TIMESTAMP", "DATETIME", "DATE", "TIME", "TIMESTAMPTZ",
    "TIMESTAMP_S", "TIMESTAMP_MS", "TIMESTAMP_NS", "DATETIMEOFFSET", "DATETIME2",
    "JSON", "JSONB", "ARRAY", "XML", "BLOB", "CLOB", "TEXT",
    "VARCHAR", "VARCHAR2", "CHAR", "NVARCHAR", "NCHAR", "STRING", "CHARACTER VARYING",
    "NUMBER", "DECIMAL", "NUMERIC", "MONEY", "SMALLMONEY", "REAL", "FLOAT", "DOUBLE",
    "HUGEINT", "BIGINT", "TINYINT", "SMALLINT",
]

FUNCTIONAL_CATEGORIES = [
    "Current_Time_Retrieval",
    "Date_Component_Extraction",
    "Date_Arithmetic",
    "Date_Truncation",
    "Age_And_Interval_Calculation",
    "String_Substring_Extraction",
    "String_Splitting",
    "String_Pattern_Matching",
    "Data_Type_Conversion",
    "Data_Formatting",
    "Result_Pagination",
    "Null_Sorting",
    "Conditional_Aggregation",
    "Deduplication_Aggregation",
    "Ratio_And_Growth_Calculation",
    "Window_Function_Ranking",
    "Window_Function_Offset",
    "Window_Function_Aggregation",
    "Data_Bucketing",
    "JSON_Object_Construction",
    "JSON_Path_Extraction",
    "JSON_Existence_Check",
    "JSON_Modification",
    "Conditional_Branching",
    "Null_Handling",
    "Range_Filtering",
    "Virtual_Table_Query",
    "Correlated_Subquery",
    "Recursive_Query",
    "Mathematical_Calculation",
    "Other_Dialect_Specific",
]
