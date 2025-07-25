import asyncio
import mysql.connector
import json
import re
import os
import pkg_resources
from langchain.llms.base import LLM
import requests
from typing import Optional, List
from langchain_core.messages import HumanMessage

# ================ 依赖检查（自动提示版本问题） ================
def check_dependencies():
    required = {
        "langgraph": "0.1.10",
        "langchain-core": "0.2.30",
        "mysql-connector-python": "8.2.0",
        "requests": "2.31.0"
    }
    for pkg, min_ver in required.items():
        try:
            current_ver = pkg_resources.get_distribution(pkg).version
            if current_ver < min_ver:
                print(f"⚠️ 警告：{pkg}版本过低（当前{current_ver}，需≥{min_ver}）")
        except pkg_resources.DistributionNotFound:
            print(f"⚠️ 警告：未安装{pkg}，请执行 `pip install {pkg}≥{min_ver}`")

# ================ 修复LLM类：放宽密钥长度限制（或替换有效密钥） ================
class DeepSeekLLM(LLM):
    # 替换为从DeepSeek控制台获取的有效密钥（长度需符合平台要求）
    api_key: str = "sk-578f63b08e74438692e3ebdb42b49934"  
    api_url: str = "https://api.deepseek.com/v1/chat/completions"  

    @property
    def _llm_type(self) -> str:
        return "deepseek"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        # 【关键修复】注释或调整密钥长度校验（若平台允许其他长度）
        # if len(self.api_key.strip()) not in [32, 40]:
        #     error_msg = "DeepSeek API密钥格式无效（长度异常），请检查密钥是否正确"
        #     print(f"❌ {error_msg}")
        #     return f"ERROR: {error_msg}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
            "temperature": 0.3,
            "stop": stop
        }
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=20)
            print(f"DeepSeek API响应状态码: {response.status_code}")

            if response.status_code == 401:
                return "ERROR: API密钥无效或已过期，请更换有效密钥"
            if response.status_code == 403:
                return "ERROR: API权限不足，请确认开通deepseek-chat权限"
            if response.status_code != 200:
                return f"ERROR: API请求失败（状态码{response.status_code}）"

            result = response.json()
            if not result.get("choices") or not result["choices"][0].get("message"):
                return "ERROR: LLM返回无有效内容"

            content = result["choices"][0]["message"]["content"].strip()
            # 过滤无效响应
            if any(p in content for p in ["Error", "Traceback"]):
                return "ERROR: LLM返回内容异常"
            return content

        except requests.exceptions.Timeout:
            return "ERROR: API调用超时（20秒）"
        except Exception as e:
            return f"ERROR: API调用异常 - {str(e)}"

# ================ 数据库工具函数（保持不变） ================
def execute_mysql_query(sql: str, db_config: dict) -> str:
    if not sql.strip():
        return "SQL执行失败：语句为空"
    try:
        conn = mysql.connector.connect(**db_config, connection_timeout=10)
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        columns = [col[0] for col in cursor.description] if cursor.description else []
        cursor.close()
        conn.close()
        if not results:
            return "数据库查询成功，但无结果"
        # 格式化结果输出
        result_str = " | ".join(columns) + "\n"
        result_str += "\n".join(" | ".join(str(col) for col in row) for row in results)
        return result_str
    except mysql.connector.Error as e:
        return f"MySQL错误：{str(e)}（SQL: {sql[:100]}...）"
    except Exception as e:
        return f"数据库操作失败：{str(e)}"

# ================ 初始化配置（保持不变） ================
mysql_db_config = {
    "host": "localhost",
    "user": "root",
    "password": "xuhongming3410",
    "database": "BIRD"
}

# 强化提示词：明确要求SQL和Answer格式
prompt = """
严格按照以下格式输出（无额外内容）：
SQL: [符合MySQL语法的查询语句]
Answer: [基于查询结果的简洁答案]

表结构：
- customers: CustomerID, Currency, Segment
- yearmonth: CustomerID, Date(YYYYMM), Consumption

Question: {question}
"""

# ================ 业务逻辑：简化流程（移除Agent，直接调用LLM） ================
async def run_application():
    check_dependencies()
    # 检查数据库连接
    try:
        test_conn = mysql.connector.connect(**mysql_db_config, connect_timeout=5)
        test_conn.close()
        print("✅ 数据库连接测试成功")
    except mysql.connector.Error as e:
        print(f"⚠️ 数据库连接失败：{str(e)}")
        return

    llm = DeepSeekLLM()
    results = []
    for query_info in queries_info:
        question = query_info["question"]
        print(f"\n===== 处理问题 {query_info['question_id']} =====")
        print(f"问题: {question}")

        # 构造完整Prompt并调用LLM
        full_prompt = prompt.format(question=question)
        print("调用LLM生成SQL和答案...")
        llm_output = llm._call(full_prompt)
        print(f"LLM原始输出:\n{llm_output}\n" + "-"*50)

        # 解析SQL（增强容错）
        sql_match = re.search(r"(?i)SQL:\s*(.*?)(?=\nAnswer:|$)", llm_output, re.DOTALL)
        generated_sql = sql_match.group(1).strip() if sql_match else "SQL解析失败"
        # 补全SQL分号
        if generated_sql and not generated_sql.endswith(";"):
            generated_sql += ";"

        # 解析答案
        answer_match = re.search(r"(?i)Answer:\s*(.*?)(?=\n|$)", llm_output, re.DOTALL)
        answer = answer_match.group(1).strip() if answer_match else "答案解析失败"

        # 执行SQL（仅当SQL有效时）
        db_result = "未执行SQL：解析失败"
        if "解析失败" not in generated_sql:
            print("执行SQL中...")
            db_result = execute_mysql_query(generated_sql, mysql_db_config)

        # 保存结果
        results.append({
            "question_id": query_info["question_id"],
            "question": question,
            "generated_sql": generated_sql,
            "answer": answer,
            "db_result": db_result,
            "llm_output": llm_output[:500]
        })

    # 输出结果到文件
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print(f"\n===== 处理完成 =====")
    print(f"结果已保存到 {os.path.abspath('results.json')}")

# ================ 问题列表（保持不变） ================
queries_info = [
    {
        "question_id": 1471,
        "question": "What is the ratio of customers who pay in EUR against customers who pay in CZK?",
    },
    {
        "question_id": 1472,
        "question": "In 2012, who had the least consumption in LAM?",
    },
    {
        "question_id": 1473,
        "question": "What was the average monthly consumption of customers in SME for the year 2013?",
    }
]

# ================ 运行入口 ================
if __name__ == "__main__":
    print("""
    若运行异常，请先安装依赖：
    pip install -U langgraph>=0.1.10 langchain-core>=0.2.30 mysql-connector-python>=8.2.0 requests>=2.31.0
    """)
    asyncio.run(run_application())