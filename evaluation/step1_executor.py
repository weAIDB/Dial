# evaluation/step1_executor.py
# Step 1: Execute generated SQL on target engines and save results.
# Supports MySQL, PostgreSQL, SQLite, DuckDB, SQL Server, Oracle via per-engine executors.

import pymysql
import sqlite3
import time
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List
from tqdm import tqdm

try:
    import psycopg2
except ImportError:
    psycopg2 = None
try:
    import duckdb
except ImportError:
    duckdb = None
try:
    import pyodbc
except ImportError:
    pyodbc = None
try:
    import oracledb
except ImportError:
    oracledb = None
try:
    from dbutils.pooled_db import PooledDB
except ImportError:
    PooledDB = None

from config import EXECUTE_ENGINES
from common_utils import logger, save_json, load_json


# -----------------------------------------------------------------------------
# Base executor and per-engine implementations
# -----------------------------------------------------------------------------
class BaseExecutor:
    def __init__(self, db_config):
        self.db_config = db_config
        self.max_rows = 1000
        self.timeout = 60
        self.pool = None

    def _init_pool(self):
        pass

    def get_connection(self, db_id: str):
        raise NotImplementedError

    def release_connection(self, connection):
        if connection:
            connection.close()

    def execute_sql(self, sql: str, db_id: str) -> Dict[str, Any]:
        connection = None
        cursor = None
        timer = None
        try:
            connection = self.get_connection(db_id)
            cursor = connection.cursor()

            if isinstance(connection, (sqlite3.Connection, duckdb.DuckDBPyConnection)):
                def interrupt_db():
                    if connection:
                        try:
                            connection.interrupt()
                        except Exception:
                            pass

                timer = threading.Timer(self.timeout, interrupt_db)
                timer.start()

            start_time = time.time()
            cursor.execute(sql)
            sql_upper = sql.strip().upper()
            is_select = sql_upper.startswith(("SELECT", "SHOW", "DESCRIBE", "DESC", "WITH", "PRAGMA"))

            if is_select:
                results = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description] if cursor.description else []
                execution_time = time.time() - start_time
                processed_data = []
                truncated = False
                for i, row in enumerate(results):
                    if i >= self.max_rows:
                        truncated = True
                        break
                    processed_data.append(list(row))
                return {
                    "success": True,
                    "columns": column_names,
                    "data": processed_data,
                    "execution_time": round(execution_time, 3),
                    "row_count": len(processed_data),
                    "truncated": truncated,
                }
            else:
                if hasattr(connection, "commit"):
                    connection.commit()
                return {
                    "success": True,
                    "columns": ["affected_rows"],
                    "data": [[cursor.rowcount if hasattr(cursor, "rowcount") else 0]],
                    "execution_time": round(time.time() - start_time, 3),
                    "row_count": 1,
                }
        except Exception as e:
            return {"success": False, "error": f"Execute Error: {str(e)}", "execution_time": 0}
        finally:
            if timer:
                timer.cancel()
            if cursor:
                cursor.close()
            if connection:
                self.release_connection(connection)

    def close(self):
        if self.pool and hasattr(self.pool, "close"):
            self.pool.close()


class MySQLExecutor(BaseExecutor):
    def _init_pool(self):
        if PooledDB:
            self.pool = PooledDB(
                creator=pymysql,
                maxconnections=20,
                mincached=5,
                blocking=True,
                **self.db_config,
                charset="utf8mb4",
                autocommit=True,
                read_timeout=self.timeout,
            )

    def get_connection(self, db_id: str):
        if self.pool:
            conn = self.pool.connection()
            try:
                conn.connection().select_db(db_id)
            except Exception:
                cur = conn.cursor()
                cur.execute(f"USE `{db_id}`")
                cur.close()
            return conn
        config = self.db_config.copy()
        config["database"] = db_id
        config["autocommit"] = True
        return pymysql.connect(**config)


class PostgreSQLExecutor(BaseExecutor):
    def get_connection(self, db_id: str):
        config = self.db_config.copy()
        config["dbname"] = db_id
        config["options"] = f"-c statement_timeout={self.timeout * 1000}"
        return psycopg2.connect(**config)


class SQLiteExecutor(BaseExecutor):
    def __init__(self, sqlite_dir):
        super().__init__({})
        self.sqlite_dir = sqlite_dir

    def get_connection(self, db_id: str):
        db_path = os.path.join(self.sqlite_dir, db_id, f"{db_id}.sqlite")
        if not os.path.exists(db_path):
            db_path = os.path.join(self.sqlite_dir, f"{db_id}.sqlite")
        return sqlite3.connect(db_path, timeout=self.timeout, check_same_thread=False)


class DuckDBExecutor(BaseExecutor):
    def __init__(self, duckdb_dir):
        super().__init__({})
        self.duckdb_dir = duckdb_dir

    def get_connection(self, db_id: str):
        db_path = os.path.join(self.duckdb_dir, f"{db_id}.duckdb")
        return duckdb.connect(database=db_path, read_only=True)


class SQLServerExecutor(BaseExecutor):
    def get_connection(self, db_id: str):
        cfg = self.db_config
        conn_str = (
            f"DRIVER={cfg['driver']};SERVER={cfg['host']},{cfg['port']};"
            f"DATABASE={db_id};UID={cfg['user']};PWD={cfg['password']};"
            f"LoginTimeout={self.timeout};"
        )
        conn = pyodbc.connect(conn_str)
        conn.timeout = self.timeout
        return conn


class OracleExecutor(BaseExecutor):
    def _init_pool(self):
        if oracledb:
            cfg = self.db_config
            dsn = cfg.get("dsn") or f"{cfg.get('host', 'localhost')}:{cfg.get('port', 1521)}/{cfg.get('service_name', 'ORCL')}"
            self.pool = oracledb.create_pool(
                user=cfg["user"],
                password=cfg["password"],
                dsn=dsn,
                min=2,
                max=20,
                increment=1,
            )

    def get_connection(self, db_id: str):
        if not self.pool:
            self._init_pool()
        return self.pool.acquire()

    def release_connection(self, connection):
        if self.pool:
            self.pool.release(connection)
        else:
            connection.close()

    def execute_sql(self, sql: str, db_id: str) -> Dict[str, Any]:
        connection = None
        cursor = None
        try:
            connection = self.get_connection(db_id)
            cursor = connection.cursor()
            sql = sql.strip().rstrip(";")
            target_schema = f"U_{db_id.upper()}" if db_id and db_id[0].isdigit() else db_id.upper()
            try:
                cursor.execute(f'ALTER SESSION SET CURRENT_SCHEMA = "{target_schema}"')
            except Exception:
                pass
            start_time = time.time()
            cursor.execute(sql)
            is_select = sql.strip().upper().startswith(("SELECT", "WITH", "DESC"))
            if is_select:
                results = cursor.fetchmany(self.max_rows + 1)
                column_names = [desc[0] for desc in cursor.description] if cursor.description else []
                data = []
                for row in results[: self.max_rows]:
                    clean_row = []
                    for item in row:
                        if hasattr(item, "__str__") and "oracledb" in str(type(item)):
                            clean_row.append(str(item))
                        else:
                            clean_row.append(item)
                    data.append(clean_row)
                return {
                    "success": True,
                    "columns": column_names,
                    "data": data,
                    "execution_time": round(time.time() - start_time, 3),
                    "row_count": len(data),
                    "truncated": len(results) > self.max_rows,
                }
            else:
                connection.commit()
                return {
                    "success": True,
                    "columns": ["affected_rows"],
                    "data": [[cursor.rowcount]],
                    "execution_time": round(time.time() - start_time, 3),
                    "row_count": 1,
                }
        except Exception as e:
            return {"success": False, "error": f"Oracle Error: {str(e)}", "execution_time": 0}
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.release_connection(connection)


# -----------------------------------------------------------------------------
# Executor factory and worker
# -----------------------------------------------------------------------------
def get_executor(engine_type: str, db_config_all: dict):
    executor_map = {
        "mysql": lambda: MySQLExecutor(db_config_all["mysql"]),
        "postgres": lambda: PostgreSQLExecutor(db_config_all["postgres"]),
        "sqlite": lambda: SQLiteExecutor(db_config_all["sqlite_dir"]),
        "duckdb": lambda: DuckDBExecutor(db_config_all["duckdb_dir"]),
        "sqlserver": lambda: SQLServerExecutor(db_config_all["sqlserver"]),
        "oracle": lambda: OracleExecutor(db_config_all["oracle"]),
    }
    if engine_type not in executor_map:
        raise ValueError(f"Unknown engine: {engine_type}")
    exc = executor_map[engine_type]()
    exc._init_pool()
    return exc


def worker(item, index, executor, engine):
    try:
        item_core = item
        question_id = item_core.get("question_id", f"index_{index}")
        db_id = item_core.get("db_id", "bird")
        gen_obj = item_core.get("sql_generation", {})
        generated_sql = gen_obj.get(engine)
        gold_obj = item_core.get("gold_sql", {})
        gold_sql = gold_obj.get(engine)
        output_item = {
            "question_id": question_id,
            "db_id": db_id,
            "engine": engine,
            "gold_sql": gold_sql,
            "generated_sql": generated_sql,
            "result": {"status": "skipped"},
        }
        if generated_sql and isinstance(generated_sql, str) and generated_sql.strip():
            res = executor.execute_sql(generated_sql, db_id)
            if res["success"]:
                output_item["result"] = {
                    "status": "success",
                    "columns": res["columns"],
                    "data": res["data"],
                    "execution_time": res["execution_time"],
                    "row_count": res["row_count"],
                }
            else:
                output_item["result"] = {"status": "error", "error": res["error"]}
        return output_item
    except Exception as e:
        return {"question_id": f"err_{index}", "engine": engine, "result": {"status": "error", "error": str(e)}}


def run_execution(
    input_file: str,
    output_file: str,
    db_config_all: dict,
    target_engine: str = None,
    max_workers: int = 10,
) -> bool:
    logger.info("[Step 1] Parallel SQL execution | Engine: %s | Workers: %s", target_engine, max_workers)
    data = load_json(input_file)
    if not data:
        return False
    engines_to_run = [target_engine] if target_engine else EXECUTE_ENGINES
    final_output = []
    for engine in engines_to_run:
        try:
            executor = get_executor(engine, db_config_all)
            engine_results = []
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = [pool.submit(worker, item, i, executor, engine) for i, item in enumerate(data)]
                for f in tqdm(as_completed(futures), total=len(futures), desc=f"Exec {engine}"):
                    engine_results.append(f.result())
            final_output.extend(engine_results)
            executor.close()
        except Exception as e:
            logger.error("Engine %s failed: %s", engine, e)
    save_json(final_output, output_file)
    return True
