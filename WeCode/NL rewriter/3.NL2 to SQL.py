import json
import re
import os
import asyncio
import logging
import copy
import time
from openai import AsyncOpenAI  # 使用异步客户端
from dotenv import load_dotenv
from tqdm.asyncio import tqdm_asyncio  # 异步进度条

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
JSON_BLOCK_PATTERN = re.compile(r'^```json\s*|\s*```$', re.MULTILINE)



# -----------------------------------------------------------------------------
# 配置区域
# -----------------------------------------------------------------------------
# 在这里配置你的 API 信息。concurrency 控制该模型的最大并发数。
API_CONFIGS = [
    {
        "api_key": "sk-537b00fe9a444de096505eca44f7c6bc",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "output_file": "数据/deepseekV3.2/sql98.json",
        "concurrency": 10  # 并发数控制
    },
]

INPUT_JSON_PATH = '数据/deepseekV3.2/nl2_rewrite98.json'  # 上一步生成的包含 nl2_rewrite 的文件



async def generate_sql_async(client, model, nl2_rewrite, semaphore):
    """
    异步生成 SQL，使用优化的 Prompt 和 JSON 模式
    """
    question_logic = ""
    if isinstance(nl2_rewrite, dict):
        question_logic = nl2_rewrite.get("Question2", "")
    else:
        # 如果数据格式有变（比如已经是字符串），做个兼容
        question_logic = str(nl2_rewrite)
    system_message = """
    You are an expert SQL Translator. Your task is to convert a "Structured Natural Language Query" into a precise MySQL statement.
    
    ### Input Format Understanding
    The input provides a structured natural language description of the query logic (Question2).
    It is composed of various logical blocks (e.g., Filtering, Computing, Sorting). **You must interpret these blocks dynamically based on their content.**
    
    ### Critical Instructions
    1. **Target Dialect**: Generate SQL strictly for **MySQL**.
    2. **Dynamic Logic Mapping**: Understand and implement the task requirements to generate the SQL statement.

    ### Output Format
    Return **strictly** a raw JSON object (no markdown formatting, no code blocks) with the following structure:
    {
        "mysql": "SELECT ... ;"
    }
    """
    user_message = f"""
    Please generate the SQL statements based on the structured analysis below.

    Input Data:
    {question_logic}

    Remember to handle the syntax differences for Date/String functions across the three dialects strictly.
    Output (JSON only):
    """

    async with semaphore:  # 限制并发
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

                # 清理 markdown
                content = JSON_BLOCK_PATTERN.sub('', content)

                sql_results = json.loads(content)

                # 3. 修改验证逻辑：只检查 mysql 键
                if 'mysql' in sql_results:
                    # 为了保持后续逻辑兼容，如果只返回了mysql，我们只返回这个即可
                    # 也可以在这里过滤掉其他不需要的键
                    return {'success': True, 'mysql': sql_results['mysql']}
                else:
                    return {'success': False, 'error': 'Missing mysql key in response'}

            except Exception as e:
                if "429" in str(e) or "Rate limit" in str(e):
                    wait_time = (2 ** attempt) + 1
                    logger.warning(f"[{model}] Rate limit, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                elif attempt == retries - 1:
                    return {'success': False, 'error': str(e)}
                else:
                    await asyncio.sleep(1)


async def process_single_item(item, api_config, client, semaphore):
    """
    处理单个条目：复制数据 -> 调用API -> 返回结果 (去除了验证逻辑)
    """
    # 【优化】使用浅拷贝 (shallow copy) 替代 deepcopy，大幅提升性能
    # 只要不修改 item 内部嵌套的字典/列表，浅拷贝是安全的
    q_data = item.copy()

    nl2_rewrite = q_data.get('nl2_rewrite')

    if not nl2_rewrite:
        q_data['sql_generation'] = {'error': 'Missing nl2_rewrite'}
        return api_config['model'], q_data

    # 调用 LLM
    gen_result = await generate_sql_async(client, api_config['model'], nl2_rewrite, semaphore)

    # 【修改】只输出 sql_generation: mysql，移除 validation 字段
    if gen_result['success']:
        q_data['sql_generation'] = {
            'mysql': gen_result['mysql']  # 直接保存 SQL 字符串
        }
    else:
        q_data['sql_generation'] = {
            'error': gen_result.get('error', 'Unknown error')
        }

    return api_config['model'], q_data


async def main_async():
    # 1. 读取输入数据
    if not os.path.exists(INPUT_JSON_PATH):
        logger.error(f"Input file not found: {INPUT_JSON_PATH}")
        return

    with open(INPUT_JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"Loaded {len(data)} items. Initializing {len(API_CONFIGS)} API clients...")

    # 2. 初始化 Clients 和 Semaphores
    # results 字典用于按 API 名称分类存储结果
    results_by_api = {cfg['model']: [] for cfg in API_CONFIGS}

    tasks = []

    # 为每个配置创建一个 Client 和 Semaphore，并生成所有任务
    # 注意：我们要保持 Client 存活直到任务结束
    clients = []  # 保持引用防止被回收

    for config in API_CONFIGS:
        client = AsyncOpenAI(api_key=config['api_key'], base_url=config['base_url'])
        clients.append(client)
        semaphore = asyncio.Semaphore(config.get('concurrency', 5))

        for item in data:
            # 创建任务
            tasks.append(process_single_item(item, config, client, semaphore))

    logger.info(f"Created {len(tasks)} tasks total.")

    # 3. 并发执行
    try:
        # 使用 tqdm_asyncio 显示总进度
        completed_tasks = await tqdm_asyncio.gather(*tasks, desc="Generating SQL")

        # 4. 收集结果
        for api_name, processed_item in completed_tasks:
            results_by_api[api_name].append(processed_item)

    except KeyboardInterrupt:
        logger.warning("Process interrupted!")
    except Exception as e:
        logger.error(f"Global error: {e}")

    # 5. 分别保存文件
    for config in API_CONFIGS:
        api_name = config['model']
        output_file = config['output_file']
        api_data = results_by_api[api_name]

        logger.info(f"Saving {len(api_data)} results for {api_name} to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(api_data, f, ensure_ascii=False, indent=2)

    # 6. 简单的质量分析
    analyze_results(results_by_api)


def analyze_results(results_map):
    print("\n=== Summary Analysis ===")
    for api_name, items in results_map.items():
        success = sum(1 for i in items if 'mysql' in i.get('sql_generation', {}))

        total = len(items)
        rate = (success / total * 100) if total > 0 else 0
        print(f"[{api_name}]: {success}/{total} successful ({rate:.1f}%)")


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main_async())
    print(f"Total time elapsed: {time.time() - start_time:.2f} seconds")