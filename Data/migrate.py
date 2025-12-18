import pandas as pd
from sqlalchemy import create_engine, text
import sqlite3
from sqlalchemy.exc import ProgrammingError

# --- 配置 ---
SQLITE_DB_PATH =r'C:\Users\X1 Carbon\Desktop\XunLongLin\Work\Doctor\SJTU\AI+DB\__cybersecurity_threat_monitoring_and_analysis__\__cybersecurity_threat_monitoring_and_analysis__.sqlite'

# MySQL 连接信息
MYSQL_USER = 'root'
MYSQL_PASSWORD = '123456'
MYSQL_HOST = ''
MYSQL_PORT = '3306'
MYSQL_DB = '__cybersecurity_threat_monitoring_and_analysis__'

# PostgreSQL 连接信息
PG_USER = 'postgres'
PG_PASSWORD = '123456'
PG_HOST = ''
PG_PORT = '5433'
PG_DB = '__cybersecurity_threat_monitoring_and_analysis__'

def setup_databases():
    """Ensures the target databases exist, creating them if necessary."""
    # --- MySQL Setup ---
    try:
        mysql_admin_url = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}'
        mysql_admin_engine = create_engine(mysql_admin_url)
        with mysql_admin_engine.connect() as connection:
            connection.execute(text(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        print(f"MySQL database '{MYSQL_DB}' is ready.")
    except Exception as e:
        print(f"Error setting up MySQL database: {e}")
        exit()

    # --- PostgreSQL Setup ---
    try:
        pg_admin_url = f'postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/postgres'
        pg_admin_engine = create_engine(pg_admin_url, isolation_level='AUTOCOMMIT')
        with pg_admin_engine.connect() as connection:
            # Check if db exists
            result = connection.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{PG_DB}'")).fetchone()
            if not result:
                connection.execute(text(f'CREATE DATABASE "{PG_DB}"'))
                print(f"PostgreSQL database '{PG_DB}' created.")
        print(f"PostgreSQL database '{PG_DB}' is ready.")
    except ProgrammingError as e:
        # If database already exists, it might raise an error we can safely ignore.
        if "already exists" in str(e).lower():
             print(f"PostgreSQL database '{PG_DB}' is ready.")
        else:
            print(f"Error setting up PostgreSQL database: {e}")
            exit()
    except Exception as e:
        print(f"Error setting up PostgreSQL database: {e}")
        exit()

# --- 创建数据库引擎 ---
try:
    setup_databases() # 确保数据库存在
    mysql_engine = create_engine(
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'
    )
    pg_engine = create_engine(
        f'postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}'
    )
except ImportError as e:
    print(f"缺少数据库驱动，请安装. Error: {e}")
    print("您可能需要运行: pip install pymysql psycopg2-binary")
    exit()


def drop_databases():
    """
    Deletes the target databases in MySQL and PostgreSQL.
    !!! WARNING: THIS IS A DESTRUCTIVE AND IRREVERSIBLE OPERATION !!!
    """
    print("--- Starting database deletion process ---")
    
    # --- MySQL Deletion ---
    try:
        print(f"Attempting to drop MySQL database '{MYSQL_DB}'...")
        # Connect to the server without specifying a database
        mysql_admin_url = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}'
        mysql_admin_engine = create_engine(mysql_admin_url)
        with mysql_admin_engine.connect() as connection:
            connection.execute(text(f"DROP DATABASE IF EXISTS `{MYSQL_DB}`"))
        print(f"MySQL database '{MYSQL_DB}' dropped successfully (if it existed).")
    except Exception as e:
        print(f"Error dropping MySQL database: {e}")

    # --- PostgreSQL Deletion ---
    try:
        print(f"Attempting to drop PostgreSQL database '{PG_DB}'...")
        # Connect to the default 'postgres' database to perform admin tasks
        pg_admin_url = f'postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/postgres'
        # AUTOCOMMIT is required for commands like DROP DATABASE
        pg_admin_engine = create_engine(pg_admin_url, isolation_level='AUTOCOMMIT')
        with pg_admin_engine.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{PG_DB}"'))
        print(f"PostgreSQL database '{PG_DB}' dropped successfully (if it existed).")
    except Exception as e:
        print(f"Error dropping PostgreSQL database: {e}")
        
    print("--- Database deletion process finished ---")


def migrate_database():
    """
    将 SQLite 数据库中的所有表迁移到 MySQL 和 PostgreSQL。
    此方法主要迁移数据，不会迁移主键、外键、索引等复杂约束。
    """
    sqlite_conn = None  # 提前声明变量
    try:
        # 1. 连接到 SQLite 数据库
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        
        # 2. 获取所有表的列表
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        # 【修正点】从元组列表中提取表名字符串
        table_names = [table[0] for table in tables]
        
        if not table_names:
            print("在 SQLite 数据库中没有找到任何表。")
            return
            
        print(f"找到以下表: {table_names}")

        # 3. 逐个迁移每个表
        for table_name in table_names:
            # 跳过 SQLite 内部的系统表
            if table_name.startswith('sqlite_'):
                print(f"跳过 SQLite 系统表: {table_name}")
                continue

            print(f"正在处理表: {table_name}...")
            
            try:
                # 使用 pandas 从 SQLite 读取整个表到 DataFrame
                df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', sqlite_conn)
                
                # 将 DataFrame 写入 MySQL
                print(f"  -> 正在写入到 MySQL...")
                df.to_sql(table_name, mysql_engine, if_exists='replace', index=False, chunksize=1000)
                
                # 将 DataFrame 写入 PostgreSQL
                print(f"  -> 正在写入到 PostgreSQL...")
                df.to_sql(table_name, pg_engine, if_exists='replace', index=False, chunksize=1000)

                print(f"表 {table_name} 迁移完成。")
            
            except Exception as e:
                print(f"处理表 {table_name} 时发生错误: {e}")
                # 选择继续处理下一张表
                continue

    except sqlite3.Error as e:
        print(f"连接到 SQLite 数据库时发生错误: {e}")
    except Exception as e:
        print(f"迁移过程中发生未知错误: {e}")
    finally:
        if sqlite_conn:
            sqlite_conn.close()
        print("迁移过程结束。")

if __name__ == '__main__':
    # 在运行前，请确保:
    # 1. 已安装所需库: pip install pandas sqlalchemy pymysql psycopg2-binary
    # 2. 脚本会自动创建目标数据库（如果尚不存在）
    migrate_database()