# # qwen3-max config.py
# import os
# import sys
# from openai import OpenAI

# # ===================== 路径常量 =====================
# RESULT_JSON_PATH = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\translator4.0\输出结果\第三次测试结果\nl2rag_multi_db_result.json"
# OUTPUT_DIR = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\translator4.0\输出结果\第三次测试结果"
# RULES_ROOT_DIR = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\rag\knowledge\Rule_based_dialect"
# RAG_MODULE_PATH = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\rag\Model4.0_rag"  # rag_fixed_chunk.py路径

# # ===================== ModelScope配置 =====================
# API_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
# MODEL_NAME = "qwen3-max"
# API_KEY = "sk-a84e13e80bc3459594537184984f32ed"

# # ===================== 数据库配置 =====================
# # 数据库规则文件映射
# DB_TYPE_TO_RULE_FILE = {
#     "MySQL": "MySQL.txt",
#     "PostgreSQL": "PostgreSQL.txt",
#     "SQLite": "SQLite.txt",
#     "Oracle": "Oracle.txt",
#     "SQL Server": "SQL Server.txt"
# }
# SUPPORTED_DBS = list(DB_TYPE_TO_RULE_FILE.keys())

# # 数据库连接配置
# DB_CONNECT_CONFIGS = {
#     "MySQL": {
#         "host": "localhost",
#         "user": "root",
#         "password": "xuhongming3410",
#         "database": "bird",
#         "buffered": True,
#         "autocommit": True,
#         "connection_timeout": 30
#     },
#     "PostgreSQL": {
#         "host": "localhost",
#         "user": "postgres",
#         "password": "postgres",
#         "database": "bird",
#         "port": 5432
#     },
#     "SQLite": {
#         "database": r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\bird.db"
#     }
# }

# # ===================== 执行配置 =====================
# SQL_EXECUTION_TIMEOUT = 30  # SQL执行超时时间（秒）
# MAX_RETRY_COUNT = 1         # 超时重试次数

# # ===================== 输出文件路径 =====================
# JSON_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "rag2SQL_result.json")
# FINAL_REPORT_PATH = os.path.join(OUTPUT_DIR, "final_sql_execution_report.json")
# SEMANTIC_FAIL_LOG_PATH = os.path.join(OUTPUT_DIR, "semantic_validation_failures.json")

# # ===================== 全局初始化 =====================
# # 添加RAG模块路径
# sys.path.append(RAG_MODULE_PATH)

# # 初始化OpenAI客户端
# client = OpenAI(
#     api_key=API_KEY,
#     base_url=API_BASE_URL
# )



##gpt5.2


import os
import sys
from openai import OpenAI

# ===================== 路径常量（无需修改） =====================
RESULT_JSON_PATH = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\translator4.0\输出结果\第三次测试结果\nl2rag_multi_db_result.json"
OUTPUT_DIR = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\translator4.0\输出结果\第三次测试结果"
RULES_ROOT_DIR = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\rag\knowledge\Rule_based_dialect"
RAG_MODULE_PATH = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\rag\Model4.0_rag"  # rag_fixed_chunk.py路径

# ===================== GPT 5.2 配置（核心修改） =====================
# 方式1：从系统环境变量读取（推荐，避免硬编码密钥）

API_KEY = "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"

# OpenAI 官方基础地址（私有部署/企业版需替换为自定义地址）
API_BASE_URL = "https://api.openai.com/v1"
# GPT 5.2 模型名称（以OpenAI官方命名为准，需确认）
MODEL_NAME = "gpt-5.2"

# ===================== 数据库配置（无需修改） =====================
# 数据库规则文件映射
DB_TYPE_TO_RULE_FILE = {
    "MySQL": "MySQL.txt",
    "PostgreSQL": "PostgreSQL.txt",
    "SQLite": "SQLite.txt",
    "Oracle": "Oracle.txt",
    "SQL Server": "SQL Server.txt"
}
SUPPORTED_DBS = list(DB_TYPE_TO_RULE_FILE.keys())

# 数据库连接配置
DB_CONNECT_CONFIGS = {
    "MySQL": {
        "host": "localhost",
        "user": "root",
        "password": "xuhongming3410",
        "database": "bird",
        "buffered": True,
        "autocommit": True,
        "connection_timeout": 30
    },
    "PostgreSQL": {
        "host": "localhost",
        "user": "postgres",
        "password": "postgres",
        "database": "bird",
        "port": 5432
    },
    "SQLite": {
        "database": r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\bird.db"
    }
}

# ===================== 执行配置（无需修改） =====================
SQL_EXECUTION_TIMEOUT = 30  # SQL执行超时时间（秒）
MAX_RETRY_COUNT = 1         # 超时重试次数

# ===================== 输出文件路径（无需修改） =====================
JSON_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "rag2SQL_result.json")
FINAL_REPORT_PATH = os.path.join(OUTPUT_DIR, "final_sql_execution_report.json")
SEMANTIC_FAIL_LOG_PATH = os.path.join(OUTPUT_DIR, "semantic_validation_failures.json")

# ===================== 全局初始化（核心修改） =====================
# 添加RAG模块路径
sys.path.append(RAG_MODULE_PATH)

# 初始化 OpenAI GPT 5.2 客户端
client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE_URL,

)