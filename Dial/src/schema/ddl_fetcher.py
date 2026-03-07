# src/schema/ddl_fetcher.py
# Fetches DDL (CREATE TABLE) and optional column examples for SQLite, MySQL, PostgreSQL,
# SQL Server, DuckDB, and Oracle. Used by the NL-LQP generation stage to enrich prompts.

import os
import sqlite3

try:
    import pymysql
except ImportError:
    pymysql = None
try:
    import psycopg2
except ImportError:
    psycopg2 = None
try:
    import pyodbc
except ImportError:
    pyodbc = None
try:
    import duckdb
except ImportError:
    duckdb = None
try:
    import oracledb
except ImportError:
    oracledb = None


class DDLFetcher:
    """Fetches DDL for given db_id and table list per dialect. Config must provide PATHS and DB_CONN."""

    def __init__(self, config):
        self.config = config
        self.sqlite_dir = config["PATHS"]["sqlite_db_dir"]
        self.mysql_cfg = config["DB_CONN"]["mysql"]
        self.pg_cfg = config["DB_CONN"]["postgres"]
        self.sqlserver_cfg = config["DB_CONN"].get("sqlserver")
        self.duckdb_dir = config["PATHS"].get("duckdb_dir")
        self.oracle_cfg = config["DB_CONN"].get("oracle")

    def extract_tables(self, true_tables_columns_str):
        """Parse 'Table.Column, ...' string into list of table names."""
        if not true_tables_columns_str:
            return []
        tables = set()
        for item in true_tables_columns_str.split(","):
            item = item.strip()
            if "." in item:
                tables.add(item.split(".")[0])
        return list(tables)

    def execute_sql(self, dialect_key, db_id, sql):
        """Execute SQL on the given dialect and db_id. Returns (success: bool, error_message or None)."""
        try:
            if dialect_key == "sqlite":
                db_path = os.path.join(self.sqlite_dir, db_id, f"{db_id}.sqlite")
                conn = sqlite3.connect(db_path)
                conn.cursor().execute(sql)
                conn.close()
            elif dialect_key == "mysql":
                conn = pymysql.connect(database=db_id, **self.mysql_cfg)
                conn.cursor().execute(sql)
                conn.close()
            elif dialect_key == "postgres":
                pg_args = self.pg_cfg.copy()
                pg_args["dbname"] = db_id
                conn = psycopg2.connect(**pg_args)
                conn.cursor().execute(sql)
                conn.close()
            elif dialect_key == "sqlserver":
                conn_str = (
                    f"DRIVER={self.sqlserver_cfg['driver']};SERVER={self.sqlserver_cfg['host']},"
                    f"{self.sqlserver_cfg['port']};DATABASE={db_id};UID={self.sqlserver_cfg['user']};"
                    f"PWD={self.sqlserver_cfg['password']}"
                )
                conn = pyodbc.connect(conn_str)
                conn.cursor().execute(sql)
                conn.close()
            elif dialect_key == "duckdb":
                db_path = os.path.join(self.duckdb_dir, f"{db_id}.duckdb")
                conn = duckdb.connect(db_path, read_only=True)
                conn.cursor().execute(sql)
                conn.close()
            elif dialect_key == "oracle":
                conn = oracledb.connect(
                    user=self.oracle_cfg["user"],
                    password=self.oracle_cfg["password"],
                    dsn=self.oracle_cfg["dsn"],
                )
                cursor = conn.cursor()
                sql = sql.strip().rstrip(";")
                target_schema = db_id.upper()
                if target_schema[0].isdigit():
                    target_schema = f"U_{target_schema}"
                cursor.execute(f'ALTER SESSION SET CURRENT_SCHEMA = "{target_schema}"')
                cursor.execute(sql)
                conn.close()
            return True, None
        except Exception as e:
            return False, str(e)

    def _get_column_examples(self, cursor, table_name, column_name, db_type="generic", limit=3):
        """Append sample values for a column to DDL (for prompt enrichment)."""
        try:
            if db_type == "sqlserver":
                query = f"SELECT DISTINCT TOP {limit} [{column_name}] FROM [{table_name}]"
            else:
                col_q = f'"{column_name}"' if db_type in ["sqlite", "postgres", "duckdb"] else f"`{column_name}`"
                tbl_q = f'"{table_name}"' if db_type in ["sqlite", "postgres", "duckdb"] else f"`{table_name}`"
                query = f"SELECT DISTINCT {col_q} FROM {tbl_q} LIMIT {limit}"
            cursor.execute(query)
            rows = cursor.fetchall()
            values = [r[0] for r in rows if r[0] is not None]
            return f" -- example: {str(values)}" if values else ""
        except Exception:
            return ""

    def get_sqlite_ddl(self, db_id, tables):
        """Return DDL string for SQLite database and given tables."""
        db_path = os.path.join(self.sqlite_dir, db_id, f"{db_id}.sqlite")
        if not os.path.exists(db_path):
            return "-- Error: SQLite file not found"
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            if not tables:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [r[0] for r in cursor.fetchall()]
            schema_lines = []
            for table in tables:
                cursor.execute(f"PRAGMA table_info('{table}')")
                cols = cursor.fetchall()
                lines = [
                    f"    {col[1]} {col[2]} {'NOT NULL' if col[3] else ''}{self._get_column_examples(cursor, table, col[1], 'sqlite')}"
                    for col in cols
                ]
                schema_lines.append(f"CREATE TABLE {table} (\n" + ",\n".join(lines) + "\n);")
            conn.close()
            return "\n\n".join(schema_lines)
        except Exception as e:
            return f"-- SQLite Error: {e}"

    def get_mysql_ddl(self, db_id, tables):
        """Return DDL string for MySQL database and given tables."""
        if not pymysql:
            return "-- PyMySQL not installed"
        try:
            conn = pymysql.connect(database=db_id, **self.mysql_cfg)
            cursor = conn.cursor()
            if not tables:
                cursor.execute("SHOW TABLES")
                tables = [r[0] for r in cursor.fetchall()]
            schema_lines = []
            for table in tables:
                cursor.execute(f"DESCRIBE `{table}`")
                cols = cursor.fetchall()
                lines = [
                    f"    `{c[0]}` {c[1]} {'NOT NULL' if c[2] == 'NO' else ''}{self._get_column_examples(cursor, table, c[0], 'mysql')}"
                    for c in cols
                ]
                schema_lines.append(f"CREATE TABLE `{table}` (\n" + ",\n".join(lines) + "\n);")
            conn.close()
            return "\n\n".join(schema_lines)
        except Exception as e:
            return f"-- MySQL Error: {e}"

    def get_postgres_ddl(self, db_id, tables):
        """Return DDL string for PostgreSQL database and given tables."""
        if not psycopg2:
            return "-- Psycopg2 not installed"
        try:
            pg_args = self.pg_cfg.copy()
            pg_args["dbname"] = db_id
            conn = psycopg2.connect(**pg_args)
            cursor = conn.cursor()
            if not tables:
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
                tables = [r[0] for r in cursor.fetchall()]
            schema_lines = []
            for table in tables:
                cursor.execute(
                    "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = %s",
                    (table,),
                )
                rows = cursor.fetchall()
                lines = [
                    f"    {c[0]} {c[1]} {'NOT NULL' if c[2] == 'NO' else ''}{self._get_column_examples(cursor, table, c[0], 'postgres')}"
                    for c in rows
                ]
                schema_lines.append(f"CREATE TABLE {table} (\n" + ",\n".join(lines) + "\n);")
            conn.close()
            return "\n\n".join(schema_lines)
        except Exception as e:
            return f"-- Postgres Error: {e}"

    def get_sqlserver_ddl(self, db_id, tables):
        """Return DDL string for SQL Server database and given tables."""
        if not pyodbc:
            return "-- pyodbc not installed"
        try:
            conn_str = (
                f"DRIVER={self.sqlserver_cfg['driver']};SERVER={self.sqlserver_cfg['host']},"
                f"{self.sqlserver_cfg['port']};DATABASE={db_id};UID={self.sqlserver_cfg['user']};"
                f"PWD={self.sqlserver_cfg['password']}"
            )
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            if not tables:
                cursor.execute("SELECT name FROM sys.tables")
                tables = [r[0] for r in cursor.fetchall()]
            schema_lines = []
            for table in tables:
                cursor.execute(f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = '{table}'")
                rows = cursor.fetchall()
                lines = [
                    f"    [{c[0]}] {c[1]} {'NOT NULL' if c[2] == 'NO' else ''}{self._get_column_examples(cursor, table, c[0], 'sqlserver')}"
                    for c in rows
                ]
                schema_lines.append(f"CREATE TABLE {table} (\n" + ",\n".join(lines) + "\n);")
            conn.close()
            return "\n\n".join(schema_lines)
        except Exception as e:
            return f"-- SQLServer Error: {e}"

    def get_duckdb_ddl(self, db_id, tables):
        """Return DDL string for DuckDB database and given tables."""
        if not duckdb:
            return "-- duckdb not installed"
        try:
            conn = duckdb.connect(os.path.join(self.duckdb_dir, f"{db_id}.duckdb"), read_only=True)
            cursor = conn.cursor()
            if not tables:
                cursor.execute("SHOW TABLES")
                tables = [r[0] for r in cursor.fetchall()]
            schema_lines = []
            for table in tables:
                cursor.execute(f"DESCRIBE {table}")
                rows = cursor.fetchall()
                lines = [
                    f"    {c[0]} {c[1]} {'NOT NULL' if c[2] == 'NO' else ''}{self._get_column_examples(cursor, table, c[0], 'sqlite')}"
                    for c in rows
                ]
                schema_lines.append(f"CREATE TABLE {table} (\n" + ",\n".join(lines) + "\n);")
            conn.close()
            return "\n\n".join(schema_lines)
        except Exception as e:
            return f"-- DuckDB Error: {e}"

    def get_oracle_ddl(self, db_id, tables):
        """Return DDL string for Oracle schema and given tables."""
        if not oracledb:
            return "-- oracledb not installed"
        target_schema = db_id.upper()
        if target_schema[0].isdigit():
            target_schema = f"U_{target_schema}"

        def _get_column_examples_oracle(conn, t_name, c_name, c_type, limit=3):
            if any(kw in str(c_type).upper() for kw in ["LOB", "LONG", "RAW", "XML"]):
                return " -- examples: [LOB Type]"
            ex_cursor = conn.cursor()
            try:
                ex_query = f'SELECT DISTINCT "{c_name.upper()}" FROM "{target_schema}"."{t_name.upper()}" WHERE "{c_name.upper()}" IS NOT NULL FETCH FIRST {limit} ROWS ONLY'
                ex_cursor.execute(ex_query)
                rows = ex_cursor.fetchall()
                values = [str(r[0])[:50].replace("\n", " ") for r in rows if r[0] is not None]
                return f" -- examples: {values}" if values else " -- examples: []"
            except Exception as e:
                return f" -- examples: [error: {str(e)[:30]}]"
            finally:
                ex_cursor.close()

        try:
            conn = oracledb.connect(
                user=self.oracle_cfg["user"],
                password=self.oracle_cfg["password"],
                dsn=self.oracle_cfg["dsn"],
            )
            cursor = conn.cursor()
            if not tables:
                cursor.execute("SELECT table_name FROM all_tables WHERE owner = :own", {"own": target_schema})
                tables = [r[0] for r in cursor.fetchall()]
            else:
                tables = [t.upper() for t in tables]
            schema_lines = []
            for table in tables:
                cursor.execute(
                    "SELECT column_name, data_type, nullable FROM all_tab_columns WHERE table_name = :tbl AND owner = :own ORDER BY column_id",
                    {"tbl": table, "own": target_schema},
                )
                cols = cursor.fetchall()
                lines = []
                for c in cols:
                    col_name, data_type, is_nullable = c[0], c[1], c[2]
                    ex_str = _get_column_examples_oracle(conn, table, col_name, data_type)
                    null_str = " NOT NULL" if is_nullable == "N" else ""
                    lines.append(f"    {col_name} {data_type}{null_str}{ex_str}")
                schema_lines.append(f'CREATE TABLE "{target_schema}"."{table}" (\n' + ",\n".join(lines) + "\n);")
            conn.close()
            return "\n\n".join(schema_lines)
        except Exception as e:
            return f"-- Oracle Error: {e}"
