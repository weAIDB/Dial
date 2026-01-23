# sql_utils.py
import re


def clean_sql_for_execution(sql: str, db_type: str = "oracle") -> str:
    """
    清洗 SQL 语句以适配 Python 数据库驱动的执行要求。
    特别是针对 Oracle，必须移除末尾的分号。

    :param sql: 原始 SQL 语句
    :param db_type: 数据库类型
    :return: 可执行的 SQL 语句（无末尾分号）
    """
    if not sql:
        return ""

    # 1. 去除首尾空白字符
    cleaned_sql = sql.strip()

    # 2. 针对所有数据库（尤其是 Oracle），移除末尾的分号
    # Python 的 DB-API (如 oracledb, psycopg2) 通常不支持单条执行时带分号
    while cleaned_sql.endswith(';'):
        cleaned_sql = cleaned_sql[:-1].strip()

    # 3. (可选) 针对 Oracle 的额外清理：移除可能存在的 "/" (SQLPlus 结束符)
    if "oracle" in db_type.lower():
        if cleaned_sql.endswith('/'):
            cleaned_sql = cleaned_sql[:-1].strip()

    return cleaned_sql