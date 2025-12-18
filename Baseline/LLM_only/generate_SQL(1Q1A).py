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

# 尝试导入 psycopg2 用于 Postgres，如果没有安装则跳过
try:
    import psycopg2
    from psycopg2 import sql

    HAS_PG = True
except ImportError:
    HAS_PG = False

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# ==========================================
# [CONFIGURATION] 配置区域
# ==========================================

API_CONFIGS = [
    {
        "api_key": os.environ.get('DEEPSEEK_API_KEY'),  # 请替换为你的 Key
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",  # 示例模型
        "output_file": "sql_all_deepseekV3.2.json",
        "concurrency": 10
    },
]

# 1. MySQL 配置 (Host/User/Pass, db由db_id决定)
MYSQL_CONFIG = {
    'host': '192.168.10.100',
    'user': 'root',
    'password': '123456',
    'port': 3306,
    'charset': 'utf8mb4',
    'connect_timeout': 5
}

# 2. PostgreSQL 配置 (Host/User/Pass, db由db_id决定)
POSTGRES_CONFIG = {
    'host': '192.168.10.100',
    'user': 'postgres',
    'password': 'password',
    'port': 5433,
    'connect_timeout': 5
}

# 3. SQLite 配置 (存放所有sqlite文件的根目录)
# 假设结构为: data/dev_databases/{db_id}/{db_id}.sqlite
SQLITE_ROOT_PATH = '../../data/full_data/database-sqlite/'

INPUT_JSON_PATH = '../../data/full_data/dataset.json'


class MultiDialectDDLExtractor:
    def __init__(self, mysql_conf, pg_conf, sqlite_path):
        self.mysql_conf = mysql_conf
        self.pg_conf = pg_conf
        self.sqlite_path = sqlite_path
        self.cache_lock = asyncio.Lock()
        # 简单缓存： { (dialect, db_id, table_name): ddl_string }
        self.ddl_cache = {}

    def _get_mysql_connection(self, db_name):
        """连接特定的 MySQL 数据库"""
        config = self.mysql_conf.copy()
        config['database'] = db_name
        return pymysql.connect(**config, cursorclass=pymysql.cursors.DictCursor)

    def _get_pg_connection(self, db_name):
        """连接特定的 PG 数据库"""
        if not HAS_PG:
            raise ImportError("psycopg2 not installed")
        config = self.pg_conf.copy()
        config['dbname'] = db_name
        return psycopg2.connect(**config)

    def _get_sqlite_path(self, db_id):
        """
                定位 SQLite 文件路径
                目标格式: data/dev_databases/{db_id}.sqlite
                """
        # 直接拼接：根目录 + db_id.sqlite
        return os.path.join(self.sqlite_path, f"{db_id}.sqlite")

    async def get_ddl_async(self, dialect, db_id, table_names):
        """
        异步获取指定方言、指定库、指定表的 DDL
        """
        # 简单的去重
        table_names = list(set([t.lower() for t in table_names]))
        if not table_names:
            return "No tables specified."

        ddl_blocks = []

        # 针对每个表获取 DDL
        for table in table_names:
            cache_key = (dialect, db_id, table)
            if cache_key in self.ddl_cache:
                ddl_blocks.append(self.ddl_cache[cache_key])
                continue

            try:
                # 放到线程池中执行 IO 操作
                ddl = await asyncio.to_thread(self._fetch_ddl_sync, dialect, db_id, table)
                self.ddl_cache[cache_key] = ddl
                ddl_blocks.append(ddl)
            except Exception as e:
                # logger.warning(f"Failed to fetch DDL for {dialect} - {db_id}.{table}: {e}")
                ddl_blocks.append(f"-- Error fetching DDL for table {table}: {str(e)}")

        return "\n\n".join(ddl_blocks)

    def _fetch_ddl_sync(self, dialect, db_id, table_name):
        """同步执行实际的数据库查询"""
        if dialect == 'mysql':
            return self._fetch_mysql_ddl(db_id, table_name)
        elif dialect == 'postgres':
            return self._fetch_pg_ddl(db_id, table_name)
        elif dialect == 'sqlite':
            return self._fetch_sqlite_ddl(db_id, table_name)
        return ""

    def _fetch_mysql_ddl(self, db_id, table_name):
        conn = None
        try:
            conn = self._get_mysql_connection(db_id)
            with conn.cursor() as cursor:
                # 处理大小写：MySQL在某些系统上表名大小写敏感，这里尝试直接查询，如果失败查一下列表
                try:
                    cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
                except pymysql.err.ProgrammingError:
                    # 尝试模糊匹配或找真实表名（简化版）
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
                return f"-- Table {table_name} not found in SQLite"
        finally:
            conn.close()

    def _fetch_pg_ddl(self, db_id, table_name):
        """
        Postgres 没有简单的 SHOW CREATE TABLE。
        这里我们查询 information_schema 构建一个简化的 DDL 或者 Schema 描述。
        """
        if not HAS_PG:
            return "-- psycopg2 not installed, cannot fetch PG DDL"

        conn = None
        try:
            conn = self._get_pg_connection(db_id)
            cursor = conn.cursor()

            # 简单查询列信息构建伪 DDL
            query = """
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position; \
                    """
            cursor.execute(query, (table_name.lower(),))
            rows = cursor.fetchall()

            if not rows:
                return f"-- Table {table_name} not found in Postgres"

            lines = [f"CREATE TABLE {table_name} ("]
            for col, dtype, nullable in rows:
                null_str = "NULL" if nullable == 'YES' else "NOT NULL"
                lines.append(f"  {col} {dtype} {null_str},")

            # 获取主键
            pk_query = """
                       SELECT a.attname
                       FROM pg_index i \
                                JOIN pg_attribute a ON a.attrelid = i.indrelid
                           AND a.attnum = ANY (i.indkey)
                       WHERE i.indrelid = %s::regclass
                AND    i.indisprimary; \
                       """
            try:
                cursor.execute(pk_query, (table_name.lower(),))
                pks = [r[0] for r in cursor.fetchall()]
                if pks:
                    lines.append(f"  PRIMARY KEY ({', '.join(pks)})")
            except:
                pass  # 忽略复杂的主键错误

            lines.append(");")
            return f"--- PostgreSQL Table: {table_name} ---\n" + "\n".join(lines)

        except Exception as e:
            raise e
        finally:
            if conn: conn.close()

    def close(self):
        pass


# ==========================================
# [HELPER] 解析表名
# ==========================================
def extract_tables_from_string(tables_columns_str):
    """
    从 "table1.col1, table2.col2" 格式中提取表名列表
    """
    if not tables_columns_str:
        return []
    pairs = [p.strip() for p in tables_columns_str.split(',') if p.strip()]
    tables = set()
    for pair in pairs:
        if '.' in pair:
            tables.add(pair.split('.', 1)[0].strip())
        else:
            # 如果没有点，可能是只有表名或者只有列名，这里假设没有点就是表名的情况较少见
            # 但为了鲁棒性，如果有纯字符串也暂且当作表名（视具体数据格式而定）
            pass
    return list(tables)


# ==========================================
# [CORE] SQL 生成逻辑
# ==========================================
async def generate_sql_async(client, model, question, evidence, ddl_info, selected_schema, dialect, semaphore):
    """
    根据方言生成对应的 SQL
    """

    # 针对不同方言的 System Prompt
    system_message = f"""
    ## CONTEXT ##
    You are a database expert specializing in the {dialect.upper()} SQL dialect. Your primary skill is to accurately write SQL queries that answer a user's question based on a provided database schema.
    
    ## OBJECTIVE ##
    Your task is to generate a syntactically correct and semantically accurate {dialect.upper()} SQL query that answers the user's question, ensuring the following criteria are met:
    1. **Grammar Compliance**: The generated SQL must strictly adhere to the grammar and conventions of {dialect}.
    2. **Schema Adherence**: The query must only use tables and columns defined in the provided database schema.
    3. **Correctness**: The query must logically and correctly answer the user's question.
    4. **Output Format**: Return **strictly** a raw JSON object with a single key "{dialect}".

    ### Output Format
    {{
        "{dialect}": "SELECT ..."
    }}
    """

    user_message = f"""
    ### Question
    {question}

    ### External Evidence
    {evidence if evidence else "No specific evidence provided."}

    3.  **Selected Schema**: {selected_schema}
    
    4.  **DDL**: 
    {ddl_info}

    Please generate the {dialect} SQL statement strictly following the JSON format.
    """

    # # ==========================================
    # # [在此处打印 PROMPT]
    # # ==========================================
    # print(f"\n{'='*20} [{dialect.upper()}] FULL PROMPT {'='*20}")
    # print(f"--- SYSTEM ---\n{system_message}")
    # print(f"--- USER ---\n{user_message}")
    # print(f"{'='*60}\n")
    # # ==========================================

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

                sql_results = json.loads(content)

                if dialect in sql_results:
                    return {'success': True, 'data': sql_results[dialect]}
                else:
                    keys = list(sql_results.keys())
                    if keys:
                        return {'success': True, 'data': sql_results[keys[0]]}
                    return {'success': False, 'error': f'Missing "{dialect}" key in response'}

            except Exception as e:
                if "429" in str(e) or "Rate limit" in str(e):
                    wait_time = (2 ** attempt) + 1
                    logger.warning(f"[{model}][{dialect}] Rate limit, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                elif attempt == retries - 1:
                    logger.error(f"[{model}][{dialect}] Failed: {e}")
                    return {'success': False, 'error': str(e)}
                else:
                    await asyncio.sleep(1)


async def process_single_item(item, api_config, client, ddl_manager: MultiDialectDDLExtractor, semaphore):
    """
    处理单个条目：针对三种方言分别生成
    """
    item_copy = copy.deepcopy(item)

    # 结果容器
    if 'sql_generation' not in item_copy:
        item_copy['sql_generation'] = {}

    question = item_copy.get('question')
    evidence = item_copy.get('external_knowledge', '')
    extracted_cols_str = item_copy.get('true_tables_columns', '')  # 使用 gold sql 涉及的列
    db_id = item_copy.get('db_id')  # 获取数据库ID

    if not question or not extracted_cols_str or not db_id:
        item_copy['sql_generation'] = {'error': "Missing question, db_id or schema info"}
        return api_config['model'], item_copy

    # 解析出涉及的表名
    table_names = extract_tables_from_string(extracted_cols_str)

    dialects = ['mysql', 'postgres', 'sqlite']

    # 依次处理每种方言 (为了避免并发过高导致数据库连接数爆炸，这里串行处理三种方言)
    for dialect in dialects:
        # 1. 获取特定方言的 DDL
        try:
            ddl_info = await ddl_manager.get_ddl_async(dialect, db_id, table_names)
        except Exception as e:
            logger.error(f"DDL Extract Error ({dialect}/{db_id}): {e}")
            item_copy['sql_generation'][dialect] = f"Error extracting DDL: {str(e)}"
            continue

        # 2. 生成 SQL
        # [修改点 2] 这里增加了 extracted_cols_str 参数
        gen_result = await generate_sql_async(
            client,
            api_config['model'],
            question,
            evidence,
            ddl_info,
            extracted_cols_str,
            dialect,
            semaphore
        )

        # 3. 保存结果
        if gen_result['success']:
            item_copy['sql_generation'][dialect] = gen_result['data']
        else:
            item_copy['sql_generation'][dialect] = f"Error: {gen_result.get('error')}"

    return api_config['model'], item_copy


async def main_async():
    # 1. 初始化通用数据库提取器
    ddl_manager = MultiDialectDDLExtractor(MYSQL_CONFIG, POSTGRES_CONFIG, SQLITE_ROOT_PATH)
    logger.info("Multi-Dialect DDL Extractor initialized.")

    # 2. 读取文件
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
        # 初始化 Clients
        for config in API_CONFIGS:
            if not config['api_key']:
                logger.warning(f"API Key for {config['model']} is missing!")

            client = AsyncOpenAI(api_key=config['api_key'], base_url=config['base_url'])
            clients.append(client)
            semaphore = asyncio.Semaphore(config.get('concurrency', 5))

            for item in data:
                tasks.append(process_single_item(item, config, client, ddl_manager, semaphore))

        logger.info(f"Created {len(tasks)} tasks total (each task generates 3 SQLs).")

        # 执行任务
        completed_tasks = await tqdm_asyncio.gather(*tasks, desc="Generating SQLs")

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
        if ddl_manager:
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
    dialects = ['mysql', 'postgres', 'sqlite']

    for api_name, items in results_map.items():
        print(f"\nModel: {api_name}")
        total = len(items)
        if total == 0:
            continue

        for dialect in dialects:
            success_count = 0
            for item in items:
                sql_gen = item.get('sql_generation', {})
                sql_val = sql_gen.get(dialect, '')
                # 简单判断是否生成了非 Error 的内容
                if sql_val and isinstance(sql_val, str) and not sql_val.startswith("Error"):
                    success_count += 1

            rate = (success_count / total * 100)
            print(f"  - {dialect.upper()}: {success_count}/{total} ({rate:.1f}%)")


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main_async())
    print(f"Total time elapsed: {time.time() - start_time:.2f} seconds")