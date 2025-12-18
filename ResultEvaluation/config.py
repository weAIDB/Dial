# config.py
import os

# 数据库配置
DB_CONFIG = {
    'mysql': {
        'host': '192.168.10.100',
        'user': 'root',
        'password': '123456',
        'port': 3306,
    },
    'postgres': {
        'host': '192.168.10.100',
        'user': 'postgres',
        'password': '123456',
        'port': 5433,
    },
    # SQLite 数据库存放的根目录 (在该目录下应有 folder_db_id/db_id.sqlite)
    'sqlite_dir': '../data/full_data/database-sqlite/'
}

# 选择要执行的引擎列表：['mysql', 'postgres', 'sqlite'] 中的一个或多个
# 注意：通常一次只跑一种方言，如果列表有多个，逻辑会依次执行覆盖结果
EXECUTE_ENGINES = ['mysql', 'postgres','sqlite']

# 路径配置 (保持不变)
PIPELINE_TASKS = [
    {
        'name': '测试1',
        'input_sql': '../baseline/LLM_only/deepseekV3.2/分开生成sql语句/sql_all_deepseekV3.2.json',
        'output_exec': '../baseline/LLM_only/deepseekV3.2/分开生成sql语句/test.json',
    },
]
GOLD_RESULT_FILE = 'true_result_all_no_empty.json'

FINAL_EXCEL_PATH = 'result/result.xlsx'

for task in PIPELINE_TASKS:
    os.makedirs(os.path.dirname(task['output_exec']), exist_ok=True)
os.makedirs(os.path.dirname(FINAL_EXCEL_PATH), exist_ok=True)