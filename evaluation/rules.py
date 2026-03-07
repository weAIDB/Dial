"""
Classification rules for SQL dialect differences.

Each rule defines:
- dialect: The primary dialect this rule identifies
- main: Main category of the difference
- sub: Sub-category
- detail: Detailed description
- pattern: Regex pattern to match
- positive: Dialects where the pattern SHOULD match
- negative: Dialects where the pattern should NOT match

Rules are organized by dialect for clarity.
"""

# =============================================================================
# SQLite-specific rules
# =============================================================================
SQLITE_RULES = [
    {
        'dialect': 'sqlite',
        'main': 'Syntax Difference',
        'sub': 'Function',
        'detail': 'JSON Extraction (json_extract)',
        'pattern': r'\bjson_extract\s*\(',
        'positive': ['sqlite'],
        'negative': ['mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'sqlite',
        'main': 'Syntax Difference',
        'sub': 'Data Type Conversion',
        'detail': 'CAST AS INTEGER',
        'pattern': r'\bCAST\s*\([^)]+\s+AS\s+INTEGER\b',
        'positive': ['sqlite'],
        'negative': ['mysql', 'sqlserver']
    },
    {
        'dialect': 'sqlite',
        'main': 'Syntax Difference',
        'sub': 'Function',
        'detail': 'Date/Time Function (strftime)',
        'pattern': r'\bstrftime\s*\(',
        'positive': ['sqlite'],
        'negative': ['mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'sqlite',
        'main': 'Syntax Difference',
        'sub': 'Function',
        'detail': 'Date/Time Function (julianday)',
        'pattern': r'\bjulianday\s*\(',
        'positive': ['sqlite'],
        'negative': ['mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'sqlite',
        'main': 'Syntax Difference',
        'sub': 'Function',
        'detail': 'Date/Time Function (date)',
        'pattern': r'\bdate\s*\([^)]+\)',
        'positive': ['sqlite'],
        'negative': ['mysql', 'postgres', 'sqlserver']
    },
    {
        'dialect': 'sqlite',
        'main': 'Syntax Difference',
        'sub': 'Function',
        'detail': 'Random Number (RANDOM)',
        'pattern': r'\bRANDOM\s*\(\)',
        'positive': ['sqlite', 'postgres'],
        'negative': ['mysql', 'sqlserver']
    },
    {
        'dialect': 'sqlite',
        'main': 'Syntax Difference',
        'sub': 'Function',
        'detail': 'Inline Max (MAX with multiple args)',
        'pattern': r'\bMAX\s*\([^,)]+,\s*[^)]+\)',
        'positive': ['sqlite'],
        'negative': ['mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'sqlite',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'SUBSTR Function',
        'pattern': r'\bSUBSTR\s*\(',
        'positive': ['sqlite'],
        'negative': ['sqlserver']
    },
    {
        'dialect': 'sqlite',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'INSTR Function',
        'pattern': r'\bINSTR\s*\(',
        'positive': ['sqlite', 'mysql'],
        'negative': ['postgres', 'sqlserver']
    },
    {
        'dialect': 'sqlite',
        'main': 'Syntax Difference',
        'sub': 'NULL Handling',
        'detail': 'IFNULL Function',
        'pattern': r'\bIFNULL\s*\(',
        'positive': ['sqlite', 'mysql'],
        'negative': ['postgres', 'sqlserver']
    },
    {
        'dialect': 'sqlite',
        'main': 'Syntax Difference',
        'sub': 'Conditional Logic',
        'detail': 'IIF Function',
        'pattern': r'\bIIF\s*\(',
        'positive': ['sqlite', 'sqlserver'],
        'negative': ['mysql', 'postgres']
    },
    {
        'dialect': 'sqlite',
        'main': 'Syntax Difference',
        'sub': 'JSON Function',
        'detail': 'JSON Array Aggregation (json_group_array)',
        'pattern': r'\bjson_group_array\s*\(',
        'positive': ['sqlite'],
        'negative': ['mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'sqlite',
        'main': 'Syntax Difference',
        'sub': 'Aggregate Function',
        'detail': 'GROUP_CONCAT',
        'pattern': r'\bGROUP_CONCAT\s*\(',
        'positive': ['sqlite', 'mysql'],
        'negative': ['postgres', 'sqlserver']
    },
    {
        'dialect': 'sqlite',
        'main': 'Data Type Difference',
        'sub': 'Type Conversion',
        'detail': 'CAST AS REAL',
        'pattern': r'\bCAST\s*\([^)]+\s+AS\s+REAL\b',
        'positive': ['sqlite'],
        'negative': ['mysql', 'sqlserver']
    },
]

# =============================================================================
# MySQL-specific rules
# =============================================================================
MYSQL_RULES = [
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'Function',
        'detail': 'JSON Extraction (JSON_EXTRACT)',
        'pattern': r'\bJSON_EXTRACT\s*\(',
        'positive': ['mysql'],
        'negative': ['sqlite', 'postgres', 'sqlserver']
    },
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'Data Type Conversion',
        'detail': 'CAST AS SIGNED/UNSIGNED',
        'pattern': r'\bCAST\s*\([^)]+\s+AS\s+(SIGNED|UNSIGNED)\b',
        'positive': ['mysql'],
        'negative': ['sqlite', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'NOW/CURDATE',
        'pattern': r'\b(NOW|CURDATE|CURTIME)\s*\(\)',
        'positive': ['mysql'],
        'negative': ['sqlite', 'postgres', 'sqlserver']
    },
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'YEAR/MONTH/DAY Functions',
        'pattern': r'\b(YEAR|MONTH|DAY|HOUR|MINUTE|SECOND)\s*\([^)]+\)',
        'positive': ['mysql'],
        'negative': ['sqlite', 'postgres']
    },
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'DATE_FORMAT',
        'pattern': r'\bDATE_FORMAT\s*\(',
        'positive': ['mysql'],
        'negative': ['sqlite', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'INTERVAL Expression',
        'pattern': r'\bINTERVAL\s+\d+\s+(DAY|MONTH|YEAR|HOUR|MINUTE|SECOND)\b',
        'positive': ['mysql', 'postgres'],
        'negative': ['sqlite', 'sqlserver']
    },
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'SUBSTRING_INDEX',
        'pattern': r'\bSUBSTRING_INDEX\s*\(',
        'positive': ['mysql'],
        'negative': ['sqlite', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'Identifier Quoting',
        'detail': 'Backtick Identifiers',
        'pattern': r'`[^`]+`',
        'positive': ['mysql'],
        'negative': ['postgres', 'sqlserver']
    },
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'CONCAT Function',
        'pattern': r'\bCONCAT\s*\(',
        'positive': ['mysql', 'sqlserver'],
        'negative': ['sqlite']
    },
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'LOCATE Function',
        'pattern': r'\bLOCATE\s*\(',
        'positive': ['mysql'],
        'negative': ['sqlite', 'postgres', 'sqlserver']
    },
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'CHAR_LENGTH Function',
        'pattern': r'\bCHAR_LENGTH\s*\(',
        'positive': ['mysql', 'postgres'],
        'negative': ['sqlite', 'sqlserver']
    },
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'Aggregate Function',
        'detail': 'GROUP_CONCAT with SEPARATOR',
        'pattern': r'\bGROUP_CONCAT\s*\([^)]*SEPARATOR\s+',
        'positive': ['mysql'],
        'negative': ['sqlite', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'Function',
        'detail': 'Random Number (RAND)',
        'pattern': r'\bRAND\s*\(\)',
        'positive': ['mysql', 'sqlserver'],
        'negative': ['sqlite', 'postgres']
    },
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'DML Statement',
        'detail': 'ON DUPLICATE KEY UPDATE',
        'pattern': r'\bON\s+DUPLICATE\s+KEY\s+UPDATE\b',
        'positive': ['mysql'],
        'negative': ['sqlite', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'Pagination',
        'detail': 'LIMIT offset,count Syntax',
        'pattern': r'\bLIMIT\s+\d+\s*,\s*\d+',
        'positive': ['mysql'],
        'negative': ['postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'LPAD/RPAD Functions',
        'pattern': r'\b(LPAD|RPAD)\s*\(',
        'positive': ['mysql', 'postgres'],
        'negative': ['sqlite', 'sqlserver']
    },
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'Math Function',
        'detail': 'POWER Function',
        'pattern': r'\bPOWER\s*\(',
        'positive': ['mysql', 'postgres', 'sqlserver'],
        'negative': ['sqlite']
    },
    {
        'dialect': 'mysql',
        'main': 'Data Type Difference',
        'sub': 'Type Conversion',
        'detail': 'CAST AS FLOAT',
        'pattern': r'\bCAST\s*\([^)]+\s+AS\s+FLOAT\b',
        'positive': ['mysql', 'sqlserver'],
        'negative': ['sqlite', 'postgres']
    },
]

# =============================================================================
# PostgreSQL-specific rules
# =============================================================================
POSTGRES_RULES = [
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'Function',
        'detail': 'JSON Extraction (JSON_EXTRACT_PATH)',
        'pattern': r'\bJSON_EXTRACT_PATH(_TEXT)?\s*\(',
        'positive': ['postgres'],
        'negative': ['sqlite', 'mysql', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'Identifier Quoting',
        'detail': 'Double Quote Identifiers',
        'pattern': r'(FROM|JOIN|UPDATE|INTO)\s+"[^"]+"',
        'positive': ['postgres', 'duckdb'],
        'negative': ['mysql']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'DATE_TRUNC',
        'pattern': r'\bDATE_TRUNC\s*\(',
        'positive': ['postgres', 'duckdb'],
        'negative': ['sqlite', 'mysql', 'sqlserver']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'NULL Handling',
        'detail': 'NULLS FIRST/LAST',
        'pattern': r'\bORDER\s+BY\s+.+\bNULLS\s+(FIRST|LAST)\b',
        'positive': ['postgres', 'sqlite', 'duckdb'],
        'negative': ['mysql', 'sqlserver']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'SPLIT_PART Function',
        'pattern': r'\bSPLIT_PART\s*\(',
        'positive': ['postgres', 'duckdb'],
        'negative': ['sqlite', 'mysql', 'sqlserver']
    },
    {
        'dialect': 'postgres',
        'main': 'Data Type Difference',
        'sub': 'Type Conversion',
        'detail': 'Concise Type Cast (::)',
        'pattern': r'::\s*(integer|int|text|varchar|numeric|date|timestamp|float|double|boolean)\b',
        'positive': ['postgres', 'duckdb'],
        'negative': ['sqlite', 'mysql', 'sqlserver']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'STRPOS Function',
        'pattern': r'\bSTRPOS\s*\(',
        'positive': ['postgres', 'duckdb'],
        'negative': ['sqlite', 'mysql', 'sqlserver']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'Aggregate Function',
        'detail': 'STRING_AGG Function',
        'pattern': r'\bSTRING_AGG\s*\(',
        'positive': ['postgres', 'sqlserver', 'duckdb'],
        'negative': ['sqlite', 'mysql']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'TO_CHAR Function',
        'pattern': r'\bTO_CHAR\s*\(',
        'positive': ['postgres', 'duckdb'],
        'negative': ['sqlite', 'mysql', 'sqlserver']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'EXTRACT FROM',
        'pattern': r'\bEXTRACT\s*\(\s*(YEAR|MONTH|DAY|HOUR|MINUTE|SECOND|DOW|DOY|WEEK)\s+FROM\b',
        'positive': ['postgres', 'duckdb'],
        'negative': ['sqlite', 'mysql']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'Comparison Operator',
        'detail': 'ILIKE (Case-insensitive)',
        'pattern': r'\bILIKE\b',
        'positive': ['postgres', 'duckdb'],
        'negative': ['sqlite', 'mysql', 'sqlserver']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'DML Statement',
        'detail': 'RETURNING Clause',
        'pattern': r'\bRETURNING\b',
        'positive': ['postgres', 'sqlite', 'duckdb'],
        'negative': ['mysql']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'DML Statement',
        'detail': 'ON CONFLICT DO UPDATE',
        'pattern': r'\bON\s+CONFLICT\b',
        'positive': ['postgres', 'sqlite', 'duckdb'],
        'negative': ['mysql', 'sqlserver']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'Pagination',
        'detail': 'LIMIT OFFSET Syntax',
        'pattern': r'\bLIMIT\s+\d+\s+OFFSET\s+\d+',
        'positive': ['postgres', 'sqlite', 'duckdb'],
        'negative': ['mysql', 'sqlserver']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'SUBSTRING FROM Syntax',
        'pattern': r'\bSUBSTRING\s*\([^)]+\s+FROM\s+',
        'positive': ['postgres'],
        'negative': ['sqlite', 'mysql', 'sqlserver']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'Math Operation',
        'detail': 'Power Operator (^)',
        'pattern': r'\s\^\s',
        'positive': ['postgres'],
        'negative': ['sqlite', 'mysql', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'Function',
        'detail': 'GREATEST/LEAST Functions',
        'pattern': r'\b(GREATEST|LEAST)\s*\(',
        'positive': ['postgres', 'mysql', 'duckdb'],
        'negative': ['sqlite', 'sqlserver']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'Boolean',
        'detail': 'Boolean Literals (TRUE/FALSE)',
        'pattern': r'\b(TRUE|FALSE)\b',
        'positive': ['postgres', 'mysql', 'duckdb'],
        'negative': ['sqlserver']
    },
]

# =============================================================================
# SQL Server-specific rules
# =============================================================================
SQLSERVER_RULES = [
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'Aggregate Function',
        'detail': 'COUNT_BIG Function',
        'pattern': r'\bCOUNT_BIG\s*\(',
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'mysql', 'postgres', 'duckdb']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'Pagination',
        'detail': 'TOP Clause',
        'pattern': r'\bSELECT\s+TOP\s+\d+\b',
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'mysql', 'postgres', 'duckdb']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'Pagination',
        'detail': 'TOP with PERCENT',
        'pattern': r'\bTOP\s+\d+\s+PERCENT\b',
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'mysql', 'postgres', 'duckdb']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'Pagination',
        'detail': 'OFFSET FETCH',
        'pattern': r'\bOFFSET\s+\d+\s+ROWS?\s+FETCH\s+(FIRST|NEXT)\s+\d+\s+ROWS?\s+ONLY\b',
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'mysql', 'duckdb']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'GETDATE Function',
        'pattern': r'\bGETDATE\s*\(\)',
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'mysql', 'postgres', 'duckdb']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'GETUTCDATE Function',
        'pattern': r'\bGETUTCDATE\s*\(\)',
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'mysql', 'postgres', 'duckdb']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'DATEADD Function',
        'pattern': r'\bDATEADD\s*\(',
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'mysql', 'postgres', 'duckdb']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'DATEDIFF Function',
        'pattern': r'\bDATEDIFF\s*\(',
        'positive': ['sqlserver', 'mysql'],
        'negative': ['sqlite', 'postgres']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'DATEPART Function',
        'pattern': r'\bDATEPART\s*\(',
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'mysql', 'postgres', 'duckdb']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'DATENAME Function',
        'pattern': r'\bDATENAME\s*\(',
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'mysql', 'postgres', 'duckdb']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'Type Conversion',
        'detail': 'CONVERT Function',
        'pattern': r'\bCONVERT\s*\(\s*(VARCHAR|NVARCHAR|INT|FLOAT|DATETIME|DATE)',
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'postgres', 'duckdb']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'Identifier Quoting',
        'detail': 'Square Bracket Identifiers',
        'pattern': r'\[[^\]]+\]',
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'mysql', 'postgres', 'duckdb']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'String Concatenation',
        'detail': 'Plus Operator for Strings',
        'pattern': r"'[^']*'\s*\+\s*'[^']*'",
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'postgres', 'duckdb']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'NULL Handling',
        'detail': 'ISNULL Function',
        'pattern': r'\bISNULL\s*\(',
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'postgres', 'duckdb']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'LEN Function',
        'pattern': r'\bLEN\s*\(',
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'mysql', 'postgres', 'duckdb']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'CHARINDEX Function',
        'pattern': r'\bCHARINDEX\s*\(',
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'mysql', 'postgres', 'duckdb']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'PATINDEX Function',
        'pattern': r'\bPATINDEX\s*\(',
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'mysql', 'postgres', 'duckdb']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'CTE',
        'detail': 'WITH (NOLOCK) Hint',
        'pattern': r'\bWITH\s*\(\s*NOLOCK\s*\)',
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'mysql', 'postgres', 'duckdb']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'Data Type',
        'detail': 'NVARCHAR Type',
        'pattern': r'\bNVARCHAR\s*\(',
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'mysql', 'postgres', 'duckdb']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'DML Statement',
        'detail': 'MERGE Statement',
        'pattern': r'\bMERGE\s+INTO\b',
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'mysql']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'Window Function',
        'detail': 'ROW_NUMBER with ORDER BY',
        'pattern': r'\bROW_NUMBER\s*\(\s*\)\s+OVER\s*\(',
        'positive': ['sqlserver', 'postgres', 'mysql', 'duckdb'],
        'negative': ['sqlite']
    },
]

# =============================================================================
# DuckDB-specific rules
# =============================================================================
DUCKDB_RULES = [
    {
        'dialect': 'duckdb',
        'main': 'Syntax Difference',
        'sub': 'SELECT Clause',
        'detail': 'EXCLUDE Clause',
        'pattern': r'\bEXCLUDE\s*\(',
        'positive': ['duckdb'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver']
    },
    {
        'dialect': 'duckdb',
        'main': 'Syntax Difference',
        'sub': 'SELECT Clause',
        'detail': 'REPLACE Clause',
        'pattern': r'\bREPLACE\s*\([^)]+\s+AS\s+',
        'positive': ['duckdb'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver']
    },
    {
        'dialect': 'duckdb',
        'main': 'Syntax Difference',
        'sub': 'List Operations',
        'detail': 'List Syntax []',
        'pattern': r'\[\s*[^\]]+\s*\]',
        'positive': ['duckdb', 'postgres'],
        'negative': ['sqlite', 'mysql']
    },
    {
        'dialect': 'duckdb',
        'main': 'Syntax Difference',
        'sub': 'Aggregate Function',
        'detail': 'LIST_AGG Function',
        'pattern': r'\bLIST_AGG\s*\(',
        'positive': ['duckdb'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver']
    },
    {
        'dialect': 'duckdb',
        'main': 'Syntax Difference',
        'sub': 'Function',
        'detail': 'UNNEST Function',
        'pattern': r'\bUNNEST\s*\(',
        'positive': ['duckdb', 'postgres'],
        'negative': ['sqlite', 'mysql', 'sqlserver']
    },
    {
        'dialect': 'duckdb',
        'main': 'Syntax Difference',
        'sub': 'Sampling',
        'detail': 'SAMPLE Clause',
        'pattern': r'\bUSING\s+SAMPLE\b',
        'positive': ['duckdb'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver']
    },
    {
        'dialect': 'duckdb',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'STRING_SPLIT Function',
        'pattern': r'\bSTRING_SPLIT\s*\(',
        'positive': ['duckdb'],
        'negative': ['sqlite', 'mysql', 'postgres']
    },
    {
        'dialect': 'duckdb',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'EPOCH Function',
        'pattern': r'\bEPOCH\s*\(',
        'positive': ['duckdb'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver']
    },
    {
        'dialect': 'duckdb',
        'main': 'Syntax Difference',
        'sub': 'Aggregate Function',
        'detail': 'ARG_MAX/ARG_MIN Functions',
        'pattern': r'\bARG_(MAX|MIN)\s*\(',
        'positive': ['duckdb'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver']
    },
    {
        'dialect': 'duckdb',
        'main': 'Syntax Difference',
        'sub': 'Window Function',
        'detail': 'QUALIFY Clause',
        'pattern': r'\bQUALIFY\b',
        'positive': ['duckdb'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver']
    },
]

# =============================================================================
# Oracle-specific rules
# =============================================================================
ORACLE_RULES = [
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Identifier Quoting',
        'detail': 'Double-quoted Identifiers (Oracle style)',
        'pattern': r'"[A-Z_][A-Z0-9_]*"',
        'positive': ['oracle'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'NULL Ordering',
        'detail': 'NULLS LAST clause',
        'pattern': r'\bNULLS\s+LAST\b',
        'positive': ['oracle', 'postgres'],
        'negative': ['sqlite', 'mysql', 'sqlserver']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'NULL Ordering',
        'detail': 'NULLS FIRST clause',
        'pattern': r'\bNULLS\s+FIRST\b',
        'positive': ['oracle', 'postgres'],
        'negative': ['sqlite', 'mysql', 'sqlserver']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Data Type Conversion',
        'detail': 'CAST AS FLOAT',
        'pattern': r'\bCAST\s*\([^)]+\s+AS\s+FLOAT\b',
        'positive': ['oracle', 'mysql', 'sqlserver'],
        'negative': ['sqlite']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Data Type Conversion',
        'detail': 'TO_NUMBER Function',
        'pattern': r'\bTO_NUMBER\s*\(',
        'positive': ['oracle'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Data Type Conversion',
        'detail': 'TO_CHAR Function',
        'pattern': r'\bTO_CHAR\s*\(',
        'positive': ['oracle', 'postgres'],
        'negative': ['sqlite', 'mysql', 'sqlserver']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Data Type Conversion',
        'detail': 'TO_DATE Function',
        'pattern': r'\bTO_DATE\s*\(',
        'positive': ['oracle'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'NVL Function (NULL handling)',
        'pattern': r'\bNVL\s*\(',
        'positive': ['oracle'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'NVL2 Function',
        'pattern': r'\bNVL2\s*\(',
        'positive': ['oracle'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'DECODE Function',
        'pattern': r'\bDECODE\s*\(',
        'positive': ['oracle'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'SYSDATE',
        'pattern': r'\bSYSDATE\b',
        'positive': ['oracle'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'SYSTIMESTAMP',
        'pattern': r'\bSYSTIMESTAMP\b',
        'positive': ['oracle'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'ADD_MONTHS Function',
        'pattern': r'\bADD_MONTHS\s*\(',
        'positive': ['oracle'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'MONTHS_BETWEEN Function',
        'pattern': r'\bMONTHS_BETWEEN\s*\(',
        'positive': ['oracle'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Pseudo Table',
        'detail': 'DUAL Table',
        'pattern': r'\bFROM\s+DUAL\b',
        'positive': ['oracle'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Sequence',
        'detail': 'NEXTVAL/CURRVAL',
        'pattern': r'\b(NEXTVAL|CURRVAL)\b',
        'positive': ['oracle', 'postgres'],
        'negative': ['sqlite', 'mysql', 'sqlserver']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Row Limiting',
        'detail': 'ROWNUM',
        'pattern': r'\bROWNUM\b',
        'positive': ['oracle'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Row Limiting',
        'detail': 'FETCH FIRST/NEXT',
        'pattern': r'\bFETCH\s+(FIRST|NEXT)\b',
        'positive': ['oracle', 'postgres', 'sqlserver'],
        'negative': ['sqlite', 'mysql']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'String Concatenation',
        'detail': 'Double Pipe Operator (||)',
        'pattern': r'\|\|',
        'positive': ['oracle', 'sqlite', 'postgres', 'duckdb'],
        'negative': ['mysql', 'sqlserver']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Hierarchical Query',
        'detail': 'CONNECT BY',
        'pattern': r'\bCONNECT\s+BY\b',
        'positive': ['oracle'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Hierarchical Query',
        'detail': 'START WITH',
        'pattern': r'\bSTART\s+WITH\b',
        'positive': ['oracle'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Analytic Function',
        'detail': 'LISTAGG Function',
        'pattern': r'\bLISTAGG\s*\(',
        'positive': ['oracle', 'duckdb'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Analytic Function',
        'detail': 'LISTAGG with WITHIN GROUP',
        'pattern': r'\bLISTAGG\s*\([^)]*\)\s*WITHIN\s+GROUP',
        'positive': ['oracle'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Analytic Function',
        'detail': 'WITHIN GROUP Clause',
        'pattern': r'\bWITHIN\s+GROUP\s*\(',
        'positive': ['oracle', 'postgres'],
        'negative': ['sqlite', 'mysql', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'TRUNC (Date Truncation)',
        'pattern': r'\bTRUNC\s*\(',
        'positive': ['oracle'],
        'negative': ['sqlite', 'mysql', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'INITCAP Function',
        'pattern': r'\bINITCAP\s*\(',
        'positive': ['oracle', 'postgres'],
        'negative': ['sqlite', 'mysql', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'EXTRACT Function',
        'pattern': r'\bEXTRACT\s*\(\s*(YEAR|MONTH|DAY|HOUR|MINUTE|SECOND)\s+FROM\b',
        'positive': ['oracle', 'postgres', 'mysql'],
        'negative': ['sqlite', 'sqlserver']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'REGEXP_LIKE Function',
        'pattern': r'\bREGEXP_LIKE\s*\(',
        'positive': ['oracle'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'REGEXP_SUBSTR Function',
        'pattern': r'\bREGEXP_SUBSTR\s*\(',
        'positive': ['oracle'],
        'negative': ['sqlite', 'mysql', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'REGEXP_REPLACE Function',
        'pattern': r'\bREGEXP_REPLACE\s*\(',
        'positive': ['oracle', 'postgres'],
        'negative': ['sqlite', 'mysql', 'sqlserver']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Analytic Function',
        'detail': 'OVER (PARTITION BY)',
        'pattern': r'\bOVER\s*\(\s*PARTITION\s+BY\b',
        'positive': ['oracle', 'postgres', 'sqlserver', 'mysql'],
        'negative': ['sqlite']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Row Limiting',
        'detail': 'OFFSET ROWS',
        'pattern': r'\bOFFSET\s+\d+\s+ROWS?\b',
        'positive': ['oracle', 'sqlserver'],
        'negative': ['sqlite', 'mysql', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'Date/Time Function',
        'detail': 'INTERVAL Literal',
        'pattern': r"\bINTERVAL\s+'[^']+'\s+(YEAR|MONTH|DAY|HOUR|MINUTE|SECOND)",
        'positive': ['oracle'],
        'negative': ['sqlite', 'mysql', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'LPAD Function',
        'pattern': r'\bLPAD\s*\(',
        'positive': ['oracle', 'mysql', 'postgres'],
        'negative': ['sqlite', 'sqlserver']
    },
    {
        'dialect': 'oracle',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'RPAD Function',
        'pattern': r'\bRPAD\s*\(',
        'positive': ['oracle', 'mysql', 'postgres'],
        'negative': ['sqlite', 'sqlserver']
    },
]

# =============================================================================
# Cross-dialect / Shared rules
# =============================================================================
SHARED_RULES = [
    # =========================================================================
    # NULL Ordering (NULLS FIRST/LAST) - Very common pattern!
    # positive = dialects where the pattern ACTUALLY APPEARS in the SQL
    # negative = dialects where the pattern should NOT appear
    # =========================================================================
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'NULL Ordering',
        'detail': 'NULLS LAST in ORDER BY',
        'pattern': r'\bNULLS\s+LAST\b',
        'positive': ['postgres'],  # Only postgres/duckdb actually use this
        'negative': ['sqlite', 'mysql', 'sqlserver']
    },
    {
        'dialect': 'duckdb',
        'main': 'Syntax Difference',
        'sub': 'NULL Ordering',
        'detail': 'NULLS LAST in ORDER BY',
        'pattern': r'\bNULLS\s+LAST\b',
        'positive': ['duckdb'],
        'negative': ['sqlite', 'mysql', 'sqlserver']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'NULL Ordering',
        'detail': 'NULLS FIRST in ORDER BY',
        'pattern': r'\bNULLS\s+FIRST\b',
        'positive': ['postgres'],
        'negative': ['mysql', 'sqlserver']
    },
    {
        'dialect': 'duckdb',
        'main': 'Syntax Difference',
        'sub': 'NULL Ordering',
        'detail': 'NULLS FIRST in ORDER BY',
        'pattern': r'\bNULLS\s+FIRST\b',
        'positive': ['duckdb'],
        'negative': ['mysql', 'sqlserver']
    },

    # =========================================================================
    # NULLIF Function - used in postgres/sqlserver when sqlite doesn't have it
    # =========================================================================
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'NULL Handling',
        'detail': 'NULLIF Function',
        'pattern': r'\bNULLIF\s*\(',
        'positive': ['postgres'],
        'negative': ['sqlite']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'NULL Handling',
        'detail': 'NULLIF Function',
        'pattern': r'\bNULLIF\s*\(',
        'positive': ['sqlserver'],
        'negative': ['sqlite']
    },
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'NULL Handling',
        'detail': 'NULLIF Function',
        'pattern': r'\bNULLIF\s*\(',
        'positive': ['mysql'],
        'negative': ['sqlite']
    },
    {
        'dialect': 'duckdb',
        'main': 'Syntax Difference',
        'sub': 'NULL Handling',
        'detail': 'NULLIF Function',
        'pattern': r'\bNULLIF\s*\(',
        'positive': ['duckdb'],
        'negative': ['sqlite']
    },

    # =========================================================================
    # Math Functions - CEILING vs CEIL
    # =========================================================================
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'Math Function',
        'detail': 'CEILING Function',
        'pattern': r'\bCEILING\s*\(',
        'positive': ['sqlserver'],
        'negative': ['sqlite', 'postgres', 'duckdb']
    },
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'Math Function',
        'detail': 'CEIL Function',
        'pattern': r'\bCEIL\s*\(',
        'positive': ['mysql'],
        'negative': ['sqlite', 'sqlserver']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'Math Function',
        'detail': 'CEIL Function',
        'pattern': r'\bCEIL\s*\(',
        'positive': ['postgres'],
        'negative': ['sqlite', 'sqlserver']
    },
    {
        'dialect': 'duckdb',
        'main': 'Syntax Difference',
        'sub': 'Math Function',
        'detail': 'CEIL Function',
        'pattern': r'\bCEIL\s*\(',
        'positive': ['duckdb'],
        'negative': ['sqlite', 'sqlserver']
    },

    # =========================================================================
    # Character Code Functions - ORD vs ASCII
    # =========================================================================
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'ORD Function (Character Code)',
        'pattern': r'\bORD\s*\(',
        'positive': ['mysql'],
        'negative': ['sqlite', 'postgres', 'sqlserver', 'duckdb']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'ASCII Function (Character Code)',
        'pattern': r'\bASCII\s*\(',
        'positive': ['postgres'],
        'negative': ['sqlite']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'ASCII Function (Character Code)',
        'pattern': r'\bASCII\s*\(',
        'positive': ['sqlserver'],
        'negative': ['sqlite']
    },

    # =========================================================================
    # LOG Function variations
    # =========================================================================
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'Math Function',
        'detail': 'LOG Function',
        'pattern': r'\bLOG\s*\(',
        'positive': ['mysql'],
        'negative': ['sqlite']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'Math Function',
        'detail': 'LOG Function',
        'pattern': r'\bLOG\s*\(',
        'positive': ['postgres'],
        'negative': ['sqlite']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'Math Function',
        'detail': 'LOG Function',
        'pattern': r'\bLOG\s*\(',
        'positive': ['sqlserver'],
        'negative': ['sqlite']
    },
    {
        'dialect': 'duckdb',
        'main': 'Syntax Difference',
        'sub': 'Math Function',
        'detail': 'LOG Function',
        'pattern': r'\bLOG\s*\(',
        'positive': ['duckdb'],
        'negative': ['sqlite']
    },

    # =========================================================================
    # TRIM Function variations
    # =========================================================================
    {
        'dialect': 'mysql',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'TRIM Function',
        'pattern': r'\bTRIM\s*\(',
        'positive': ['mysql'],
        'negative': ['sqlite']
    },
    {
        'dialect': 'postgres',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'TRIM Function',
        'pattern': r'\bTRIM\s*\(',
        'positive': ['postgres'],
        'negative': ['sqlite']
    },
    {
        'dialect': 'sqlserver',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'TRIM Function',
        'pattern': r'\bTRIM\s*\(',
        'positive': ['sqlserver'],
        'negative': ['sqlite']
    },
    {
        'dialect': 'duckdb',
        'main': 'Syntax Difference',
        'sub': 'String Function',
        'detail': 'TRIM Function',
        'pattern': r'\bTRIM\s*\(',
        'positive': ['duckdb'],
        'negative': ['sqlite']
    },

    # =========================================================================
    # Original shared rules
    # =========================================================================
    {
        'dialect': 'shared',
        'main': 'Syntax Difference',
        'sub': 'String Concatenation',
        'detail': 'Double Pipe Operator (||)',
        'pattern': r'\|\|',
        'positive': ['sqlite', 'postgres', 'duckdb'],
        'negative': ['mysql', 'sqlserver']
    },
    {
        'dialect': 'shared',
        'main': 'Syntax Difference',
        'sub': 'NULL Handling',
        'detail': 'COALESCE Function',
        'pattern': r'\bCOALESCE\s*\(',
        'positive': ['sqlite', 'mysql', 'postgres', 'sqlserver', 'duckdb'],
        'negative': []
    },
    {
        'dialect': 'shared',
        'main': 'Syntax Difference',
        'sub': 'Conditional',
        'detail': 'CASE WHEN Expression',
        'pattern': r'\bCASE\s+WHEN\b',
        'positive': ['sqlite', 'mysql', 'postgres', 'sqlserver', 'duckdb'],
        'negative': []
    },
]

# =============================================================================
# Combined rules list
# =============================================================================
ALL_CLASSIFICATION_RULES = (
    SQLITE_RULES +
    MYSQL_RULES +
    POSTGRES_RULES +
    SQLSERVER_RULES +
    DUCKDB_RULES +
    ORACLE_RULES +
    SHARED_RULES
)
