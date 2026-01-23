# config.py
import os
import sys
from openai import OpenAI

# ===================== 路径常量 =====================
# 请根据实际情况调整这些根目录
BASE_DATA_DIR = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\正在测试数据集\2206条数据\全量数据"

RESULT_JSON_PATH = os.path.join(BASE_DATA_DIR, r"result\nl2rag_multi_db_result copy.json")
OUTPUT_DIR = os.path.join(BASE_DATA_DIR, "result")
RULES_ROOT_DIR = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\rag\knowledge\Rule_based_dialect"
RAG_MODULE_PATH = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\rag\Model4.0_rag"
FUNCTIONAL_ROOT_DIR = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\rag\knowledge\Functional_dialect"

# ===================== ModelScope/OpenAI 配置 =====================
API_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen3-max"
API_KEY = "sk-a84e13e80bc3459594537184984f32ed"

# ===================== 数据库配置 (核心修改) =====================
# 统一变量名为 DB_CONFIG，并补全缺失的数据库类型
DB_CONFIG = {
    'mysql': {
        'host': "192.168.10.100",
        'user': "root",
        'password': "123456",
        'port': 3306,
        'buffered': True,
        'autocommit': True,
        'connection_timeout': 30
    },
    'postgres': {
        'host': "192.168.10.100",
        'user': "postgres",
        'password': "123456",
        'port': 5433,  # 注意你原配置是 5433
    },
    'sqlserver': {
        'driver': '{ODBC Driver 17 for SQL Server}',  # 需确保本地安装了此驱动
        'host': '192.168.10.100',  # 假设也在同一台服务器，如在本地则写 localhost
        'user': 'sa',
        'password': 'YourPassword',  # 请替换为实际密码
        'port': 1433,
    },
    'oracle': {
        'user': 'system',  # 对应截图中的用户名
        'password': 'Dialectsql123',  # 请确保密码与 Navicat 中保存的一致
        # 格式: IP地址:端口/服务名称
        # 修改点: localhost -> 192.168.10.110
        'dsn': '192.168.10.110:1521/ORCLPDB',
    },
    # SQLite 数据库存放的根目录
    # db_operations 会寻找: sqlite_dir/db_id/db_id.sqlite
    'sqlite_dir': r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\data\sqlite_databases",

    # DuckDB 数据库存放的根目录
    # db_operations 会寻找: duckdb_dir/db_id.duckdb
    'duckdb_dir': r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\data\duckdb_databases"
}

# 数据库规则文件映射
DB_TYPE_TO_RULE_FILE = {
    "MySQL": "MySQL.txt",
    "PostgreSQL": "PostgreSQL.txt",
    "SQLite": "SQLite.txt",
    "Oracle": "Oracle.txt",
    "SQL Server": "SQL Server.txt"
}
SUPPORTED_DBS = list(DB_TYPE_TO_RULE_FILE.keys())

# ===================== 执行配置 =====================
SQL_EXECUTION_TIMEOUT = 30  # SQL执行超时时间（秒）
MAX_RETRY_COUNT = 1  # 超时重试次数

# ===================== 输出文件路径 =====================
JSON_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "rag2SQL_result.json")
FINAL_REPORT_PATH = os.path.join(OUTPUT_DIR, "final_sql_execution_report.json")
SEMANTIC_FAIL_LOG_PATH = os.path.join(OUTPUT_DIR, "semantic_validation_failures.json")

# ===================== 全局初始化 =====================
sys.path.append(RAG_MODULE_PATH)

client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE_URL
)

MAGIC_SIMILARITY_THRESHOLD = 0.75