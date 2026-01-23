# db_operations.py
# -*- coding: utf-8 -*-

import threading
import os
import sys

# 数据库驱动导入
import mysql.connector
from mysql.connector import Error as MySQLError

import psycopg2
from psycopg2 import OperationalError as PgOperationalError

import sqlite3
from sqlite3 import Error as SQLiteError

# 新增驱动支持
try:
    import pyodbc
except ImportError:
    pyodbc = None

try:
    import oracledb
except ImportError:
    oracledb = None

try:
    import duckdb
except ImportError:
    duckdb = None

# 导入配置
# 假设 SQL_EXECUTION_TIMEOUT 定义在 config.py 中，如果没有则使用默认值
try:
    from config import DB_CONFIG, SQL_EXECUTION_TIMEOUT
except ImportError:
    from config import DB_CONFIG

    SQL_EXECUTION_TIMEOUT = 30  # 默认超时时间


def get_db_connection(db_type, specific_db_name=None):
    """
    创建数据库连接
    :param db_type: 数据库类型 (mysql, postgres, sqlite, sqlserver, oracle, duckdb) - 不区分大小写
    :param specific_db_name: 具体的数据库名 (对应 JSON 中的 db_id)
    """
    # 统一转换为小写以匹配 config.py 的键
    engine_key = db_type.lower()

    # 映射 db_type 到 config key (处理一些命名差异)
    if 'postgres' in engine_key:
        engine_key = 'postgres'
    elif 'sql' in engine_key and 'server' in engine_key:
        engine_key = 'sqlserver'
    elif 'oracle' in engine_key:
        engine_key = 'oracle'
    elif 'duck' in engine_key:
        engine_key = 'duckdb'
    elif 'sqlite' in engine_key:
        engine_key = 'sqlite'
    elif 'mysql' in engine_key:
        engine_key = 'mysql'

    connection = None

    try:
        # ================= MySQL =================
        if engine_key == 'mysql':
            config = DB_CONFIG['mysql'].copy()
            if specific_db_name:
                config["database"] = specific_db_name
            else:
                print(f"⚠️ Warning: MySQL need db_id to connect.")
            connection = mysql.connector.connect(**config)

        # ================= PostgreSQL =================
        elif engine_key == 'postgres':
            config = DB_CONFIG['postgres'].copy()
            if specific_db_name:
                config["dbname"] = specific_db_name
            connection = psycopg2.connect(**config)

        # ================= SQLite =================
        elif engine_key == 'sqlite':
            if not specific_db_name:
                raise ValueError("SQLite connect requires specific_db_name (db_id)")

            # 路径逻辑: sqlite_dir/db_id/db_id.sqlite (BIRD 数据集标准结构)
            base_dir = DB_CONFIG.get('sqlite_dir', './')
            db_path = os.path.join(base_dir, specific_db_name, f"{specific_db_name}.sqlite")

            if not os.path.exists(db_path):
                print(f"❌ SQLite file not found: {os.path.abspath(db_path)}")
                return None

            # check_same_thread=False 允许在不同线程(超时控制线程)中使用连接
            connection = sqlite3.connect(db_path, check_same_thread=False)

        # ================= SQL Server =================
        elif engine_key == 'sqlserver':
            if not pyodbc:
                raise ImportError("Please install pyodbc for SQL Server support.")

            config = DB_CONFIG['sqlserver']
            # 构建连接字符串
            # Driver 需与本机安装一致，config 中已定义
            driver = config.get('driver', '{ODBC Driver 17 for SQL Server}')
            host = config['host']
            port = config['port']
            user = config['user']
            pwd = config['password']

            # SQL Server 连接默认进入 master，如果需要切库，可以在连接串指定或后续 USE
            # 注意: 如果数据库名包含特殊字符，可能需要转义
            conn_str = f"DRIVER={driver};SERVER={host},{port};UID={user};PWD={pwd}"
            if specific_db_name:
                conn_str += f";DATABASE={specific_db_name}"

            connection = pyodbc.connect(conn_str)

        # ================= Oracle =================
        elif engine_key == 'oracle':
            if not oracledb:
                raise ImportError("Please install oracledb for Oracle support.")

            config = DB_CONFIG['oracle']
            # 使用 Thin 模式连接 (不需要安装 Instant Client)
            # 这里的 dsn 可以是 "host:port/service_name" 格式
            dsn = config.get('dsn')
            if not dsn and 'host' in config:
                dsn = f"{config['host']}:{config.get('port', 1521)}/{config.get('service_name', 'ORCL')}"

            connection = oracledb.connect(
                user=config['user'],
                password=config['password'],
                dsn=dsn
            )
            # Oracle 没有直接"切换数据库"的概念(对应 Schema/Service)，通常连接后直接查询
            # 如果 specific_db_name 是 schema，可能需要 ALTER SESSION SET CURRENT_SCHEMA

        # ================= DuckDB =================
        elif engine_key == 'duckdb':
            if not duckdb:
                raise ImportError("Please install duckdb for DuckDB support.")

            if not specific_db_name:
                raise ValueError("DuckDB connect requires specific_db_name (db_id)")

            # 路径逻辑: duckdb_dir/db_id.duckdb
            base_dir = DB_CONFIG.get('duckdb_dir', './')
            db_path = os.path.join(base_dir, f"{specific_db_name}.duckdb")

            if not os.path.exists(db_path):
                print(f"❌ DuckDB file not found: {os.path.abspath(db_path)}")
                return None

            # DuckDB 连接
            connection = duckdb.connect(db_path, read_only=True)

        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")

        return connection

    except MySQLError as e:
        if e.errno == 1049:
            print(f"❌ MySQL DB '{specific_db_name}' not found.")
        else:
            print(f"❌ MySQL Connection Error: {str(e)[:200]}")
    except PgOperationalError as e:
        print(f"❌ PostgreSQL Connection Error: {str(e)[:200]}")
    except SQLiteError as e:
        print(f"❌ SQLite Connection Error: {str(e)[:200]}")
    except Exception as e:
        print(f"❌ {db_type} Connection Error: {str(e)[:200]}")

    return None


def _execute_sql_without_timeout(sql, db_type, connection, cursor):
    """
    无超时限制地执行SQL，供内部线程调用
    """
    engine_key = db_type.lower()
    result_set = []

    try:
        # ================= DuckDB (特殊处理) =================
        if 'duckdb' in engine_key:
            # DuckDB 的 cursor 行为略有不同，可以直接 execute 并 fetchall
            # 如果 connection 是 duckdb 的 connection 对象
            if cursor:
                cursor.execute(sql)
                result_set = cursor.fetchall()
            else:
                result_set = connection.execute(sql).fetchall()
            return {"status": "success", "error": None, "result": result_set}

        # ================= 其他 DB (标准 DBAPI 2.0) =================
        if not cursor:
            return {"status": "failed", "error": "Cursor is None"}

        cursor.execute(sql)

        # 处理结果获取
        # 对于 SELECT 语句或有返回结果的语句
        if 'oracle' in engine_key:
            # Oracle 游标通常可以直接迭代，或 fetchall
            if cursor.description:
                result_set = cursor.fetchall()

        elif 'sqlserver' in engine_key:
            if cursor.description:
                result_set = cursor.fetchall()

        elif 'sqlite' in engine_key:
            if cursor.description:
                result_set = cursor.fetchall()
            connection.commit()  # SQLite 有时需要 commit 即使是 Select 后的事务清理

        elif 'postgres' in engine_key:
            if cursor.description:
                result_set = cursor.fetchall()
            connection.commit()  # 防止处于 "idle in transaction"

        else:  # MySQL
            # MySQL Connector 有些版本需要先 fetchall 才能读 rowcount
            if cursor.with_rows:
                result_set = cursor.fetchall()

        return {"status": "success", "error": None, "result": result_set}

    except Exception as e:
        return {"status": "failed", "error": str(e)}


def test_sql_execution(sql, db_type, connection):
    """
    执行 SQL 并带有超时控制
    """
    execution_result = {"status": "failed", "error": "未知错误"}
    cursor = None
    engine_key = db_type.lower()

    try:
        if not connection:
            return {"status": "failed", "error": f"{db_type} Connection is None"}

        # 创建游标
        # DuckDB 可以直接用 connection 当游标用，或者 .cursor()
        if 'duckdb' in engine_key:
            cursor = connection.cursor()
        else:
            cursor = connection.cursor()

        # 定义工作线程
        worker_result = None

        def worker():
            nonlocal worker_result
            worker_result = _execute_sql_without_timeout(sql, db_type, connection, cursor)

        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()

        # 等待结果
        thread.join(timeout=SQL_EXECUTION_TIMEOUT)

        if thread.is_alive():
            # 超时处理
            execution_result = {
                "status": "timeout",
                "error": f"SQL execution timed out (> {SQL_EXECUTION_TIMEOUT}s)."
            }
            print(f"⚠️ SQL Execution Timeout: {sql[:50]}...")

            # 尝试中断连接以停止远端查询
            try:
                if 'duckdb' in engine_key:
                    connection.interrupt()
                else:
                    # 对于其他数据库，强制关闭连接是停止查询的最快方法
                    # 注意：这会导致传入的 connection 对象失效，调用者需要处理重连
                    connection.close()
            except:
                pass
        else:
            # 正常返回
            if worker_result:
                execution_result = worker_result
            else:
                execution_result = {"status": "failed", "error": "Worker thread returned no result"}

    except Exception as e:
        execution_result = {"status": "failed", "error": str(e)}

    finally:
        # 关闭游标
        if cursor:
            try:
                cursor.close()
            except:
                pass

    # 错误信息截断
    if execution_result.get("error") and len(str(execution_result["error"])) > 1000:
        execution_result["error"] = str(execution_result["error"])[:1000] + "..."

    return execution_result