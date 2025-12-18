import json
import asyncio
import os
from openai import AsyncOpenAI

# 1. 配置异步 LLM 客户端
client = AsyncOpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com"
)

# 限制最大并发数，避免触发服务器压力过大或速率限制 (根据你的 API 额度调整)
MAX_CONCURRENT_TASKS = 10
semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

async def get_columns_from_llm(gold_sql_dict, idx):
    """
    异步构造 Prompt 并请求 LLM 解析 SQL
    """
    prompt = f"""
    你是一个 SQL 解析专家。请分析以下三个不同方言的 SQL 语句，并提取其中引用的所有【真实物理表名.列名】。

    SQL 内容：
    - MySQL: {gold_sql_dict.get('mysql', 'N/A')}
    - SQLite: {gold_sql_dict.get('sqlite', 'N/A')}
    - PostgreSQL: {gold_sql_dict.get('postgres', 'N/A')}

    任务要求：
    1. 必须还原别名（Alias），找到原始表名。
    2. 如果是子查询，请穿透到最底层的物理表。
    3. 将所有“表名.列名”取并集，去重。
    4. 最终结果只需输出一个字符串，各字段用英文逗号分隔（例如: "table1.col1,table1.col2"）。
    5. 不要输出任何解释、不要输出 Markdown，只给字符串结果。
    """

    async with semaphore:  # 控制并发数量
        try:
            response = await client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            result = response.choices[0].message.content.strip().replace('"', '').replace('`', '')
            print(f"[{idx}] 处理完成")
            return result
        except Exception as e:
            print(f"[{idx}] LLM 请求失败: {e}")
            return ""

async def process_json_async(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = [data]

    # 2. 创建所有待执行的任务列表
    tasks = []
    for i, item in enumerate(data):
        gold_sql = item.get("gold_sql", {})
        # 将协程包装进任务
        tasks.append(get_columns_from_llm(gold_sql, i + 1))

    # 3. 并行执行所有任务并等待结果
    print(f"开始并行处理 {len(tasks)} 条数据...")
    results = await asyncio.gather(*tasks)

    # 4. 将结果回填到原始数据中
    for i, res in enumerate(results):
        data[i]["true_table_columns"] = res

    # 5. 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    # 使用 asyncio.run 运行主入口
    asyncio.run(process_json_async('dataset.json', 'output.json'))
    print("全部处理完成！")