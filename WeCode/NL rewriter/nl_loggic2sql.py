import json
import re
import os
import asyncio
import logging
import time
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm_asyncio

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

# -----------------------------------------------------------------------------
# 配置区域
# -----------------------------------------------------------------------------
API_CONFIGS = [
    {
        "api_key": os.environ.get("DASHSCOPE_API_KEY"),
        "base_url": os.environ.get("DASHSCOPE_URL"),
        "model": "qwen3-max",  # 示例模型
        "output_file": "../qwen3max/sql.json",
        "concurrency": 10,
        "dialects": ["Oracle"]
    },
]

INPUT_JSON_PATH = '../qwen3max/nl2.json'


async def generate_sql_async(client, model, final_nl_data, question, evidence, dialect, semaphore):
    """
    异步生成 SQL，输入包含：逻辑计划、原始问题、业务证据、SQL方言
    """
    if isinstance(final_nl_data, dict):
        question_logic = final_nl_data.get("Question_final", "")
    else:
        question_logic = str(final_nl_data)

    if not question_logic:
        return {'success': False, 'error': 'Empty logic input in final_NL'}

    # -------------------------------------------------------------------------
    # System Prompt (动态注入 dialect)
    # -------------------------------------------------------------------------
    system_message = f"""
    You are a Senior SQL Developer specializing in {dialect} optimization. 
    Your task is to translate a "Deterministic Logical Specification" into a production-ready {dialect} statement.

    ### Contextual Awareness:
    - You are provided with the original 'User Question' to better understand business terms, but the 'Logical Plan' is your primary technical blueprint.
    - If the Logical Plan's semantic descriptions (e.g., "active status") are clarified in the Evidence, use that specific value.

    ### Execution Protocol:
    1. **Logical Decoding**: Map sections like `### Source & Joins` and `### Filters` to SQL.
    2. **{dialect} Standards**: Apply syntax, identifier quoting conventions (e.g., backticks vs double quotes), and date/string functions specific to {dialect}. Use CTEs for multi-step logic.
    3. **Output**: Return strictly a JSON object: {{"sql": "SELECT ..."}}
    """

    user_message = f"""
    ### Context:
    - **User Question**: {question}

    ### Technical Logical Plan:
    {question_logic}

    ### Task:
    Generate the {dialect} query that strictly follows the Logical Plan while respecting the Context provided.
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

                try:
                    sql_results = json.loads(content)
                except json.JSONDecodeError:
                    clean_content = content.replace("```json", "").replace("```", "")
                    sql_results = json.loads(clean_content)

                # 优先获取 'sql'，其次尝试获取 dialect 名字
                if 'sql' in sql_results:
                    return {'success': True, 'sql': sql_results['sql']}
                elif dialect.lower() in sql_results:
                    return {'success': True, 'sql': sql_results[dialect.lower()]}
                else:
                    return {'success': False, 'error': 'Missing "sql" key'}

            except Exception as e:
                await asyncio.sleep(1)
                if attempt == retries - 1:
                    return {'success': False, 'error': str(e)}


async def process_single_item(item, api_config, client, semaphore):
    """
    处理单个条目：支持多方言并发生成
    """
    # 1. 浅拷贝数据
    q_data = item.copy()

    question = q_data.get('question', 'Unknown Question')
    evidence = q_data.get('external_knowledge') or q_data.get('evidence', '')

    # 2. 获取方言列表 (如果没有配置，默认用 MySQL)
    target_dialects = api_config.get('dialects', ['MySQL'])

    # 初始化输出结构
    q_data['sql_generation'] = {}

    # 3. 准备并发任务
    tasks = []
    valid_dialects = []

    for dialect in target_dialects:
        # 构造 key 名，例如: final_NL_oracle
        key_name = f"final_NL_{dialect.lower()}"
        final_nl = q_data.get(key_name)

        if not final_nl:
            # 如果缺少对应的逻辑计划，直接在结果中记录错误，不阻碍其他方言生成
            q_data['sql_generation'][dialect.lower()] = f"Error: Missing {key_name}"
            continue

        valid_dialects.append(dialect)
        # 创建生成任务
        tasks.append(
            generate_sql_async(
                client,
                api_config['model'],
                final_nl,
                question,
                evidence,
                dialect,
                semaphore
            )
        )

    # 4. 并发执行所有方言的生成任务
    if tasks:
        results = await asyncio.gather(*tasks)

        # 5. 将结果回填到字典中
        for dialect, res in zip(valid_dialects, results):
            # 键名为小写 (oracle, mysql)
            dict_key = dialect.lower()

            if res['success']:
                # 直接赋值 SQL 字符串
                q_data['sql_generation'][dict_key] = res['sql']
            else:
                # 记录错误信息
                q_data['sql_generation'][dict_key] = f"Error: {res.get('error')}"

    return api_config['model'], q_data


async def main_async():
    if not os.path.exists(INPUT_JSON_PATH):
        logger.error(f"Input file not found: {INPUT_JSON_PATH}")
        return

    with open(INPUT_JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"Loaded {len(data)} items. Initializing API clients...")

    results_by_api = {cfg['model']: [] for cfg in API_CONFIGS}
    tasks = []
    clients = []

    for config in API_CONFIGS:
        client = AsyncOpenAI(api_key=config['api_key'], base_url=config['base_url'])
        clients.append(client)
        semaphore = asyncio.Semaphore(config.get('concurrency', 5))

        for item in data:
            tasks.append(process_single_item(item, config, client, semaphore))

    logger.info(f"Created {len(tasks)} tasks total.")

    try:
        completed_tasks = await tqdm_asyncio.gather(*tasks, desc="Generating SQL")

        for api_name, processed_item in completed_tasks:
            results_by_api[api_name].append(processed_item)

    except KeyboardInterrupt:
        logger.warning("Process interrupted!")
    except Exception as e:
        logger.error(f"Global error: {e}")
    finally:
        # 关闭客户端连接
        for c in clients:
            await c.close()

    # 保存结果
    for config in API_CONFIGS:
        api_name = config['model']
        output_file = config['output_file']
        api_data = results_by_api[api_name]

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        logger.info(f"Saving {len(api_data)} results for {api_name} ({config.get('dialect')}) to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(api_data, f, ensure_ascii=False, indent=2)

    analyze_results(results_by_api)


def analyze_results(results_map):
    print("\n=== Summary Analysis ===")
    for api_name, items in results_map.items():
        success_count = 0
        for item in items:
            gen_data = item.get('sql_generation', {})
            if not gen_data:
                continue

            # 只要有一个方言生成成功（值不是以 "Error:" 开头），就算这条数据成功
            # 注意：我们在 process_single_item 里定义错误是以 "Error:" 开头的
            is_valid = False
            for val in gen_data.values():
                if isinstance(val, str) and not val.startswith("Error:"):
                    is_valid = True
                    break

            if is_valid:
                success_count += 1

        total = len(items)
        rate = (success_count / total * 100) if total > 0 else 0
        print(f"[{api_name}]: {success_count}/{total} successful ({rate:.1f}%)")


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main_async())
    print(f"Total time elapsed: {time.time() - start_time:.2f} seconds")