# db_operations.py
import threading
import mysql.connector
from mysql.connector import Error as MySQLError
import psycopg2
from psycopg2 import OperationalError as PgOperationalError
import sqlite3
from sqlite3 import Error as SQLiteError
from config import DB_CONNECT_CONFIGS, SQL_EXECUTION_TIMEOUT

def get_db_connection(db_type):
    """创建数据库连接"""
    if db_type not in DB_CONNECT_CONFIGS:
        raise ValueError(f"不支持的数据库类型：{db_type}")
    
    config = DB_CONNECT_CONFIGS[db_type]
    connection = None
    
    try:
        if db_type == "MySQL":
            connection = mysql.connector.connect(**config)
        elif db_type == "PostgreSQL":
            connection = psycopg2.connect(**config)
        elif db_type == "SQLite":
            connection = sqlite3.connect(config["database"], timeout=30)
        
        if connection:
            print(f"✅ {db_type} 连接成功")
        return connection
    except Exception as e:
        print(f"❌ {db_type} 连接失败：{str(e)[:200]}")
        return None

def reconnect_db(db_type):
    """数据库重连"""
    print(f"⚠️ {db_type} 连接失效，尝试重连...")
    return get_db_connection(db_type)

def _execute_sql_without_timeout(sql, db_type, connection, cursor):
    """无超时执行SQL（供线程调用）"""
    try:
        if db_type == "PostgreSQL":
            cursor.execute(sql)
            if cursor.description:
                cursor.fetchall()
        elif db_type == "SQLite":
            cursor.execute(sql)
            connection.commit()
        else:  # MySQL
            cursor.execute(sql)
            if cursor.with_rows:
                cursor.fetchall()
        return {"status": "success", "error": None}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def test_sql_execution(sql, db_type, connection):
    """测试SQL执行（支持超时检测，用于处理死循环）"""
    cursor = None
    execution_result = {"status": "failed", "error": "未知错误"}
    
    try:
        # 检查连接有效性
        if not connection:
            connection = reconnect_db(db_type)
            if not connection:
                return {"status": "failed", "error": f"{db_type} 连接不可用"}
        
        # 不同数据库的连接检查
        if db_type == "MySQL" and not connection.is_connected():
            connection = reconnect_db(db_type)
        elif db_type == "PostgreSQL" and connection.closed:
            connection = reconnect_db(db_type)
        
        if not connection:
            return {"status": "failed", "error": f"{db_type} 重连失败"}
        
        # 创建游标
        cursor = connection.cursor()
        
        # 使用线程执行SQL，设置超时
        result = None
        thread = None
        
        def worker():
            nonlocal result
            result = _execute_sql_without_timeout(sql, db_type, connection, cursor)
        
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
        
        # 等待线程完成，超时则判定为死循环
        thread.join(timeout=SQL_EXECUTION_TIMEOUT)
        
        if thread.is_alive():
            # SQL执行超时，判定为死循环或查询过于复杂
            execution_result = {
                "status": "failed", 
                "error": f"SQL执行超时（超过{SQL_EXECUTION_TIMEOUT}秒），可能陷入死循环或查询过于复杂。请优化SQL，避免无限递归、笛卡尔积过大的关联查询、未加限制条件的大范围扫描等情况。"
            }
            print(f"⚠️ SQL执行超时，已终止执行")
            
            # 强制关闭游标和重置连接（避免资源泄漏）
            try:
                if db_type == "MySQL":
                    connection.reset_session()
                elif db_type == "PostgreSQL":
                    connection.rollback()
                elif db_type == "SQLite":
                    connection.rollback()
            except:
                pass
        else:
            # 线程正常结束，获取执行结果
            execution_result = result if result else {"status": "failed", "error": "执行结果未知"}
        
        return execution_result
    
    except MySQLError as e:
        err_msg = f"MySQL错误：{str(e)}"
        execution_result = {"status": "failed", "error": err_msg}
    except PgOperationalError as e:
        err_msg = f"PostgreSQL错误：{str(e)}"
        execution_result = {"status": "failed", "error": err_msg}
    except SQLiteError as e:
        err_msg = f"SQLite错误：{str(e)}"
        execution_result = {"status": "failed", "error": err_msg}
    except Exception as e:
        err_msg = f"未知错误：{str(e)}"
        execution_result = {"status": "failed", "error": err_msg}
    
    finally:
        # 确保游标关闭
        if cursor:
            try:
                cursor.close()
            except:
                pass
    
    # 截断过长错误信息
    if len(execution_result["error"]) > 500:
        execution_result["error"] = execution_result["error"][:500] + "..."
    
    return execution_result