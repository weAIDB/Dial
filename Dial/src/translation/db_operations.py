# db_operations.py
# -*- coding: utf-8 -*-

import threading
import os
import sys
import time

# ================= Database Driver Imports =================
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    mysql = None

try:
    import psycopg2
    from psycopg2 import OperationalError as PgOperationalError
except ImportError:
    psycopg2 = None

import sqlite3
from sqlite3 import Error as SQLiteError

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

# ================= Configuration Imports =================
try:
    from .config import DB_CONFIG, SQL_EXECUTION_TIMEOUT
except ImportError:
    # Default fallback configuration (if config.py is missing)
    SQL_EXECUTION_TIMEOUT = 30
    DB_CONFIG = {
        'sqlserver': {
            'driver': '{ODBC Driver 17 for SQL Server}',
            'host': '192.168.103.2',
            'user': 'sa',
            'password': 'Dialectsql123',
            'port': 1433,
        }
    }

def get_db_connection(db_type, specific_db_name=None):
    """
    Create a database connection
    :param db_type: Database type (mysql, postgres, sqlite, sqlserver, oracle, duckdb)
    :param specific_db_name: Specific database name (corresponds to db_id in JSON)
    """
    engine_key = db_type.lower()
    
    # Simple alias mapping
    if 'postgres' in engine_key: engine_key = 'postgres'
    elif 'sql' in engine_key and 'server' in engine_key: engine_key = 'sqlserver'
    elif 'oracle' in engine_key: engine_key = 'oracle'
    elif 'duck' in engine_key: engine_key = 'duckdb'
    elif 'sqlite' in engine_key: engine_key = 'sqlite'
    elif 'mysql' in engine_key: engine_key = 'mysql'

    connection = None

    try:
        # ================= MySQL =================
        if engine_key == 'mysql':
            if not mysql: raise ImportError("Missing mysql-connector-python")
            config = DB_CONFIG['mysql'].copy()
            if specific_db_name:
                config["database"] = specific_db_name
            connection = mysql.connector.connect(**config)

        # ================= PostgreSQL =================
        elif engine_key == 'postgres':
            if not psycopg2: raise ImportError("Missing psycopg2")
            config = DB_CONFIG['postgres'].copy()
            if specific_db_name:
                config["dbname"] = specific_db_name
            connection = psycopg2.connect(**config)

        # ================= SQLite =================
        elif engine_key == 'sqlite':
            if not specific_db_name:
                raise ValueError("SQLite connect requires specific_db_name (db_id)")
            
            base_dir = DB_CONFIG.get('sqlite_dir', './')
            db_path = os.path.join(base_dir, specific_db_name, f"{specific_db_name}.sqlite")

            if not os.path.exists(db_path):
                # Try finding the filename directly without subdirectories (compatible with different dataset structures)
                db_path_flat = os.path.join(base_dir, f"{specific_db_name}.sqlite")
                if os.path.exists(db_path_flat):
                    db_path = db_path_flat
                else:
                    print(f"❌ SQLite file not found: {db_path}")
                    return None

            connection = sqlite3.connect(db_path, check_same_thread=False)

        # ================= SQL Server (Fixed) =================
        elif engine_key == 'sqlserver':
            if not pyodbc:
                raise ImportError("Please install pyodbc: pip install pyodbc")

            config = DB_CONFIG['sqlserver']
            driver = config.get('driver', '{ODBC Driver 17 for SQL Server}')
            host = config['host']
            port = config.get('port', 1433)
            user = config['user']
            pwd = config['password']

            # Build connection string
            # Note: TrustServerCertificate=yes is used to bypass self-signed certificate verification
            conn_str = (
                f"DRIVER={driver};"
                f"SERVER={host},{port};"
                f"UID={user};"
                f"PWD={pwd};"
                f"TrustServerCertificate=yes;" 
            )
            
            if specific_db_name:
                conn_str += f"DATABASE={specific_db_name};"

            connection = pyodbc.connect(conn_str)

        # ================= Oracle =================
        elif engine_key == 'oracle':
            if not oracledb: raise ImportError("Missing oracledb")
            config = DB_CONFIG['oracle']
            dsn = config.get('dsn')
            if not dsn and 'host' in config:
                dsn = f"{config['host']}:{config.get('port', 1521)}/{config.get('service_name', 'ORCL')}"
            
            connection = oracledb.connect(
                user=config['user'],
                password=config['password'],
                dsn=dsn
            )

        # ================= DuckDB =================
        elif engine_key == 'duckdb':
            if not duckdb: raise ImportError("Missing duckdb")
            if not specific_db_name: raise ValueError("DuckDB requires db_id")
            
            base_dir = DB_CONFIG.get('duckdb_dir', './')
            db_path = os.path.join(base_dir, f"{specific_db_name}.duckdb")
            
            connection = duckdb.connect(db_path, read_only=True)

        else:
            raise ValueError(f"Unknown db_type: {db_type}")

        return connection

    except Exception as e:
        print(f"❌ Connection Error ({db_type} - {specific_db_name}): {str(e)[:200]}")
        return None


def _execute_sql_without_timeout(sql, db_type, connection, cursor):
    """
    Logic for actual SQL execution (called by thread).
    Handle fetch differences for various databases here, resolving 'with_rows' errors.
    """
    engine_key = db_type.lower()
    result_set = []

    try:
        # --- DuckDB Special Handling ---
        if 'duckdb' in engine_key:
            # DuckDB can use connection or cursor
            if cursor:
                cursor.execute(sql)
                result_set = cursor.fetchall()
            else:
                result_set = connection.execute(sql).fetchall()
            return {"status": "success", "error": None, "result": result_set}

        # --- Standard DBAPI Execution ---
        if not cursor:
            return {"status": "failed", "error": "Cursor is None"}

        cursor.execute(sql)

        # --- Result Retrieval Logic (Core Fix Point) ---
        
        # 1. SQL Server (pyodbc)
        if 'sql' in engine_key and 'server' in engine_key:
            # pyodbc does not support .with_rows, must use .description to check for result set
            if cursor.description:
                rows = cursor.fetchall()
                # pyodbc returns pyodbc.Row objects, recommended to convert to tuple for serialization
                result_set = [tuple(row) for row in rows]
            else:
                # If not a query statement (like UPDATE/INSERT), commit is needed
                connection.commit()

        # 2. Oracle / PostgreSQL / SQLite
        elif any(k in engine_key for k in ['oracle', 'postgres', 'sqlite']):
            if cursor.description:
                result_set = cursor.fetchall()
            else:
                # Some databases require explicit commit
                if 'sqlite' in engine_key or 'postgres' in engine_key:
                    connection.commit()

        # 3. MySQL
        elif 'mysql' in engine_key:
            # MySQL Connector sometimes needs .with_rows property to judge
            # But can fallback to description
            if getattr(cursor, 'with_rows', False) or cursor.description:
                result_set = cursor.fetchall()
            else:
                connection.commit()
        
        # 4. Other unknown databases
        else:
            if cursor.description:
                result_set = cursor.fetchall()
            else:
                connection.commit()

        return {"status": "success", "error": None, "result": result_set}

    except Exception as e:
        return {"status": "failed", "error": str(e)}


def test_sql_execution(sql, db_type, connection):
    """
    SQL Executor with timeout control
    """
    # Initialize return structure
    execution_result = {"status": "failed", "error": "Unknown Error"}
    cursor = None
    engine_key = db_type.lower()

    if not connection:
        return {"status": "failed", "error": "Connection is None"}

    try:
        # Get cursor
        try:
            cursor = connection.cursor()
        except AttributeError:
            # DuckDB connection can be used directly as a cursor
            if 'duckdb' in engine_key:
                cursor = connection
            else:
                raise

        # Define thread container to receive results
        container = {"result": None}

        def worker():
            container['result'] = _execute_sql_without_timeout(sql, db_type, connection, cursor)

        # Start daemon thread
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()

        # Wait for result or timeout
        thread.join(timeout=SQL_EXECUTION_TIMEOUT)

        if thread.is_alive():
            # === Timeout Handling ===
            execution_result = {
                "status": "timeout",
                "error": f"SQL execution timed out (> {SQL_EXECUTION_TIMEOUT}s)"
            }
            print(f"⚠️ Timeout: {sql[:40]}...")

            # Force close connection to stop database-side query
            try:
                if 'duckdb' in engine_key:
                    connection.interrupt()
                else:
                    # For PyODBC (SQL Server) and Psycopg2, closing the connection is the most effective way to stop the query
                    connection.close()
            except Exception:
                pass
        else:
            # === Normal Return ===
            if container['result']:
                execution_result = container['result']
            else:
                execution_result = {"status": "failed", "error": "Thread did not return result"}

    except Exception as e:
        execution_result = {"status": "failed", "error": str(e)}
        
    finally:
        # Cleanup cursor (if connection wasn't closed)
        if cursor:
            try:
                # DuckDB cursor close behavior is inconsistent, wrap in try-catch
                if hasattr(cursor, 'close'):
                    cursor.close()
            except:
                pass

    # Truncate error log to prevent excessive length
    if execution_result.get("error"):
        execution_result["error"] = str(execution_result["error"])[:500]

    return execution_result