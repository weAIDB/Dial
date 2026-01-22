import json
import re
import os
import asyncio
import time
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm_asyncio
from functools import partial
import shutil

try:
    from schema_extractor import DDLFetcher
except ImportError:
    print("Error: schema_extractor.py not found. Please place it in the same directory.")
    exit(1)

# ==========================================
# [USER CONFIGURATION] 用户配置区域
# ==========================================

OPENAI_CONFIG = {
    "api_key": os.environ.get("DASHSCOPE_API_KEY"),
    "base_url": os.environ.get("DASHSCOPE_URL"),
    "model": "qwen3-max",
}

# 适配 schema_extractor 的配置结构
# 注意：这里主要配置 mysql，因为原代码是针对 MySQL 的
GLOBAL_DB_CONFIG = {
    "PATHS": {
        "sqlite_db_dir": "../../data/data-last/sqlite_databases/",
        "duckdb_dir": "../../data/data-last/duckdb_databases/",
    },
    "DB_CONN": {
        "mysql": {
            "host": "localhost",
            "user": "root",
            "password": "123456",
            "port": 3306,
            "charset": "utf8mb4"
        },
        "postgres": {
            "host": "localhost",
            "user": "postgres",
            "password": "123456",
            "port": 5432
        },
        "sqlserver": {
            'driver': '{ODBC Driver 17 for SQL Server}',
            'host': 'localhost',
            'user': 'sa',
            'password': 'Dialectsql123',
            'port': 1433,
        },
        "oracle": {
            "user": "system",
            "password": "Dialectsql123",
            "dsn": "localhost:1521/ORCLPDB"
        }
    }
}

# 指定当前任务使用的数据库方言'sqlite','mysql','postgres','duckdb','sqlserver','oracle'
TARGET_DIALECTS = ['oracle']

FILE_CONFIG = {
    'input_json': "../../data/data-last/Dialects.json",
    'output_json': '../qwen3max/nl2.json',
    'prompt_cache': '../qwen3max/prompt_cache',
    'temp_dir': '../qwen3max/temp_nl2'
}

MAX_CONCURRENT_REQUESTS = 10

# 预编译正则以提高性能
RE_JSON_CODE_BLOCK = re.compile(r'```(?:json)?\s*({.*?})\s*```', re.DOTALL | re.IGNORECASE)

# ==========================================
# [PROMPT TEMPLATE] Prompt 模板
# ==========================================

PROMPT_TEMPLATE_REWRITE = """
# Task: Logical Query Restructuring (Dialect-Agnostic, Business-Aware)

## Role
You are a Senior Data Architect with strong business understanding.
Your task is to translate a natural language question into a **complete, logically executable, dialect-agnostic query plan**.
This plan must bridge natural language and SQL while compensating for missing or implicit business logic.

You are NOT writing SQL.
You are writing a **deterministic logical specification** that can be translated into SQL later.

---

## Inputs
1. **User Question**
- The original natural language question.
- May be a complete question, or it may be multiple rounds of dialogue between the user and the system

2. **Selected Schema**
- A focused list of `Table.Column` pairs that are considered relevant.

3. **DDL**
- Complete table definition and data examples for each column.
- Use this to verify data types, identify implicit or non-standard relationships and detect missing or indirect foreign key paths.

---

## Core Principles (MANDATORY)

### 1. Business Logic Depth & Heuristic Compensation
- For complex or multi-step questions:
- Decompose the problem into a **business chain**. 
- Explicitly state **implicit business constraints**.If the question assumes logic not explicitly stated, apply **reasonable heuristic compensation** and describe it clearly.

### 2. Field Usage Priority
- ALWAYS prefer fields listed in **Selected Schema**.
- Only introduce additional columns from DDL if they are strictly required for joins, filters, or correctness, or their necessity is explicitly justified in the logical steps.
- NEVER invent fields, metrics, or business concepts not grounded in schema.

### 3. Operand Completeness & Dimension Clarity
- Ensure every computation has:
- Clearly defined operands
- Explicit source columns
- Clearly distinguish:
- **Grouping / aggregation dimensions**
- **Ordering (sorting) dimensions**
- **Returned (display) columns**
- Sorting by a column does NOT imply it is returned, and vice versa.

### 4. Question Completion Guarantee
- You MUST fully answer what the User Question asks.
- Partial plans, vague placeholders, or missing outputs are FORBIDDEN.
- The `### Return` section must exactly and completely satisfy the question.

### 5. Dialect-Agnostic Enforcement
- FORBIDDEN:
- Any SQL functions or dialect-specific syntax (e.g., STRFTIME, DATEADD, DATEDIFF, LIMIT).
- REQUIRED:
- Use semantic descriptions only (e.g., "extract year from date", "rank by descending value").
- Use only standard logical operators: =, >, <, >=, <=, ≠.

### 6. Aggregation-First & Join Discipline
- Follow a **CTE-like logical order**, even though no SQL is written:
1. Filter raw data
2. Aggregate / compute metrics
3. THEN join aggregated results to other entities if needed
- Explicitly reason about:
- LEFT vs RIGHT vs INNER join semantics
- Cardinality (One-to-One, One-to-Many, Many-to-Many)
- Non-standard or indirect join conditions (not just declared foreign keys)

    ---

    ## Data Typing Rule (STRICT)
    - EVERY time a column is mentioned using `Table.Column`,
      you MUST append its data type in parentheses.
      Example:
      - 'orders.OrderDate' (DATE)
      - 'customers.CustomerID' (INT)

    ### Conditional Rationale Rule (STRICT)
    - Rationale is OPTIONAL, not mandatory for every bullet point.
    - ONLY include a rationale when the step involves:
      - Non-obvious reasoning
      - Heuristic or business compensation
      - Ambiguity resolution
      - Join direction justification (LEFT vs INNER vs RIGHT)
      - Grain alignment or de-duplication logic
    - DO NOT include rationale for:
      - Simple filters
      - Direct equality joins on explicit keys
      - Straightforward aggregations without business assumptions
    - When a rationale is included:
      - It MUST be written inline at the end of the bullet point.
      - It MUST be enclosed in parentheses.
      - It MUST NOT appear on a separate line.


    ---

    ## Output Format (STRICT)

    You must output a JSON object with **ONE key only**: `Question2`.

    The value of `Question2` must be a STRING containing a structured logical plan.

    Use Markdown headers (`###`) and bullet points (`-`).

    ### Allowed Categories (ONLY include if relevant)
    - `### Source & Joins`
    - `### Filters`
    - `### Aggregation & Computation`
    - `### Ordering & Limit`
    - `### Set Operations`
    - `### Return`

    If a category is not involved, DO NOT include it.

    ---

    ## Category-Specific Rules

    ### Source & Joins
    - Identify primary source tables.
    - Describe logical join conditions.
    - Explicitly note join direction and reasoning when not obvious.
    - If joins occur AFTER aggregation, state this clearly.
    - When listing primary tables, reference table names only, without expanding full column lists.


    ### Filters
    - List all row-level constraints.
    - Use Evidence-derived values explicitly.
    - Clarify temporal, status-based, or business-validity filters.

    ### Aggregation & Computation
    - Describe grouping keys explicitly.
    - Name derived metrics and show how they are calculated.
    - Ensure aggregation logic aligns with business intent.

    ### Ordering & Limit
    - Specify sorting dimensions and direction.
    - Clarify whether ordering affects result selection or presentation only.

    ### Set Operations
    - ONLY use for UNION / INTERSECT / EXCEPT logic.
    - Clearly describe set semantics.

    ### Return
    - List ONLY what the User Question asks for.
    - If returning an entity from the "one" side of a one-to-many relationship:
      - Explicitly state: "Distinct [Column]".
    - Do NOT include intermediate or helper columns.

    ---

    ## Current Task

    **User Question**: {AUGMENTED_QUESTION}  
    **Selected Schema**: {SELECTED_SCHEMA_LIST}  
    **DDL**:
    {RELEVANT_DDL}

    Generate the JSON response now.
    """

PROMPT_TEMPLATE_REVIEW = """
# Task: Logical Query Plan Validator & Optimizer

## Role
You are a Lead Data QA Engineer. Your goal is to verify if a "Logical Query Plan" (NL2) is accurate, executable, and business-compliant.You do NOT rewrite from scratch.
You ONLY:
1. Validate whether the NL2 logical plan is correct
2. Identify concrete errors
3. Fix ONLY the incorrect parts if needed

---

## Context Inputs
1. **User Question**: {QUESTION}
2. **Evidence**: {EVIDENCE}
3. **DDL(with examples)**: {DDL}
4. **Candidate NL2 (Logical Plan)**:
{NL2}

---

## Validation Checklist (MUST FOLLOW IN ORDER)

### Check 1: Schema Validity
- Verify every referenced Table exists in DDL.
- Verify every referenced Table.Column exists in the corresponding table.
- Verify data types are consistent with DDL.
- Verify that columns not listed in Selected Schema are only used when strictly necessary.
- If additional columns are introduced without justification, mark as Schema issue.


### Check 2: Value & Operation Correctness
- Verify that operations on column values are logically valid given:
  - Column data type
  - Sample data values
- Examples:
  - String columns are not treated as numeric
  - Date-like strings are not used with unsupported operations
  - Data cleaning / deduplication logic matches observed data patterns
- If an operation is heuristic, check whether it is reasonable.

### Check 3: Format & Structural Correctness
- Output MUST be valid JSON.
- When returning NL3, NL3 content must follow Question2 format rules.
- Inside Question2:
  - Only allowed sections may appear
  - Markdown headers must use "###"
  - Bullet points must start with "-"
  - Rationale (if present) must be inline and in parentheses
  - No SQL functions or dialect-specific syntax

### Check 4: Question Completion
- Verify that NL2 fully answers the original User Question.
- Verify that:
  - All requested entities / metrics are returned
  - No required output is missing
  - The Return section matches the question intent exactly

---

## Output Format (STRICT)

You must output a JSON object with the following structure:

If NL2 is fully correct:
{{
  "valid": true
}}

If NL2 has issues:
{{
  "valid": false,
  "issues": [
    {{
      "type": "Schema | ValueLogic | Format | Incompleteness",
      "description": "Clear explanation of the problem"
    }}
  ],
  "NL3": "<Corrected Logical Plan>"
}}

Rules:
- NL3 MUST preserve correct parts of NL2.
- NL3 MUST only modify incorrect or incomplete parts.
- Do NOT introduce new logic unless required to fix an issue.
"""


# ==========================================
# [OPTIMIZED CLASS] 异步 DDL 加载器 (基于 schema_extractor)
# ==========================================
class AsyncDDLLoader:
    def __init__(self, config):
        # 初始化原版同步 Fetcher
        self.fetcher = DDLFetcher(config)
        self.cache = {}
        self.lock = asyncio.Lock()

    async def get_enriched_ddl(self, db_id, tables_str, dialect):
        """
        异步获取带有数据示例的 DDL。
        """
        # 简单的缓存键生成
        cache_key = f"{dialect}:{db_id}:{tables_str}"

        async with self.lock:
            if cache_key in self.cache:
                return self.cache[cache_key]

        # 解析表名 (复用 fetcher 的逻辑)
        tables = self.fetcher.extract_tables(tables_str)

        # 在线程池中运行阻塞的数据库操作
        try:
            ddl_result = await asyncio.to_thread(self._fetch_ddl_sync, db_id, tables, dialect)
        except Exception as e:
            ddl_result = f"-- Error fetching DDL: {str(e)}"

        async with self.lock:
            self.cache[cache_key] = ddl_result

        return ddl_result

    def _fetch_ddl_sync(self, db_id, tables, dialect):
        """同步调用 fetcher 的特定方言方法"""
        if dialect == 'mysql':
            return self.fetcher.get_mysql_ddl(db_id, tables)
        elif dialect == 'sqlite':
            return self.fetcher.get_sqlite_ddl(db_id, tables)
        elif dialect == 'postgres':
            return self.fetcher.get_postgres_ddl(db_id, tables)
        elif dialect == 'sqlserver':
            return self.fetcher.get_sqlserver_ddl(db_id, tables)
        elif dialect == 'oracle':
            return self.fetcher.get_oracle_ddl(db_id, tables)
        else:
            return f"-- Unsupported dialect: {dialect}"


# ==========================================
# [HELPER FUNCTIONS] 辅助函数
# ==========================================

def robust_json_load(raw_str):
    if not raw_str: return None
    clean_str = raw_str.replace('\xa0', ' ').replace('\u202f', ' ').strip()
    match = RE_JSON_CODE_BLOCK.search(clean_str)
    if match:
        clean_str = match.group(1)
    else:
        start = clean_str.find('{')
        end = clean_str.rfind('}')
        if start != -1 and end != -1:
            clean_str = clean_str[start:end + 1]
    try:
        return json.loads(clean_str)
    except:
        return None


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
        line = line.strip().lower()
        if line.startswith("###"):
            if "source" in line:
                current_section = "Source & Joins"
            elif "filters" in line:
                current_section = "Filters"
            elif "aggregation" in line:
                current_section = "Aggregation & Computation"
            elif "ordering" in line:
                current_section = "Ordering & Limit"
            elif "set" in line:
                current_section = "Set Operations"
            elif "return" in line:
                current_section = "Return"
        elif current_section and (line.startswith("-") or line.startswith("*")):
            stats["breakdown"][current_section] += 1
            if current_section != "Return":
                stats["total"] += 1
    return stats


# ==========================================
# [CORE LOGIC] 核心处理逻辑
# ==========================================

async def generate_nl2_rewrite_async(client, question, evidence, schema_list_str, ddl_str, dialect):
    formatted_evidence = evidence.strip() if evidence and evidence.strip() else "None"
    prompt_content = PROMPT_TEMPLATE_REWRITE.format(
        AUGMENTED_QUESTION=question,
        HINT=formatted_evidence,
        SELECTED_SCHEMA_LIST=schema_list_str,
        RELEVANT_DDL=ddl_str,
    )

    # # --- 打印 Prompt ---
    # print(f"\n{'=' * 20} PROMPT ({dialect}) START {'=' * 20}")
    # print(prompt_content)
    # print(f"{'=' * 20} PROMPT ({dialect}) END {'=' * 20}\n")
    # # -----------------------

    retries = 3
    for attempt in range(retries):
        try:
            response = await client.chat.completions.create(
                model=OPENAI_CONFIG['model'],
                messages=[
                    {"role": "system", "content": "You are a helpful database architect."},
                    {"role": "user", "content": prompt_content}
                ],
                temperature=0.5,  # 稍微降低温度以利用 Schema 信息
            )
            content = response.choices[0].message.content.strip()
            parsed = robust_json_load(content)
            if parsed:
                return parsed
            else:
                raise ValueError("Invalid JSON format")

        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                return {"Question2": f"Error: {str(e)}"}


async def review_and_optimize_nl2_with_ddl(client, item, ddl_str, dialect):
    nl2_key = f'nl2_rewrite_{dialect}'
    if nl2_key not in item or not item[nl2_key].get('Question2'):
        return

    nl2_plan = item[nl2_key]['Question2']
    try:
        prompt_content = PROMPT_TEMPLATE_REVIEW.format(
            QUESTION=item.get('question', ''),
            EVIDENCE=item.get('external_knowledge', '') or item.get('evidence', '') or "None",
            DDL=ddl_str,
            NL2=nl2_plan
        )

        # # --- 打印 Prompt ---
        # print(f"\n{'=' * 20} PROMPT ({dialect}) START {'=' * 20}")
        # print(prompt_content)
        # print(f"{'=' * 20} PROMPT ({dialect}) END {'=' * 20}\n")
        # # -----------------------

        response = await client.chat.completions.create(
            model=OPENAI_CONFIG['model'],
            messages=[
                {"role": "system", "content": "You are a strict data logic auditor."},
                {"role": "user", "content": prompt_content}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        review_result = robust_json_load(response.choices[0].message.content)

        item[f'nl2_review_{dialect}'] = {
            "valid": review_result.get("valid", False),
            "issues": review_result.get("issues", []),
            "NL3": review_result.get("NL3")
        }
    except Exception as e:
        print(f"Review Error ({dialect}): {e}")
        item[f'nl2_review_{dialect}'] = {"valid": False, "issues": [{"type": "Error", "description": str(e)}],
                                         "NL3": None}


async def process_single_item(item, client, semaphore):
    async with semaphore:
        qid = str(item.get('question_id'))

        for dialect in TARGET_DIALECTS:
            cache_path = os.path.join(FILE_CONFIG['prompt_cache'], f"{qid}_{dialect}.json")

            if not os.path.exists(cache_path):
                item[f'nl2_rewrite_{dialect}'] = {"Question2": "Error: DDL cache missing"}
                continue

            # 现在读文件是安全的，因为同一时间只有 10 个任务能运行到这里
            with open(cache_path, 'r', encoding='utf-8') as f:
                ddl_str = json.load(f).get('ddl_str')

            llm_result = await generate_nl2_rewrite_async(
                client, item['question'], item.get('evidence', ''),
                item.get('true_tables_columns', ''), ddl_str, dialect
            )
            q2_text = llm_result.get("Question2", "")
            item[f'nl2_rewrite_{dialect}'] = {"Question2": q2_text}

            if q2_text and "Error" not in q2_text:
                await review_and_optimize_nl2_with_ddl(client, item, ddl_str, dialect)

            item[f'final_NL_{dialect}'] = build_final_nl(item, dialect)

        # 保存临时文件
        temp_path = os.path.join(FILE_CONFIG['temp_dir'], f"{qid}.json")
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(item, f, ensure_ascii=False, indent=2)

def build_final_nl(item, dialect):
    nl2 = item.get(f'nl2_rewrite_{dialect}', {}).get('Question2', '')
    review = item.get(f'nl2_review_{dialect}', {})

    final_text = nl2
    source = "NL2"
    if review.get('valid') is False and review.get('NL3'):
        final_text = review['NL3']
        source = "NL3"

    return {
        "Question_final": final_text,
        "final_source": source,
        "Steps Count": count_steps_by_header(final_text)
    }


async def main_async():
    # 1. 初始化目录
    os.makedirs(FILE_CONFIG['temp_dir'], exist_ok=True)
    os.makedirs(FILE_CONFIG['prompt_cache'], exist_ok=True)

    # 2. 初始化 Loader 和 Client
    ddl_loader = AsyncDDLLoader(GLOBAL_DB_CONFIG)
    client = AsyncOpenAI(api_key=OPENAI_CONFIG['api_key'], base_url=OPENAI_CONFIG['base_url'])

    with open(FILE_CONFIG['input_json'], 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 3. 过滤已完成的任务
    finished_qids = {f.replace(".json", "") for f in os.listdir(FILE_CONFIG['temp_dir']) if f.endswith(".json")}
    todo_data = []
    for item in data:
        qid = str(item['question_id'])
        temp_path = os.path.join(FILE_CONFIG['temp_dir'], f"{qid}.json")
        if os.path.exists(temp_path):
            with open(temp_path, 'r', encoding='utf-8') as f:
                cached_item = json.load(f)
                # 检查是否所有目标方言的结果都已存在
                if all(f'final_NL_{d}' in cached_item for d in TARGET_DIALECTS):
                    continue
        todo_data.append(item)

    if not todo_data:
        print("All tasks already completed.")
        return

    # --- 新增：Prompt 预处理进度条 ---
    print("Pre-processing: Fetching DDLs and Building Prompt Cache...")
    # 使用 tqdm_asyncio 包装一个预处理任务列表
    async def prepare_prompt(item):
        qid = str(item['question_id'])
        db_id = item['db_id']
        tables_cols_str = item.get('true_tables_columns', '')
        for dialect in TARGET_DIALECTS:
            cache_path = os.path.join(FILE_CONFIG['prompt_cache'], f"{qid}_{dialect}.json")
            if not os.path.exists(cache_path):
                # 如果数据库操作失败，这里应该能体现出来
                ddl = await ddl_loader.get_enriched_ddl(db_id, tables_cols_str, dialect)
                # 检查是否是错误信息
                if ddl and not ddl.startswith("-- Error"):
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        json.dump({"ddl_str": ddl}, f, ensure_ascii=False, indent=2)
                else:
                    print(f"Warning: Failed to fetch DDL for {qid} ({dialect}): {ddl}")

    # 限制预处理的并发量，防止数据库连接过多
    prep_semaphore = asyncio.Semaphore(5)
    async def sem_prepare(item):
        async with prep_semaphore:
            await prepare_prompt(item)

    prep_tasks = [sem_prepare(item) for item in todo_data]
    await tqdm_asyncio.gather(*prep_tasks, desc="Building Prompt Cache")
    # --- 预处理结束 ---

    # 4. 执行 LLM 生成
    print(f"Starting LLM Inference...")
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    tasks = [process_single_item(item, client, semaphore) for item in todo_data]
    await tqdm_asyncio.gather(*tasks, desc="Generating Logic Plans")

    # 6. 合并结果
    print("Merging results...")
    final_output = []
    # 建立一个以 qid 为 key 的 temp 数据字典，方便快速查找
    temp_results = {}
    for f_name in os.listdir(FILE_CONFIG['temp_dir']):
        if f_name.endswith(".json"):
            with open(os.path.join(FILE_CONFIG['temp_dir'], f_name), 'r', encoding='utf-8') as tf:
                item = json.load(tf)
                temp_results[str(item['question_id'])] = item

    # 按照原始 input_json 的顺序构建最终列表
    for item in data:
        qid = str(item['question_id'])
        if qid in temp_results:
            final_output.append(temp_results[qid])
        else:
            final_output.append(item)

    # 7. 最终保存并清理
    os.makedirs(os.path.dirname(FILE_CONFIG['output_json']), exist_ok=True)
    with open(FILE_CONFIG['output_json'], 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    # 如果想保留缓存供下次使用，可以不删；如果确认本次跑完则删除
    shutil.rmtree(FILE_CONFIG['temp_dir'])
    print(f"Done! Saved to {FILE_CONFIG['output_json']}")


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main_async())
    print(f"Time: {time.time() - start_time:.2f}s")