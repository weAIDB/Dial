import json
import re
import os
import asyncio
import logging
import copy
import time
import pymysql
import sqlite3
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm_asyncio

# 尝试导入 psycopg2 (仅用于如果需要从PG提取DDL，但在统一生成模式下通常只用MySQL或SQLite做参考)
try:
    import psycopg2

    HAS_PG = True
except ImportError:
    HAS_PG = False

# ==========================================
# [LOGGING] 日志设置
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# 屏蔽繁杂的 HTTP 日志
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# ==========================================
# [CONFIGURATION] 配置区域
# ==========================================

API_CONFIGS = [
    {
        "api_key": os.environ.get('DEEPSEEK_API_KEY'),
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "output_file": "sql_all_unified_deepseekV3.2.json",
        "concurrency": 20  # 统一生成后请求量减少，可以适当提高并发
    },
]

# 1. MySQL 配置 (作为 DDL 提取的主要来源)
MYSQL_CONFIG = {
    'host': '192.168.10.100',
    'user': 'root',
    'password': '123456',
    'port': 3306,
    'charset': 'utf8mb4',
    'connect_timeout': 5
}

# 2. PostgreSQL 配置 (保留配置供备用)
POSTGRES_CONFIG = {
    'host': '192.168.10.100',
    'user': 'postgres',
    'password': 'password',
    'port': 5433,
    'connect_timeout': 5
}

# 3. SQLite 配置
SQLITE_ROOT_PATH = '../../data/full_data/database-sqlite/'

INPUT_JSON_PATH = '../../data/full_data/dataset.json'


# ==========================================
# [CLASS] DDL 提取器
# ==========================================
class MultiDialectDDLExtractor:
    def __init__(self, mysql_conf, pg_conf, sqlite_path):
        self.mysql_conf = mysql_conf
        self.pg_conf = pg_conf
        self.sqlite_path = sqlite_path
        self.ddl_cache = {}

    def _get_mysql_connection(self, db_name):
        config = self.mysql_conf.copy()
        config['database'] = db_name
        return pymysql.connect(**config, cursorclass=pymysql.cursors.DictCursor)

    def _get_sqlite_path(self, db_id):
        return os.path.join(self.sqlite_path, f"{db_id}.sqlite")

    async def get_ddl_async(self, dialect, db_id, table_names):
        """异步获取 DDL"""
        table_names = list(set([t.lower() for t in table_names]))
        if not table_names:
            return "No tables specified."

        ddl_blocks = []
        for table in table_names:
            cache_key = (dialect, db_id, table)
            if cache_key in self.ddl_cache:
                ddl_blocks.append(self.ddl_cache[cache_key])
                continue

            try:
                # 放到线程池执行
                ddl = await asyncio.to_thread(self._fetch_ddl_sync, dialect, db_id, table)
                self.ddl_cache[cache_key] = ddl
                ddl_blocks.append(ddl)
            except Exception as e:
                ddl_blocks.append(f"-- Error fetching DDL for table {table}: {str(e)}")

        return "\n\n".join(ddl_blocks)

    def _fetch_ddl_sync(self, dialect, db_id, table_name):
        # 优先支持 MySQL 和 SQLite，PG 作为备用
        if dialect == 'mysql':
            return self._fetch_mysql_ddl(db_id, table_name)
        elif dialect == 'sqlite':
            return self._fetch_sqlite_ddl(db_id, table_name)
        return ""

    def _fetch_mysql_ddl(self, db_id, table_name):
        conn = None
        try:
            conn = self._get_mysql_connection(db_id)
            with conn.cursor() as cursor:
                try:
                    cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
                except pymysql.err.ProgrammingError:
                    # 大小写不敏感回退查找
                    cursor.execute("SHOW TABLES")
                    all_tables = [list(x.values())[0] for x in cursor.fetchall()]
                    real_name = next((t for t in all_tables if t.lower() == table_name.lower()), table_name)
                    cursor.execute(f"SHOW CREATE TABLE `{real_name}`")

                res = cursor.fetchone()
                return f"--- MySQL Table: {table_name} ---\n{res['Create Table']}"
        except Exception as e:
            raise e
        finally:
            if conn: conn.close()

    def _fetch_sqlite_ddl(self, db_id, table_name):
        path = self._get_sqlite_path(db_id)
        if not os.path.exists(path):
            return f"-- SQLite DB file not found at {path}"
        conn = sqlite3.connect(path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=? COLLATE NOCASE", (table_name,))
            res = cursor.fetchone()
            if res:
                return f"--- SQLite Table: {table_name} ---\n{res[0]}"
            else:
                return f"-- Table {table_name} not found"
        finally:
            conn.close()

    def close(self):
        pass


# ==========================================
# [HELPER] 工具函数
# ==========================================
def extract_tables_from_string(tables_columns_str):
    if not tables_columns_str:
        return []
    pairs = [p.strip() for p in tables_columns_str.split(',') if p.strip()]
    tables = set()
    for pair in pairs:
        if '.' in pair:
            tables.add(pair.split('.', 1)[0].strip())
    return list(tables)


# ==========================================
# [CORE] 统一生成 SQL 逻辑
# ==========================================
async def generate_sql_unified_async(client, model, question, evidence, ddl_info, selected_schema, semaphore):
    """
    一次性生成三种方言的 SQL
    """
    system_message = """
    ## CONTEXT ##
    You are a versatile database expert proficient in **MySQL**, **PostgreSQL**, and **SQLite**. Your primary skill is to accurately translate a user's natural language question into precise SQL queries for multiple database engines based on a provided schema.
    
    ## OBJECTIVE ##
    Your task is to generate syntactically correct and semantically accurate SQL queries for **MySQL**, **PostgreSQL**, and **SQLite** simultaneously. You must ensure the following criteria are met:

    1. **Grammar Compliance**: The generated SQL must strictly adhere to the grammar and conventions of each dialect separately.
    2. **Schema Adherence**: The query must only use tables and columns defined in the provided database schema.
    3. **Correctness**: The query must logically and correctly answer the user's question.
    4. **Output Format**: 
       - Return **strictly** a raw JSON object with exactly three keys: "mysql", "postgres", and "sqlite".
       
    ### Output Format
    {
        "mysql": "SELECT ...",
        "postgres": "SELECT ...",
        "sqlite": "SELECT ..."
    }
    """

    user_message = f"""
    ### Question
    {question}

    ### External Evidence
    {evidence if evidence else "No specific evidence provided."}

    ### Selected Schema
    {selected_schema}

    ### Database Schema (Reference DDL)
    {ddl_info}

    Please generate the SQLs strictly following the JSON format.
    """

    async with semaphore:
        retries = 3
        for attempt in range(retries):
            try:
                response = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )

                content = response.choices[0].message.content.strip()
                content = re.sub(r'^```json\s*', '', content)
                content = re.sub(r'\s*```$', '', content)

                result_json = json.loads(content)

                # 简单验证 key 是否存在
                if 'mysql' in result_json or 'sqlite' in result_json:
                    return {'success': True, 'data': result_json}
                else:
                    return {'success': False, 'error': 'Missing required keys in JSON response'}

            except Exception as e:
                if "429" in str(e) or "Rate limit" in str(e):
                    wait_time = (2 ** attempt) + 1
                    logger.warning(f"[{model}] Rate limit, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                elif attempt == retries - 1:
                    logger.error(f"[{model}] Failed: {e}")
                    return {'success': False, 'error': str(e)}
                else:
                    await asyncio.sleep(1)


async def process_single_item(item, api_config, client, ddl_manager: MultiDialectDDLExtractor, semaphore):
    """
    处理单个条目：统一生成
    """
    item_copy = copy.deepcopy(item)
    if 'sql_generation' not in item_copy:
        item_copy['sql_generation'] = {}

    question = item_copy.get('question')
    # 优先获取 external_knowledge，其次 evidence，最后为空
    evidence = item_copy.get('external_knowledge') or item_copy.get('evidence') or ''
    extracted_cols_str = item_copy.get('true_tables_columns', '')
    db_id = item_copy.get('db_id')

    if not question or not extracted_cols_str or not db_id:
        item_copy['sql_generation'] = {'error': "Missing question, db_id or schema info"}
        return api_config['model'], item_copy

    table_names = extract_tables_from_string(extracted_cols_str)

    # 1. 提取参考 DDL (默认使用 MySQL 作为 Prompt 上下文，因为它类型信息最全)
    #    如果 MySQL 提取失败，可以逻辑回退到 SQLite，这里暂且只用 MySQL
    try:
        ddl_info = await ddl_manager.get_ddl_async('mysql', db_id, table_names)
    except Exception as e:
        logger.error(f"DDL Extract Error (MySQL/{db_id}): {e}")
        # 如果MySQL失败，尝试SQLite
        try:
            ddl_info = await ddl_manager.get_ddl_async('sqlite', db_id, table_names)
        except Exception as e2:
            item_copy['sql_generation'] = {'error': f"DDL extraction failed: {e}, {e2}"}
            return api_config['model'], item_copy

    # 2. 统一生成 SQL
    gen_result = await generate_sql_unified_async(
        client,
        api_config['model'],
        question,
        evidence,
        ddl_info,
        extracted_cols_str,
        semaphore
    )

    # 3. 保存结果
    if gen_result['success']:
        # 将生成的 mysql, postgres, sqlite 结果直接更新进去
        data = gen_result['data']
        # 确保 key 存在，防止模型漏字
        item_copy['sql_generation']['mysql'] = data.get('mysql', 'Error: Missing Key')
        item_copy['sql_generation']['postgres'] = data.get('postgres', data.get('postgresql', 'Error: Missing Key'))
        item_copy['sql_generation']['sqlite'] = data.get('sqlite', 'Error: Missing Key')
    else:
        err_msg = gen_result.get('error')
        item_copy['sql_generation'] = {
            'mysql': f"Error: {err_msg}",
            'postgres': f"Error: {err_msg}",
            'sqlite': f"Error: {err_msg}"
        }

    return api_config['model'], item_copy


async def main_async():
    # 1. 初始化
    ddl_manager = MultiDialectDDLExtractor(MYSQL_CONFIG, POSTGRES_CONFIG, SQLITE_ROOT_PATH)
    logger.info("Multi-Dialect DDL Extractor initialized (Using MySQL/SQLite for Context).")

    if not os.path.exists(INPUT_JSON_PATH):
        logger.error(f"Input file not found: {INPUT_JSON_PATH}")
        return

    with open(INPUT_JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"Loaded {len(data)} items. Initializing API clients...")

    results_by_api = {cfg['model']: [] for cfg in API_CONFIGS}
    tasks = []
    clients = []

    try:
        for config in API_CONFIGS:
            if not config['api_key']:
                logger.warning(f"API Key for {config['model']} is missing!")

            client = AsyncOpenAI(api_key=config['api_key'], base_url=config['base_url'])
            clients.append(client)
            semaphore = asyncio.Semaphore(config.get('concurrency', 10))

            for item in data:
                tasks.append(process_single_item(item, config, client, ddl_manager, semaphore))

        logger.info(f"Created {len(tasks)} tasks.")

        # 执行任务
        completed_tasks = await tqdm_asyncio.gather(*tasks, desc="Generating Unified SQLs")

        for api_name, processed_item in completed_tasks:
            results_by_api[api_name].append(processed_item)

    except Exception as e:
        logger.error(f"Global error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("Closing resources...")
        for c in clients:
            await c.close()
        ddl_manager.close()

    # 保存结果
    for config in API_CONFIGS:
        api_name = config['model']
        output_file = config['output_file']
        api_data = results_by_api[api_name]

        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        logger.info(f"Saving {len(api_data)} results for {api_name} to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(api_data, f, ensure_ascii=False, indent=2)

    analyze_results(results_by_api)


def analyze_results(results_map):
    print("\n=== Summary Analysis ===")
    target_dialects = ['mysql', 'postgres', 'sqlite']

    for api_name, items in results_map.items():
        print(f"\nModel: {api_name}")
        total = len(items)
        if total == 0:
            continue

        for dialect in target_dialects:
            success_count = 0
            for item in items:
                sql_gen = item.get('sql_generation', {})
                sql_val = sql_gen.get(dialect, '')
                if sql_val and isinstance(sql_val, str) and not sql_val.startswith("Error"):
                    success_count += 1

            rate = (success_count / total * 100)
            print(f"  - {dialect.upper()}: {success_count}/{total} ({rate:.1f}%)")


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main_async())
    print(f"Total time elapsed: {time.time() - start_time:.2f} seconds")