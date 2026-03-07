# sql_utils.py
import re


def clean_sql_for_execution(sql: str, db_type: str = "oracle") -> str:
    """
    Cleans the SQL statement to adapt to the execution requirements of Python database drivers.
    Specifically for Oracle, trailing semicolons must be removed.

    :param sql: Original SQL statement
    :param db_type: Database type
    :param return: Executable SQL statement (without trailing semicolon)
    """
    if not sql:
        return ""

    # 1. Remove leading and trailing whitespace characters
    cleaned_sql = sql.strip()

    # 2. For all databases (especially Oracle), remove the trailing semicolon
    # Python's DB-API (e.g., oracledb, psycopg2) usually does not support semicolons in single executions
    while cleaned_sql.endswith(';'):
        cleaned_sql = cleaned_sql[:-1].strip()

    # 3. (Optional) Additional cleaning for Oracle: Remove potential "/" (SQLPlus terminator)
    if "oracle" in db_type.lower():
        if cleaned_sql.endswith('/'):
            cleaned_sql = cleaned_sql[:-1].strip()

    return cleaned_sql