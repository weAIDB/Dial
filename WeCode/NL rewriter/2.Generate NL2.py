import json
import re
import os
import asyncio
import pymysql
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm_asyncio
import time
from functools import partial

# ==========================================
# [USER CONFIGURATION] 用户配置区域
# ==========================================

OPENAI_CONFIG = {
    "api_key": "",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat",
}

MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'bird',
    'port': 3306,
    'charset': 'utf8mb4',
    'connect_timeout': 10
}

FILE_CONFIG = {
    'input_json': '数据/deepseekV3.2/semantic_analysis98.json',
    'output_json': '数据/deepseekV3.2/nl2_rewrite98.json'
}

MAX_CONCURRENT_REQUESTS = 10

# 预编译正则以提高性能
RE_JSON_CODE_BLOCK = re.compile(r'^```(?:json)?\s*({.*})\s*```$', re.DOTALL | re.IGNORECASE)
RE_MARKDOWN_HEADER = re.compile(r'^###\s+(.*)', re.IGNORECASE)

# ==========================================
# [PROMPT TEMPLATE] Prompt 模板
# ==========================================

PROMPT_TEMPLATE_REWRITE = """
    # Task: Logical Query Restructuring (Dialect-Agnostic)

    ## Role
    You are a Senior Data Architect. Your goal is to translate a natural language question into a structured, logical specification (Question2), strictly following the required steps to achieve the **Target Return**.
    
    ## Inputs
    1.  **User Question**: The original query (may be ambiguous).
    2.  **Evidence**: External domain knowledge or rules. 
        *   If provided: This is the **Primary Source of Truth** for resolving ambiguity (e.g., defining "best" or specific value mappings).
        *   If "None" or empty: Rely strictly on standard logic and the provided Schema.
    3.  **Selected Schema**: The primary list of `Table.Column` to focus on.
    4.  **DDL**: Full table definitions. Use this to check data types (e.g., String vs Timestamp) and identify necessary Foreign Keys not in the Selected Schema.
    5.  **Target Return**: It is exactly what the user wants to see. This MUST guide the `### Return` section.
    
    ## Key Requirements
    1.  **Data Typing**: In the `Question2` plan, every time you mention a column in the `Table.Column` format (e.g., 'customers.CustomerID'), you **MUST** append its data type in parentheses, e.g., `'customers.CustomerID' (INT)` or `'yearmonth.Date' (VARCHAR)`.
    2.  **Goal-Oriented**: The `### Return` section MUST directly map to the items listed in `Target Return`.
    3.  **Ambiguity Resolution**: Use `Evidence` to resolve vague terms into specific logical steps.
    4.  **Dialect-Agnostic**: **FORBIDDEN** to use specific SQL functions (e.g., NO `STRFTIME`, `DATEDIFF`). Use descriptive text for operations (e.g., "year part of 'date'").
    5.  **Logical Operators**: Use standard mathematical symbols (`=`, `>`, `<`, etc.).

    ## Output Format (Strict Syntax)
    You must output a JSON object containing a single key `Question2`. The value must be a string containing a structured plan.
    Inside the string, use Markdown headers (`###`). List specific operation steps with a hyphen `-`.
    **Rule**: If a category is not involved, DO NOT include it in the output.

    **Categories:**
    *   `### Source & Joins`: Specify primary tables and describe logical connections (e.g., "Link Table A and Table B on A.key = B.key").
    *   `### Filters`: List conditions to narrow down data. Mention values derived from Evidence.
    *   `### Aggregation & Computation`: Describe groupings, mathematical operations, or derived columns (e.g., "Count distinct IDs").
    *   `### Ordering & Limit`: Describe sorting logic and row limits.
    *   `### Set Operations`: ONLY for `UNION`, `INTERSECT`, or `EXCEPT` logic.
    *   `### Return`: List ONLY the columns explicitly requested in the User Question. If the data comes from a One-to-Many join and refers to the "One" side entity, explicitly write "Distinct [Column Name]".

    ## Examples
    **Input**:
    *   **User Question**: In February 2012, what percentage of customers consumed more than 528.3?
    *   **Evidence**: February 2012 refers to '201202' in yearmonth.date; The first 4 strings of the Date values in the yearmonth table can represent year; The 5th and 6th string of the date can refer to month.
    *   **Selected Schema**: yearmonth.customerid, yearmonth.consumption, yearmonth.date
    *   **DDL**: 
    --- Table: yearmonth ---
    CREATE TABLE `yearmonth` (`CustomerID` int NOT NULL, `Date` varchar(255) NOT NULL, `Consumption` double DEFAULT NULL, PRIMARY KEY (`Date`,`CustomerID`), KEY `CustomerID` (`CustomerID`), CONSTRAINT `yearmonth_ibfk_1` FOREIGN KEY (`CustomerID`) REFERENCES `customers` (`CustomerID`) ON DELETE CASCADE ON UPDATE CASCADE ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
    *   **Target Return**: Segment with biggest percentage increase, Segment with lowest percentage increase
    
    **Output**:
    ```json
    {{
      "Question2": "### Source & Joins\n- Source: 'yearmonth'\n\n### Filters\n- 'yearmonth.Date' (VARCHAR) = '201202'\n\n### Aggregation & Computation\n- Calculate 'total_customers' = Count of Distinct 'yearmonth.CustomerID' (INT)\n- Calculate 'target_customers' = Count of Distinct 'yearmonth.CustomerID' (INT) where 'yearmonth.Consumption' (DOUBLE) > 528.3\n- Calculate 'percentage' = ('target_customers' / 'total_customers') * 100\n\n### Return\n- percentage"
    }}

    ## Current Task

    **User Question**: {AUGMENTED_QUESTION}
    **Evidence**: {HINT}
    **Selected Schema**: {SELECTED_SCHEMA_LIST}
    **DDL**:
    {RELEVANT_DDL}
    Target Return: {RETURN_CONTENT}

    Please generate the JSON response now.
    """

# ==========================================
# [OPTIMIZED CLASS] 数据库提取器 (并发安全版)
# ==========================================
class MySQLDDLExtractor:
    def __init__(self, db_config):
        self.db_config = db_config
        # 缓存：避免重复查询数据库
        self.ddl_cache = {}
        self.columns_cache = {}
        self.table_map_cache = None
        # 锁：用于保护缓存写入，防止并发竞争
        self.cache_lock = asyncio.Lock()

    def _get_conn(self):
        """创建新的短连接，确保并发安全"""
        return pymysql.connect(**self.db_config, cursorclass=pymysql.cursors.DictCursor)

    async def _get_real_table_name_async(self, table_name):
        """异步获取真实表名"""
        # 1. 读缓存（无锁读取）
        if self.table_map_cache is not None:
            return self.table_map_cache.get(table_name.lower())

        # 2. 写缓存（加锁）
        async with self.cache_lock:
            # 双重检查
            if self.table_map_cache is not None:
                return self.table_map_cache.get(table_name.lower())

            # 在线程池中执行同步的数据库操作
            try:
                def fetch_tables():
                    conn = self._get_conn()
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute("SHOW TABLES")
                            return cursor.fetchall()
                    finally:
                        conn.close()

                tables = await asyncio.to_thread(fetch_tables)

                # 构建映射
                self.table_map_cache = {
                    list(t.values())[0].lower(): list(t.values())[0]
                    for t in tables
                }
            except Exception as e:
                print(f"Error fetching table list: {e}")
                return None

            return self.table_map_cache.get(table_name.lower())

    async def get_table_ddl_async(self, table_name):
        """异步获取 DDL"""
        t_lower = table_name.lower()
        if t_lower in self.ddl_cache:
            return self.ddl_cache[t_lower]

        real_name = await self._get_real_table_name_async(table_name)
        if not real_name:
            return f"Table {table_name} not found"

        async with self.cache_lock:
            # 双重检查
            if t_lower in self.ddl_cache:
                return self.ddl_cache[t_lower]

            try:
                def fetch_ddl():
                    conn = self._get_conn()
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute(f"SHOW CREATE TABLE `{real_name}`")
                            return cursor.fetchone()
                    finally:
                        conn.close()

                result = await asyncio.to_thread(fetch_ddl)

                if result:
                    ddl = result['Create Table'] if isinstance(result, dict) else result[1]
                    self.ddl_cache[t_lower] = ddl
                    return ddl
            except Exception as e:
                return f"Error getting DDL for {table_name}: {str(e)}"

        return f"Table {table_name} not found"

    def close(self):
        # 无需关闭，因为使用短连接模式
        pass


# ==========================================
# [HELPER FUNCTIONS] 辅助函数
# ==========================================

def count_steps_by_header(question2_text):
    stats = {
        "total": 0,
        "breakdown": {
            "Source & Joins": 0, "Filters": 0, "Aggregation & Computation": 0,
            "Ordering & Limit": 0, "Set Operations": 0, "Return": 0
        }
    }
    if not question2_text: return stats

    current_section = None
    lines = question2_text.split('\n')

    for line in lines:
        line = line.strip()
        lower_line = line.lower()

        # 优化：使用 startswith 快速判断
        if line.startswith("###"):
            if "source" in lower_line and "joins" in lower_line:
                current_section = "Source & Joins"
            elif "filters" in lower_line:
                current_section = "Filters"
            elif "aggregation" in lower_line or "computation" in lower_line:
                current_section = "Aggregation & Computation"
            elif "ordering" in lower_line or "limit" in lower_line:
                current_section = "Ordering & Limit"
            elif "set operations" in lower_line:
                current_section = "Set Operations"
            elif "return" in lower_line:
                current_section = "Return"
        elif current_section and (line.startswith("-") or line.startswith("*")):
            if len(line) > 2:
                stats["breakdown"][current_section] += 1
                if current_section != "Return":
                    stats["total"] += 1
    return stats


async def get_relevant_ddl_str_async(extracted_tables_columns, ddl_extractor):
    if not extracted_tables_columns or not ddl_extractor:
        return "No schema info provided."

    # 解析表名
    pairs = [p.strip() for p in extracted_tables_columns.split(',') if p.strip()]
    tables = set()
    for pair in pairs:
        if '.' in pair:
            tables.add(pair.split('.', 1)[0].strip())

    ddl_blocks = []
    for table_name in tables:
        ddl = await ddl_extractor.get_table_ddl_async(table_name)
        ddl_blocks.append(f"--- Table: {table_name} ---\n{ddl}")

    return "\n\n".join(ddl_blocks) if ddl_blocks else "No schema info provided."


# ==========================================
# [CORE LOGIC] 核心处理逻辑
# ==========================================

async def generate_nl2_rewrite_async(client, question, evidence, schema_list_str, ddl_str, target_return):
    formatted_evidence = evidence.strip() if evidence and evidence.strip() else "None"
    prompt_content = PROMPT_TEMPLATE_REWRITE.format(
        AUGMENTED_QUESTION=question,
        HINT=formatted_evidence,
        SELECTED_SCHEMA_LIST=schema_list_str,
        RELEVANT_DDL=ddl_str,
        RETURN_CONTENT=target_return,
    )

    # print(f"\n{'=' * 20} DEBUG: PROMPT START {'=' * 20}")
    # print(prompt_content)
    # print(f"{'=' * 20} DEBUG: PROMPT END {'=' * 20}\n")

    retries = 3
    for attempt in range(retries):
        try:
            response = await client.chat.completions.create(
                model=OPENAI_CONFIG['model'],
                messages=[
                    {"role": "system", "content": "You are a helpful database architect."},
                    {"role": "user", "content": prompt_content}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content.strip()

            # 优化：更鲁棒的 JSON 提取
            match = RE_JSON_CODE_BLOCK.search(content)
            if match:
                content = match.group(1)
            else:
                # 尝试找到第一个 { 和最后一个 }
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1:
                    content = content[start:end + 1]

            return json.loads(content)

        except Exception as e:
            if attempt < retries - 1:
                # 指数退避
                await asyncio.sleep(2 ** attempt)
            else:
                print(f"LLM Error: {e}")
                return {"Question2": f"Error: {str(e)}"}


async def process_single_item(item, ddl_extractor, client, semaphore):
    """处理单条数据"""
    q_data = item
    question = q_data.get('question', '')
    evidence = q_data.get('evidence', '')
    target_return = item.get('semantic_analysis', '').get('return_content','');
    # tables_cols_str = item.get('schema_linking','').get('extracted_tables_columns', '')   #用schema linking获取的列
    tables_cols_str = q_data.get('true_tables_columns', '')   #用gold sql里涉及的列


    if not tables_cols_str:
        q_data['nl2_rewrite'] = {"Question2": "Skipped: No table info", "Steps Count": {"total": 0}}
        return

    # 异步获取 DDL，不阻塞主线程
    ddl_str = await get_relevant_ddl_str_async(tables_cols_str, ddl_extractor)

    async with semaphore:
        llm_result = await generate_nl2_rewrite_async(
            client, question, evidence, tables_cols_str, ddl_str,target_return
        )

    q2_text = llm_result.get("Question2", "")
    steps_stats = count_steps_by_header(q2_text)

    q_data['nl2_rewrite'] = {
        "Question2": q2_text,
        "Steps Count": steps_stats
    }


async def main_async():
    # 1. 初始化数据库连接
    ddl_extractor = None
    if MYSQL_CONFIG:
        try:
            # 传入配置字典
            ddl_extractor = MySQLDDLExtractor(MYSQL_CONFIG)
            print("MySQL extraction initialized (Thread-safe mode).")
        except Exception as e:
            print(f"MySQL init failed: {e}")

    # 2. 初始化 OpenAI
    client = AsyncOpenAI(
        api_key=OPENAI_CONFIG['api_key'],
        base_url=OPENAI_CONFIG['base_url']
    )

    # 3. 读取输入文件
    if not os.path.exists(FILE_CONFIG['input_json']):
        print(f"Input file {FILE_CONFIG['input_json']} not found!")
        return

    with open(FILE_CONFIG['input_json'], 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Processing {len(data)} items with {MAX_CONCURRENT_REQUESTS} concurrent requests...")

    # 4. 执行任务
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    tasks = [
        process_single_item(item, ddl_extractor, client, semaphore)
        for item in data
    ]

    try:
        # 使用 tqdm 显示进度
        await tqdm_asyncio.gather(*tasks, desc="Generating Question2")
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    finally:
        if ddl_extractor:
            ddl_extractor.close()

    # 5. 保存结果
    print(f"Saving results to {FILE_CONFIG['output_json']}...")
    with open(FILE_CONFIG['output_json'], 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Done.")


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main_async())
    print(f"Time elapsed: {time.time() - start_time:.2f}s")
