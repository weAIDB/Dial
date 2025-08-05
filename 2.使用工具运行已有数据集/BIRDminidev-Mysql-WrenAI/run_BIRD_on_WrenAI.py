import requests
import json

# 1. 读取 JSON 文件 1
with open("mini_dev_mysql.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 2. 准备 API 请求参数
url = "http://localhost:3000/api/v1/generate_sql"
headers = {
    "accept": "application/json",
    "content-type": "application/json"
}

# 3. 遍历每个问题，拼接 question + evidence，调用 API 获取 SQL
output_data = {}
for idx, item in enumerate(data):
    combined_question = f"{item['question']} {item['evidence']}"

    payload = {
        "question": combined_question,
        "language": "english",
        "returnSqlDialect": True
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # 检查 HTTP 错误
        sql_result = response.json().get("sql", "")

        # 4. 按要求的格式存储 SQL
        output_data[str(idx)] = f"{sql_result}\t----- bird -----\t{item['db_id']}"

        print("生成SQL {idx} 成功")
    except requests.exceptions.RequestException as e:
        print(f"Error processing question {item['question_id']}: {e}")
        output_data[str(idx)] = f"ERROR: {e}\t----- bird -----\t{item['db_id']}"

# 5. 保存到 JSON 文件 2
with open("predict.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print("SQL 生成完成，已保存至 predict.json")