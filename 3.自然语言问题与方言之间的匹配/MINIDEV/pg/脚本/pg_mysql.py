# # # # # # # # # # # # # import json
# # # # # # # # # # # # # import requests
# # # # # # # # # # # # # import os
# # # # # # # # # # # # # from time import sleep


# # # # # # # # # # # # # def load_undo_json(file_path):
# # # # # # # # # # # # #     """加载待分析的undo.json文件，增加文件路径验证"""
# # # # # # # # # # # # #     if not os.path.exists(file_path):
# # # # # # # # # # # # #         print(f"错误：文件不存在 - {file_path}")
# # # # # # # # # # # # #         return None
# # # # # # # # # # # # #     if not os.path.isfile(file_path):
# # # # # # # # # # # # #         print(f"错误：不是有效文件 - {file_path}")
# # # # # # # # # # # # #         return None
    
# # # # # # # # # # # # #     try:
# # # # # # # # # # # # #         with open(file_path, 'r', encoding='utf-8') as f:
# # # # # # # # # # # # #             return json.load(f)
# # # # # # # # # # # # #     except json.JSONDecodeError as e:
# # # # # # # # # # # # #         print(f"错误：JSON解析失败 - {str(e)}（文件：{file_path}）")
# # # # # # # # # # # # #         return None
# # # # # # # # # # # # #     except Exception as e:
# # # # # # # # # # # # #         print(f"错误：加载文件失败 - {str(e)}（文件：{file_path}）")
# # # # # # # # # # # # #         return None


# # # # # # # # # # # # # def query_deepseek_reasoner(question, postgres_sql, mysql_sql, max_retries=3):
# # # # # # # # # # # # #     """调用deepseek-reasoner模型分析语法差异，增加重试机制和格式校验"""
# # # # # # # # # # # # #     # 配置API参数（参考Deepseek官方文档）
# # # # # # # # # # # # #     API_URL = "https://api.deepseek.com/chat/completions"
# # # # # # # # # # # # #     MODEL_NAME = "deepseek-chat"  # 模型名称必须指定
# # # # # # # # # # # # #     API_KEY = ""  # 替换为你的有效密钥
    
# # # # # # # # # # # # #     # 构建提示词（明确格式要求，减少模型输出错误）
# # # # # # # # # # # # #     prompt = f"""
# # # # # # # # # # # # #     任务：分析PostgreSQL和MySQL语句的语法差异及对应的自然语言原因。
# # # # # # # # # # # # #     自然语言问题：{question}
# # # # # # # # # # # # #     PostgreSQL语句：{postgres_sql}
# # # # # # # # # # # # #     MySQL语句：{mysql_sql}
    
# # # # # # # # # # # # #     要求：
# # # # # # # # # # # # #     1. 仅输出JSON格式，不包含任何额外文本、解释或标记（如```json）。
# # # # # # # # # # # # #     2. JSON包含两个字段：
# # # # # # # # # # # # #        - syntax_differences：数组，列举语法差异（如标识符引号、函数支持等）。
# # # # # # # # # # # # #        - causing_part：字符串，描述导致差异的自然语言问题部分（如"排序时对NULL值的处理"）。
# # # # # # # # # # # # #     3. 差异描述需准确，例如："PostgreSQL使用NULLS FIRST，MySQL不支持该语法"。
# # # # # # # # # # # # #     """
    
# # # # # # # # # # # # #     headers = {
# # # # # # # # # # # # #         "Content-Type": "application/json",
# # # # # # # # # # # # #         "Authorization": f"Bearer {API_KEY}"  # 确保格式正确
# # # # # # # # # # # # #     }
    
# # # # # # # # # # # # #     # 构建符合API要求的请求体（OpenAI兼容格式）
# # # # # # # # # # # # #     payload = {
# # # # # # # # # # # # #         "model": MODEL_NAME,
# # # # # # # # # # # # #         "messages": [{"role": "user", "content": prompt}],  # 必须用messages字段
# # # # # # # # # # # # #         "max_tokens": 500,
# # # # # # # # # # # # #         "temperature": 0.0  # 降低随机性，确保输出稳定
# # # # # # # # # # # # #     }
    
# # # # # # # # # # # # #     # 带重试的请求逻辑（处理临时网络错误）
# # # # # # # # # # # # #     for retry in range(max_retries):
# # # # # # # # # # # # #         try:
# # # # # # # # # # # # #             response = requests.post(
# # # # # # # # # # # # #                 API_URL,
# # # # # # # # # # # # #                 headers=headers,
# # # # # # # # # # # # #                 json=payload,
# # # # # # # # # # # # #                 timeout=30  # 设置超时时间
# # # # # # # # # # # # #             )
            
# # # # # # # # # # # # #             # 处理HTTP错误状态码
# # # # # # # # # # # # #             if response.status_code == 401:
# # # # # # # # # # # # #                 print("错误：API密钥无效或已过期（401）")
# # # # # # # # # # # # #                 return None  # 密钥错误无需重试
# # # # # # # # # # # # #             if response.status_code == 429:
# # # # # # # # # # # # #                 print(f"警告：请求频率超限，等待{2 ** retry}秒后重试...")
# # # # # # # # # # # # #                 sleep(2 ** retry)  # 指数退避重试
# # # # # # # # # # # # #                 continue
# # # # # # # # # # # # #             if response.status_code != 200:
# # # # # # # # # # # # #                 print(f"错误：API请求失败（状态码：{response.status_code}），响应：{response.text[:200]}")
# # # # # # # # # # # # #                 return None
            
# # # # # # # # # # # # #             # 解析响应内容
# # # # # # # # # # # # #             result = response.json()
# # # # # # # # # # # # #             # 验证响应结构
# # # # # # # # # # # # #             if not all(key in result for key in ["choices"]) or len(result["choices"]) == 0:
# # # # # # # # # # # # #                 print("错误：API返回格式异常（无choices字段）")
# # # # # # # # # # # # #                 return None
            
# # # # # # # # # # # # #             # 提取并清洗模型输出（去除可能的多余字符）
# # # # # # # # # # # # #             model_output = result["choices"][0]["message"]["content"].strip()
# # # # # # # # # # # # #             # 移除可能的代码块标记（如```json）
# # # # # # # # # # # # #             model_output = model_output.replace("```json", "").replace("```", "").strip()
            
# # # # # # # # # # # # #             # 解析为JSON
# # # # # # # # # # # # #             try:
# # # # # # # # # # # # #                 return json.loads(model_output)
# # # # # # # # # # # # #             except json.JSONDecodeError as e:
# # # # # # # # # # # # #                 print(f"错误：模型输出JSON解析失败 - {str(e)}，原始输出：{model_output[:200]}")
# # # # # # # # # # # # #                 return None
            
# # # # # # # # # # # # #         except requests.exceptions.Timeout:
# # # # # # # # # # # # #             print(f"警告：请求超时，第{retry+1}次重试...")
# # # # # # # # # # # # #         except requests.exceptions.ConnectionError:
# # # # # # # # # # # # #             print(f"警告：网络连接错误，第{retry+1}次重试...")
# # # # # # # # # # # # #         except Exception as e:
# # # # # # # # # # # # #             print(f"错误：请求过程异常 - {str(e)}")
# # # # # # # # # # # # #             if retry < max_retries - 1:
# # # # # # # # # # # # #                 sleep(1)
# # # # # # # # # # # # #                 continue
    
# # # # # # # # # # # # #     # 超过最大重试次数
# # # # # # # # # # # # #     print(f"错误：已达到最大重试次数（{max_retries}次），请求失败")
# # # # # # # # # # # # #     return None


# # # # # # # # # # # # # def main():
# # # # # # # # # # # # #     # 定义文件路径
# # # # # # # # # # # # #     input_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\undo.json"
# # # # # # # # # # # # #     output_dir = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result"
# # # # # # # # # # # # #     output_path = os.path.join(output_dir, "pg_mysql_difference.json")
    
# # # # # # # # # # # # #     # 确保输出目录存在
# # # # # # # # # # # # #     os.makedirs(output_dir, exist_ok=True)
    
# # # # # # # # # # # # #     # 加载输入数据
# # # # # # # # # # # # #     data = load_undo_json(input_path)
# # # # # # # # # # # # #     if not data:
# # # # # # # # # # # # #         print("无法加载输入数据，程序退出")
# # # # # # # # # # # # #         return
    
# # # # # # # # # # # # #     # 处理每个问题（增加进度提示）
# # # # # # # # # # # # #     total = len(data)
# # # # # # # # # # # # #     results = []
# # # # # # # # # # # # #     for i, item in enumerate(data, 1):
# # # # # # # # # # # # #         # 验证数据完整性
# # # # # # # # # # # # #         if not all(key in item for key in ['question', 'postgres', 'mysql']):
# # # # # # # # # # # # #             print(f"跳过无效数据（第{i}/{total}条）：缺少必要字段")
# # # # # # # # # # # # #             continue
        
# # # # # # # # # # # # #         question = item['question']
# # # # # # # # # # # # #         postgres_sql = item['postgres']
# # # # # # # # # # # # #         mysql_sql = item['mysql']
        
# # # # # # # # # # # # #         print(f"\n处理进度：{i}/{total} - 问题：{question[:60]}...")
# # # # # # # # # # # # #         diff_info = query_deepseek_reasoner(question, postgres_sql, mysql_sql)
        
# # # # # # # # # # # # #         if diff_info:
# # # # # # # # # # # # #             results.append({
# # # # # # # # # # # # #                 "question": question,
# # # # # # # # # # # # #                 "postgres_sql": postgres_sql,
# # # # # # # # # # # # #                 "mysql_sql": mysql_sql,
# # # # # # # # # # # # #                 "syntax_differences": diff_info.get("syntax_differences", []),
# # # # # # # # # # # # #                 "causing_part": diff_info.get("causing_part", "")
# # # # # # # # # # # # #             })
# # # # # # # # # # # # #             print(f"处理成功：已获取差异信息")
# # # # # # # # # # # # #         else:
# # # # # # # # # # # # #             # 记录失败条目，避免丢失进度
# # # # # # # # # # # # #             results.append({
# # # # # # # # # # # # #                 "question": question,
# # # # # # # # # # # # #                 "postgres_sql": postgres_sql,
# # # # # # # # # # # # #                 "mysql_sql": mysql_sql,
# # # # # # # # # # # # #                 "syntax_differences": ["分析失败"],
# # # # # # # # # # # # #                 "causing_part": "无法确定"
# # # # # # # # # # # # #             })
# # # # # # # # # # # # #             print(f"处理失败：无法获取差异信息")
    
# # # # # # # # # # # # #     # 保存结果到JSON文件
# # # # # # # # # # # # #     try:
# # # # # # # # # # # # #         with open(output_path, 'w', encoding='utf-8') as f:
# # # # # # # # # # # # #             json.dump(results, f, ensure_ascii=False, indent=2)
# # # # # # # # # # # # #         print(f"\n所有任务处理完成，结果已保存到：{output_path}")
# # # # # # # # # # # # #         print(f"成功：{sum(1 for r in results if r['syntax_differences'][0] != '分析失败')}条，失败：{sum(1 for r in results if r['syntax_differences'][0] == '分析失败')}条")
# # # # # # # # # # # # #     except Exception as e:
# # # # # # # # # # # # #         print(f"错误：保存结果文件失败 - {str(e)}")


# # # # # # # # # # # # # if __name__ == "__main__":
# # # # # # # # # # # # #     main()



# # # # # # # # # # # # # # #2.



# # # # # # # # # # # # # # import json
# # # # # # # # # # # # # # import os
# # # # # # # # # # # # # # from shutil import copy2

# # # # # # # # # # # # # # def rename_json_key(file_path, old_key, new_key):
# # # # # # # # # # # # # #     """
# # # # # # # # # # # # # #     将JSON文件中指定键名替换为新键名，并创建备份文件
    
# # # # # # # # # # # # # #     参数:
# # # # # # # # # # # # # #         file_path: JSON文件的完整路径
# # # # # # # # # # # # # #         old_key: 需要被替换的旧键名
# # # # # # # # # # # # # #         new_key: 替换后的新键名
# # # # # # # # # # # # # #     """
# # # # # # # # # # # # # #     # 验证文件是否存在
# # # # # # # # # # # # # #     if not os.path.exists(file_path):
# # # # # # # # # # # # # #         print(f"错误：文件不存在 - {file_path}")
# # # # # # # # # # # # # #         return False
    
# # # # # # # # # # # # # #     # 验证是否为有效文件
# # # # # # # # # # # # # #     if not os.path.isfile(file_path):
# # # # # # # # # # # # # #         print(f"错误：{file_path} 不是有效文件")
# # # # # # # # # # # # # #         return False
    
# # # # # # # # # # # # # #     # 创建备份文件（添加.bak后缀）
# # # # # # # # # # # # # #     backup_path = f"{file_path}.bak"
# # # # # # # # # # # # # #     try:
# # # # # # # # # # # # # #         copy2(file_path, backup_path)
# # # # # # # # # # # # # #         print(f"已创建备份文件：{backup_path}")
# # # # # # # # # # # # # #     except Exception as e:
# # # # # # # # # # # # # #         print(f"警告：备份文件创建失败 - {str(e)}，继续执行但建议手动备份")
    
# # # # # # # # # # # # # #     # 读取并解析JSON数据
# # # # # # # # # # # # # #     try:
# # # # # # # # # # # # # #         with open(file_path, 'r', encoding='utf-8') as f:
# # # # # # # # # # # # # #             data = json.load(f)
# # # # # # # # # # # # # #     except json.JSONDecodeError as e:
# # # # # # # # # # # # # #         print(f"错误：JSON格式解析失败 - {str(e)}（文件：{file_path}）")
# # # # # # # # # # # # # #         return False
# # # # # # # # # # # # # #     except Exception as e:
# # # # # # # # # # # # # #         print(f"错误：读取文件失败 - {str(e)}（文件：{file_path}）")
# # # # # # # # # # # # # #         return False
    
# # # # # # # # # # # # # #     # 统一数据格式为列表（支持单字典或列表格式的JSON）
# # # # # # # # # # # # # #     if isinstance(data, dict):
# # # # # # # # # # # # # #         items = [data]
# # # # # # # # # # # # # #     elif isinstance(data, list):
# # # # # # # # # # # # # #         items = data
# # # # # # # # # # # # # #     else:
# # # # # # # # # # # # # #         print(f"错误：不支持的JSON数据类型（必须是列表或字典）")
# # # # # # # # # # # # # #         return False
    
# # # # # # # # # # # # # #     # 替换键名并统计数量
# # # # # # # # # # # # # #     replaced_count = 0
# # # # # # # # # # # # # #     for item in items:
# # # # # # # # # # # # # #         if isinstance(item, dict) and old_key in item:
# # # # # # # # # # # # # #             # 保留值，替换键名
# # # # # # # # # # # # # #             item[new_key] = item.pop(old_key)
# # # # # # # # # # # # # #             replaced_count += 1
    
# # # # # # # # # # # # # #     # 保存修改后的内容
# # # # # # # # # # # # # #     try:
# # # # # # # # # # # # # #         with open(file_path, 'w', encoding='utf-8') as f:
# # # # # # # # # # # # # #             json.dump(data, f, ensure_ascii=False, indent=2)
# # # # # # # # # # # # # #         print(f"处理完成！文件已保存至：{file_path}")
# # # # # # # # # # # # # #         print(f"共替换 {replaced_count} 处 '{old_key}' 为 '{new_key}'")
# # # # # # # # # # # # # #         return True
# # # # # # # # # # # # # #     except Exception as e:
# # # # # # # # # # # # # #         print(f"错误：保存文件失败 - {str(e)}（文件：{file_path}）")
# # # # # # # # # # # # # #         return False


# # # # # # # # # # # # # # if __name__ == "__main__":
# # # # # # # # # # # # # #     # 目标文件路径
# # # # # # # # # # # # # #     target_file = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\do.json"
# # # # # # # # # # # # # #     # 旧键名和新键名
# # # # # # # # # # # # # #     original_key = "SQL"
# # # # # # # # # # # # # #     target_key = "postgres"
    
# # # # # # # # # # # # # #     # 执行键名替换操作
# # # # # # # # # # # # # #     rename_json_key(target_file, original_key, target_key)



# # # # # # # # # # # # # #3.



# # import json
# # import re
# # import requests
# # import os
# # from time import sleep


# # def load_undo_json(file_path):
# #     """加载待分析的 undo.json 文件，增加文件路径验证"""
# #     if not os.path.exists(file_path):
# #         print(f"错误：文件不存在 - {file_path}")
# #         return None
# #     if not os.path.isfile(file_path):
# #         print(f"错误：不是有效文件 - {file_path}")
# #         return None

# #     try:
# #         with open(file_path, 'r', encoding='utf-8') as f:
# #             return json.load(f)
# #     except json.JSONDecodeError as e:
# #         print(f"错误：JSON 解析失败 - {str(e)}（文件：{file_path}）")
# #         return None
# #     except Exception as e:
# #         print(f"错误：加载文件失败 - {str(e)}（文件：{file_path}）")
# #         return None


# # def find_substring_matches(text, patterns):
# #     """在文本中查找符合模式的子字符串，返回匹配信息列表"""
# #     matches_info = []
# #     for pattern, syntax_type in patterns:
# #         regex = re.compile(pattern, re.IGNORECASE)
# #         for match in regex.finditer(text):
# #             matches_info.append({
# #                 "text": match.group(),
# #                 "type": syntax_type
# #             })
# #     return matches_info


# # def extract_corresponding_substrings(question, postgres_sql, mysql_sql):
# #     """提取问题、PostgreSQL SQL、MySQL SQL 中对应语法差异的子字符串（不含位置信息）"""
# #     # 定义 PostgreSQL 和 MySQL 特有的语法模式
# #     pg_patterns = [
# #         (r'LIMIT\s+\d+\s+OFFSET\s+\d+', 'pg'),
# #         (r'SERIAL', 'pg'),
# #         (r'pg_\w+', 'pg'),
# #         (r'DATE_PART', 'pg'),
# #         (r'ARRAY', 'pg'),
# #         (r'NULLS\s+(FIRST|LAST)', 'pg'),
# #         (r'STRICT', 'pg'),
# #         (r'RETURNING', 'pg')
# #     ]
# #     mysql_patterns = [
# #         (r'LIMIT\s+\d+,\s*\d+', 'mysql'),
# #         (r'AUTO_INCREMENT', 'mysql'),
# #         (r'DATE_FORMAT', 'mysql'),
# #         (r'JSON_OBJECT', 'mysql'),
# #         (r'ON DUPLICATE KEY UPDATE', 'mysql'),
# #         (r'INSERT IGNORE', 'mysql'),
# #         (r'UNSIGNED', 'mysql')
# #     ]

# #     # 从问题中找到可能涉及差异语法的子串
# #     question_matches = []
# #     combined_patterns = pg_patterns + mysql_patterns
# #     for pattern, syntax_type in combined_patterns:
# #         regex = re.compile(pattern, re.IGNORECASE)
# #         for match in regex.finditer(question):
# #             question_matches.append({
# #                 "text": match.group(),
# #                 "type": syntax_type
# #             })

# #     result = []
# #     for q_match in question_matches:
# #         q_text = q_match["text"]
        
# #         # 在 PostgreSQL SQL 中找对应语法的子串
# #         pg_matches = find_substring_matches(postgres_sql, pg_patterns)
# #         pg_corresponding = [m for m in pg_matches if re.search(re.escape(q_text), m["text"], re.IGNORECASE)]
# #         pg_sub = pg_corresponding[0]["text"] if pg_corresponding else ""

# #         # 在 MySQL SQL 中找对应语法的子串
# #         mysql_matches = find_substring_matches(mysql_sql, mysql_patterns)
# #         mysql_corresponding = [m for m in mysql_matches if re.search(re.escape(q_text), m["text"], re.IGNORECASE)]
# #         mysql_sub = mysql_corresponding[0]["text"] if mysql_corresponding else ""

# #         # 只保留文本内容，不包含位置信息
# #         result.append({
# #             "text": q_text,
# #             "postgres": pg_sub,
# #             "mysql": mysql_sub
# #         })
# #     return result


# # def query_deepseek_reasoner(question, postgres_sql, mysql_sql, max_retries=3):
# #     """调用 deepseek-reasoner 模型分析语法差异（要求不返回位置信息）"""
# #     API_URL = "https://api.deepseek.com/chat/completions"
# #     MODEL_NAME = "deepseek-chat"
# #     API_KEY = ""  # 替换为你的有效密钥

# #     prompt = f"""
# #     任务：分析 PostgreSQL 和 MySQL 语句的语法差异、对应的自然语言原因，以及问题、SQL 中涉及差异的具体子字符串。
# #     自然语言问题：{question}
# #     PostgreSQL 语句：{postgres_sql}
# #     MySQL 语句：{mysql_sql}
    
# #     要求：
# #     1. 仅输出 JSON 格式，不包含任何额外文本、解释或标记（如```json）。
# #     2. JSON 包含三个字段：
# #        - syntax_differences：数组，列举语法差异（如标识符引号、函数支持等）。
# #        - causing_part：字符串，描述导致差异的自然语言问题部分。
# #        - question_substrings：数组，每个元素包含"text"（问题中的差异子字符串）、
# #          "postgres"（PostgreSQL SQL 中对应子串）、"mysql"（MySQL SQL 中对应子串）。
# #          注意：不要包含 start 和 end 等位置信息！
# #     3. 差异描述需准确，例如："PostgreSQL 使用 NULLS FIRST，MySQL 不支持该语法"。
# #     """

# #     headers = {
# #         "Content-Type": "application/json",
# #         "Authorization": f"Bearer {API_KEY}"
# #     }

# #     payload = {
# #         "model": MODEL_NAME,
# #         "messages": [{"role": "user", "content": prompt}],
# #         "max_tokens": 800,
# #         "temperature": 0.1
# #     }

# #     for retry in range(max_retries):
# #         try:
# #             response = requests.post(
# #                 API_URL,
# #                 headers=headers,
# #                 json=payload,
# #                 timeout=30
# #             )

# #             if response.status_code == 401:
# #                 print("错误：API 密钥无效或已过期（401）")
# #                 return None
# #             if response.status_code == 429:
# #                 print(f"警告：请求频率超限，等待{2 ** retry}秒后重试...")
# #                 sleep(2 ** retry)
# #                 continue
# #             if response.status_code != 200:
# #                 print(f"错误：API 请求失败（状态码：{response.status_code}），响应：{response.text[:200]}")
# #                 return None

# #             result = response.json()
# #             if not all(key in result for key in ["choices"]) or len(result["choices"]) == 0:
# #                 print("错误：API 返回格式异常（无 choices 字段）")
# #                 return None

# #             model_output = result["choices"][0]["message"]["content"].strip()
# #             model_output = model_output.replace("```json", "").replace("```", "").strip()
            
# #             # 解析后移除可能存在的位置字段
# #             model_data = json.loads(model_output)
# #             if "question_substrings" in model_data:
# #                 for item in model_data["question_substrings"]:
# #                     item.pop("start", None)
# #                     item.pop("end", None)
# #             return model_data

# #         except requests.exceptions.Timeout:
# #             print(f"警告：请求超时，第{retry + 1}次重试...")
# #         except requests.exceptions.ConnectionError:
# #             print(f"警告：网络连接错误，第{retry + 1}次重试...")
# #         except Exception as e:
# #             print(f"错误：请求过程异常 - {str(e)}")
# #             if retry < max_retries - 1:
# #                 sleep(1)
# #                 continue

# #     print(f"错误：已达到最大重试次数（{max_retries}次），请求失败")
# #     return None


# # def main():
# #     input_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\undo1.json"
# #     output_dir = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result"
# #     output_path = os.path.join(output_dir, "pg_mysql_difference_2.json")

# #     os.makedirs(output_dir, exist_ok=True)

# #     data = load_undo_json(input_path)
# #     if not data:
# #         print("无法加载输入数据，程序退出")
# #         return

# #     total = len(data)
# #     results = []
# #     success_count = 0
# #     fail_count = 0

# #     for i, item in enumerate(data, 1):
# #         required_fields = ['question', 'postgres', 'mysql']
# #         if not all(key in item for key in required_fields):
# #             missing = [key for key in required_fields if key not in item]
# #             print(f"跳过无效数据（第{i}/{total}条）：缺少字段 {missing}")
# #             continue

# #         question = item['question']
# #         postgres_sql = item['postgres']
# #         mysql_sql = item['mysql']

# #         print(f"\n处理进度：{i}/{total} - 问题：{question[:60]}...")
# #         diff_info = query_deepseek_reasoner(question, postgres_sql, mysql_sql)

# #         question_substrings = []
# #         if diff_info and "question_substrings" in diff_info:
# #             question_substrings = diff_info["question_substrings"]
# #         else:
# #             question_substrings = extract_corresponding_substrings(question, postgres_sql, mysql_sql)

# #         if diff_info:
# #             success_count += 1
# #             results.append({
# #                 "question": question,
# #                 "postgres_sql": postgres_sql,
# #                 "mysql_sql": mysql_sql,
# #                 "syntax_differences": diff_info.get("syntax_differences", []),
# #                 "causing_part": diff_info.get("causing_part", ""),
# #                 "question_substrings": question_substrings,
# #                 "analysis_method": "model"
# #             })
# #             print(f"处理成功：已获取差异信息（累计成功：{success_count}）")
# #         else:
# #             fail_count += 1
# #             results.append({
# #                 "question": question,
# #                 "postgres_sql": postgres_sql,
# #                 "mysql_sql": mysql_sql,
# #                 "syntax_differences": ["分析失败"],
# #                 "causing_part": "无法确定",
# #                 "question_substrings": question_substrings,
# #                 "analysis_method": "backup"
# #             })
# #             print(f"处理失败：使用备份方法提取子字符串（累计失败：{fail_count}）")

# #     try:
# #         with open(output_path, 'w', encoding='utf-8') as f:
# #             json.dump(results, f, ensure_ascii=False, indent=2)
# #         print(f"\n所有任务处理完成，结果已保存到：{output_path}")
# #         print(f"总处理：{total}条，成功：{success_count}条，失败：{fail_count}条")
# #     except Exception as e:
# #         print(f"错误：保存结果文件失败 - {str(e)}")


# # if __name__ == "__main__":
# #     main()
    
    
    
# # # # # # # # # # # #4.


# # # # # # # # # # # import json
# # # # # # # # # # # import requests
# # # # # # # # # # # import os
# # # # # # # # # # # from time import sleep


# # # # # # # # # # # def load_undo_json(file_path):
# # # # # # # # # # #     """加载待分析的undo.json文件，增加文件路径验证"""
# # # # # # # # # # #     if not os.path.exists(file_path):
# # # # # # # # # # #         print(f"错误：文件不存在 - {file_path}")
# # # # # # # # # # #         return None
# # # # # # # # # # #     if not os.path.isfile(file_path):
# # # # # # # # # # #         print(f"错误：不是有效文件 - {file_path}")
# # # # # # # # # # #         return None

# # # # # # # # # # #     try:
# # # # # # # # # # #         with open(file_path, 'r', encoding='utf-8') as f:
# # # # # # # # # # #             return json.load(f)
# # # # # # # # # # #     except json.JSONDecodeError as e:
# # # # # # # # # # #         print(f"错误：JSON解析失败 - {str(e)}（文件：{file_path}）")
# # # # # # # # # # #         return None
# # # # # # # # # # #     except Exception as e:
# # # # # # # # # # #         print(f"错误：加载文件失败 - {str(e)}（文件：{file_path}）")
# # # # # # # # # # #         return None


# # # # # # # # # # # def query_deepseek_reasoner(question, postgres_sql, mysql_sql, max_retries=3):
# # # # # # # # # # #     """调用deepseek-reasoner模型分析PostgreSQL和MySQL语法差异，明确每个差异项的字段结构"""
# # # # # # # # # # #     API_URL = "https://api.deepseek.com/chat/completions"
# # # # # # # # # # #     MODEL_NAME = "deepseek-chat"  # 模型名称必须指定
# # # # # # # # # # #     API_KEY = ""  # 替换为有效密钥

# # # # # # # # # # #     # 构建提示词（明确每个差异项的5个字段 + 示例引导）
# # # # # # # # # # #     prompt = f"""
# # # # # # # # # # #     任务：分析PostgreSQL和MySQL语句的语法差异，提取细粒度差异片段。
# # # # # # # # # # #     自然语言问题：{question}
# # # # # # # # # # #     PostgreSQL语句：{postgres_sql}
# # # # # # # # # # #     MySQL语句：{mysql_sql}

# # # # # # # # # # #     要求：
# # # # # # # # # # #     1. 仅输出JSON格式（无多余文本），结构如下：
# # # # # # # # # # #        {{
# # # # # # # # # # #          "syntax_differences": [
# # # # # # # # # # #            {{
# # # # # # # # # # #              "difference": "差异类别（如条件表达式语法）",
# # # # # # # # # # #              "detail": "具体差异描述（如PostgreSQL用CASE WHEN，MySQL用IF）",
# # # # # # # # # # #              "question_causing_substring": "问题中导致该差异的子串（原问题精确片段）",
# # # # # # # # # # #              "postgres_differing_substring": "PostgreSQL语句中对应差异的子串（原SQL精确片段）",
# # # # # # # # # # #              "mysql_differing_substring": "MySQL语句中对应差异的子串（原SQL精确片段）"
# # # # # # # # # # #            }},
# # # # # # # # # # #            ...
# # # # # # # # # # #          ],
# # # # # # # # # # #          "causing_part": "整体差异的自然语言概括（如条件表达式与数据类型差异）"
# # # # # # # # # # #        }}
# # # # # # # # # # #     2. 子字符串必须是原文本的**精确片段**（不得修改/概括），例如：
# # # # # # # # # # #        - 问题子串："如何处理除零错误"
# # # # # # # # # # #        - PostgreSQL子串："NULLIF(10, 0)"（处理除零）
# # # # # # # # # # #        - MySQL子串："/ 10"（未处理除零）
# # # # # # # # # # #     3. 差异描述需准确，如："PostgreSQL用NULLIF避免除零，MySQL未显式处理"。

# # # # # # # # # # #     参考示例（仅格式参考，无需复制）：
# # # # # # # # # # #     问题："如何处理条件表达式和浮点数类型"
# # # # # # # # # # #     PostgreSQL："SELECT CASE WHEN 1>0 THEN 'yes' ELSE 'no' END AS res, REAL(3.14) AS num;"
# # # # # # # # # # #     MySQL："SELECT IF(1>0, 'yes', 'no') AS res, FLOAT(3.14) AS num;"
# # # # # # # # # # #     期望输出（简化）：
# # # # # # # # # # #     {{
# # # # # # # # # # #       "syntax_differences": [
# # # # # # # # # # #         {{
# # # # # # # # # # #           "difference": "条件表达式语法",
# # # # # # # # # # #           "detail": "PostgreSQL用CASE WHEN，MySQL用IF函数",
# # # # # # # # # # #           "question_causing_substring": "处理条件表达式",
# # # # # # # # # # #           "postgres_differing_substring": "CASE WHEN",
# # # # # # # # # # #           "mysql_differing_substring": "IF("
# # # # # # # # # # #         }},
# # # # # # # # # # #         {{
# # # # # # # # # # #           "difference": "浮点数类型",
# # # # # # # # # # #           "detail": "PostgreSQL用REAL，MySQL用FLOAT",
# # # # # # # # # # #           "question_causing_substring": "浮点数类型",
# # # # # # # # # # #           "postgres_differing_substring": "REAL",
# # # # # # # # # # #           "mysql_differing_substring": "FLOAT"
# # # # # # # # # # #         }}
# # # # # # # # # # #       ],
# # # # # # # # # # #       "causing_part": "条件表达式与浮点数类型的实现差异"
# # # # # # # # # # #     }}
# # # # # # # # # # #     """

# # # # # # # # # # #     headers = {
# # # # # # # # # # #         "Content-Type": "application/json",
# # # # # # # # # # #         "Authorization": f"Bearer {API_KEY}"
# # # # # # # # # # #     }

# # # # # # # # # # #     payload = {
# # # # # # # # # # #         "model": MODEL_NAME,
# # # # # # # # # # #         "messages": [{"role": "user", "content": prompt}],
# # # # # # # # # # #         "max_tokens": 1200,  # 增加令牌数容纳更多字段
# # # # # # # # # # #         "temperature": 0.1   # 低随机性保证结构稳定
# # # # # # # # # # #     }

# # # # # # # # # # #     # 带重试的请求逻辑
# # # # # # # # # # #     for retry in range(max_retries):
# # # # # # # # # # #         try:
# # # # # # # # # # #             response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
# # # # # # # # # # #             if response.status_code == 401:
# # # # # # # # # # #                 print("错误：API密钥无效（401）")
# # # # # # # # # # #                 return None
# # # # # # # # # # #             if response.status_code == 429:
# # # # # # # # # # #                 sleep(2 ** retry)
# # # # # # # # # # #                 continue
# # # # # # # # # # #             if response.status_code != 200:
# # # # # # # # # # #                 print(f"API失败（{response.status_code}）：{response.text[:200]}")
# # # # # # # # # # #                 return None

# # # # # # # # # # #             result = response.json()
# # # # # # # # # # #             if not result.get("choices"):
# # # # # # # # # # #                 print("响应无choices字段")
# # # # # # # # # # #                 return None

# # # # # # # # # # #             model_output = result["choices"][0]["message"]["content"].strip()
# # # # # # # # # # #             model_output = model_output.replace("```json", "").replace("```", "").strip()
# # # # # # # # # # #             return json.loads(model_output)

# # # # # # # # # # #         except requests.exceptions.Timeout:
# # # # # # # # # # #             print(f"超时，第{retry+1}次重试...")
# # # # # # # # # # #         except requests.exceptions.ConnectionError:
# # # # # # # # # # #             print(f"网络错误，第{retry+1}次重试...")
# # # # # # # # # # #         except json.JSONDecodeError as e:
# # # # # # # # # # #             print(f"JSON解析失败：{e}，输出：{model_output[:200]}")
# # # # # # # # # # #             return None
# # # # # # # # # # #         except Exception as e:
# # # # # # # # # # #             print(f"请求异常：{e}")
# # # # # # # # # # #             if retry < max_retries - 1:
# # # # # # # # # # #                 sleep(1)

# # # # # # # # # # #     print("达到最大重试次数，请求失败")
# # # # # # # # # # #     return None


# # # # # # # # # # # def main():
# # # # # # # # # # #     # 更新文件路径为指定位置
# # # # # # # # # # #     input_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\undo1.json"
# # # # # # # # # # #     output_dir = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result"
# # # # # # # # # # #     output_path = os.path.join(output_dir, "postgres_mysql_difference3.json")
# # # # # # # # # # #     os.makedirs(output_dir, exist_ok=True)

# # # # # # # # # # #     data = load_undo_json(input_path)
# # # # # # # # # # #     if not data:
# # # # # # # # # # #         return

# # # # # # # # # # #     total = len(data)
# # # # # # # # # # #     results = []
# # # # # # # # # # #     for i, item in enumerate(data, 1):
# # # # # # # # # # #         # 验证必要字段是否存在
# # # # # # # # # # #         if not all(key in item for key in ['question', 'postgres', 'mysql']):
# # # # # # # # # # #             missing_fields = [key for key in ['question', 'postgres', 'mysql'] if key not in item]
# # # # # # # # # # #             print(f"跳过无效数据（{i}/{total}）：缺少字段 {missing_fields}")
# # # # # # # # # # #             continue

# # # # # # # # # # #         question = item['question']
# # # # # # # # # # #         postgres_sql = item['postgres']
# # # # # # # # # # #         mysql_sql = item['mysql']

# # # # # # # # # # #         print(f"\n处理 {i}/{total}：{question[:60]}...")
# # # # # # # # # # #         diff_info = query_deepseek_reasoner(question, postgres_sql, mysql_sql)

# # # # # # # # # # #         if diff_info:
# # # # # # # # # # #             # 确保字段存在（模型可能漏填，设默认值）
# # # # # # # # # # #             for diff in diff_info.get("syntax_differences", []):
# # # # # # # # # # #                 diff.setdefault("question_causing_substring", "")
# # # # # # # # # # #                 diff.setdefault("postgres_differing_substring", "")
# # # # # # # # # # #                 diff.setdefault("mysql_differing_substring", "")

# # # # # # # # # # #             results.append({
# # # # # # # # # # #                 "question": question,
# # # # # # # # # # #                 "postgres_sql": postgres_sql,
# # # # # # # # # # #                 "mysql_sql": mysql_sql,
# # # # # # # # # # #                 "syntax_differences": diff_info.get("syntax_differences", []),
# # # # # # # # # # #                 "causing_part": diff_info.get("causing_part", "")
# # # # # # # # # # #             })
# # # # # # # # # # #             print("处理成功：差异信息已提取")
# # # # # # # # # # #         else:
# # # # # # # # # # #             results.append({
# # # # # # # # # # #                 "question": question,
# # # # # # # # # # #                 "postgres_sql": postgres_sql,
# # # # # # # # # # #                 "mysql_sql": mysql_sql,
# # # # # # # # # # #                 "syntax_differences": [{"difference": "分析失败", "detail": "", "question_causing_substring": "", "postgres_differing_substring": "", "mysql_differing_substring": ""}],
# # # # # # # # # # #                 "causing_part": "无法确定"
# # # # # # # # # # #             })
# # # # # # # # # # #             print("处理失败：未获取有效差异")

# # # # # # # # # # #     # 保存结果
# # # # # # # # # # #     try:
# # # # # # # # # # #         with open(output_path, 'w', encoding='utf-8') as f:
# # # # # # # # # # #             json.dump(results, f, ensure_ascii=False, indent=2)
# # # # # # # # # # #         success = sum(1 for r in results if r["syntax_differences"][0]["difference"] != "分析失败")
# # # # # # # # # # #         print(f"\n结果保存至：{output_path}")
# # # # # # # # # # #         print(f"成功：{success} 条，失败：{len(results)-success} 条")
# # # # # # # # # # #     except Exception as e:
# # # # # # # # # # #         print(f"保存失败：{e}")


# # # # # # # # # # # if __name__ == "__main__":
# # # # # # # # # # #     main()
    
    
    
# # # # # # # # # # #将问题归类


# # # # # # # # # # import json
# # # # # # # # # # import os

# # # # # # # # # # def group_by_difference(input_file, output_file):
# # # # # # # # # #     """
# # # # # # # # # #     将JSON文件中的数据按"syntax_differences"数组中的"difference"字段分类，并保存到新的JSON文件
    
# # # # # # # # # #     参数:
# # # # # # # # # #         input_file: 输入JSON文件路径
# # # # # # # # # #         output_file: 输出JSON文件路径
# # # # # # # # # #     """
# # # # # # # # # #     try:
# # # # # # # # # #         # 读取输入文件
# # # # # # # # # #         with open(input_file, 'r', encoding='utf-8') as f:
# # # # # # # # # #             data = json.load(f)
        
# # # # # # # # # #         # 确保输入数据是列表类型
# # # # # # # # # #         if not isinstance(data, list):
# # # # # # # # # #             raise ValueError("输入JSON文件的根元素必须是列表")
        
# # # # # # # # # #         # 按"difference"分组
# # # # # # # # # #         grouped = {}
# # # # # # # # # #         skipped_items = 0  # 记录跳过的项目数量
# # # # # # # # # #         total_processed = 0  # 记录处理的差异数量
        
# # # # # # # # # #         for item in data:
# # # # # # # # # #             # 检查顶层必要字段
# # # # # # # # # #             top_level_fields = ["question", "postgres_sql", "mysql_sql"]
# # # # # # # # # #             missing_top_fields = [field for field in top_level_fields if field not in item]
            
# # # # # # # # # #             if missing_top_fields:
# # # # # # # # # #                 skipped_items += 1
# # # # # # # # # #                 print(f"警告: 跳过缺少顶层字段的数据项，缺少字段: {', '.join(missing_top_fields)}")
# # # # # # # # # #                 continue
            
# # # # # # # # # #             # 检查是否有syntax_differences字段且是列表
# # # # # # # # # #             if "syntax_differences" not in item or not isinstance(item["syntax_differences"], list):
# # # # # # # # # #                 skipped_items += 1
# # # # # # # # # #                 print("警告: 跳过缺少有效的syntax_differences数组的数据项")
# # # # # # # # # #                 continue
            
# # # # # # # # # #             # 处理每个syntax_difference
# # # # # # # # # #             for diff in item["syntax_differences"]:
# # # # # # # # # #                 # 检查差异项中的必要字段
# # # # # # # # # #                 diff_fields = ["difference", "question_causing_substring", 
# # # # # # # # # #                              "postgres_differing_substring", "mysql_differing_substring"]
# # # # # # # # # #                 missing_diff_fields = [field for field in diff_fields if field not in diff]
                
# # # # # # # # # #                 if missing_diff_fields:
# # # # # # # # # #                     skipped_items += 1
# # # # # # # # # #                     print(f"警告: 跳过缺少字段的差异项，缺少字段: {', '.join(missing_diff_fields)}")
# # # # # # # # # #                     continue
                
# # # # # # # # # #                 # 准备要保存的条目，包含顶层信息和当前差异信息
# # # # # # # # # #                 entry = {
# # # # # # # # # #                     "question": item["question"],
# # # # # # # # # #                     "postgres_sql": item["postgres_sql"],
# # # # # # # # # #                     "mysql_sql": item["mysql_sql"],
# # # # # # # # # #                     "question_causing_substring": diff["question_causing_substring"],
# # # # # # # # # #                     "postgres_differing_substring": diff["postgres_differing_substring"],
# # # # # # # # # #                     "mysql_differing_substring": diff["mysql_differing_substring"],
# # # # # # # # # #                     "difference": diff["difference"],
# # # # # # # # # #                     "detail": diff.get("detail", "")  # 可选字段
# # # # # # # # # #                 }
                
# # # # # # # # # #                 difference = diff["difference"]
# # # # # # # # # #                 # 确保difference是字符串类型
# # # # # # # # # #                 if not isinstance(difference, str):
# # # # # # # # # #                     difference = str(difference)
                
# # # # # # # # # #                 # 按difference分组，允许重复项
# # # # # # # # # #                 if difference not in grouped:
# # # # # # # # # #                     grouped[difference] = []
# # # # # # # # # #                 grouped[difference].append(entry)
# # # # # # # # # #                 total_processed += 1
        
# # # # # # # # # #         # 确保输出目录存在
# # # # # # # # # #         output_dir = os.path.dirname(output_file)
# # # # # # # # # #         if not os.path.exists(output_dir):
# # # # # # # # # #             os.makedirs(output_dir)
        
# # # # # # # # # #         # 保存结果到输出文件
# # # # # # # # # #         with open(output_file, 'w', encoding='utf-8') as f:
# # # # # # # # # #             json.dump(grouped, f, ensure_ascii=False, indent=4)
        
# # # # # # # # # #         print(f"成功将数据按'difference'分类，结果已保存到: {output_file}")
# # # # # # # # # #         print(f"共分为 {len(grouped)} 个不同的'difference'类别")
# # # # # # # # # #         print(f"共处理了 {total_processed} 个差异项")
# # # # # # # # # #         print(f"处理过程中跳过了 {skipped_items} 个有问题的数据项/差异项")
        
# # # # # # # # # #     except FileNotFoundError:
# # # # # # # # # #         print(f"错误: 找不到输入文件 {input_file}")
# # # # # # # # # #     except json.JSONDecodeError:
# # # # # # # # # #         print(f"错误: 输入文件 {input_file} 不是有效的JSON格式")
# # # # # # # # # #     except Exception as e:
# # # # # # # # # #         print(f"处理过程中发生错误: {str(e)}")

# # # # # # # # # # if __name__ == "__main__":
# # # # # # # # # #     # 输入文件路径
# # # # # # # # # #     input_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\postgres_mysql_difference2.json"
# # # # # # # # # #     # 输出文件路径
# # # # # # # # # #     output_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\pg_mysql_conclusion.json"
    
# # # # # # # # # #     # 执行分组操作
# # # # # # # # # #     group_by_difference(input_path, output_path)
    

# # # # # # # # # #统计比例


# # # # # # # # # import json
# # # # # # # # # import os

# # # # # # # # # # 文件路径
# # # # # # # # # file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\pg_mysql_conclusion.json"
# # # # # # # # # total_questions = 309  # 问题总数

# # # # # # # # # def calculate_and_update_ratios():
# # # # # # # # #     try:
# # # # # # # # #         # 检查文件是否存在
# # # # # # # # #         if not os.path.exists(file_path):
# # # # # # # # #             print(f"错误: 文件 {file_path} 不存在")
# # # # # # # # #             return
        
# # # # # # # # #         # 读取JSON文件
# # # # # # # # #         with open(file_path, 'r', encoding='utf-8') as f:
# # # # # # # # #             data = json.load(f)
        
# # # # # # # # #         # 统计每个difference包含的问题数量
# # # # # # # # #         difference_counts = {}
# # # # # # # # #         for key, items in data.items():
# # # # # # # # #             # 确保每个条目都是列表
# # # # # # # # #             if isinstance(items, list):
# # # # # # # # #                 difference_counts[key] = len(items)
        
# # # # # # # # #         # 计算比例并更新到原数据中
# # # # # # # # #         for key in data.keys():
# # # # # # # # #             if key in difference_counts:
# # # # # # # # #                 count = difference_counts[key]
# # # # # # # # #                 ratio = count / total_questions * 100  # 转换为百分比
# # # # # # # # #                 # 检查是否已有统计信息，避免重复添加
# # # # # # # # #                 stats_exists = any(isinstance(item, dict) and "statistic" in item for item in data[key])
                
# # # # # # # # #                 if not stats_exists:
# # # # # # # # #                     # 构造只包含 count 和 ratio 字段的统计字典
# # # # # # # # #                     statistic = {
# # # # # # # # #                         "statistic": {
# # # # # # # # #                             "count": count,
# # # # # # # # #                             "ratio": round(ratio, 2)  # 保留两位小数
# # # # # # # # #                         }
# # # # # # # # #                     }
# # # # # # # # #                     # 插入到对应列表的开头
# # # # # # # # #                     data[key].insert(0, statistic)
        
# # # # # # # # #         # 将更新后的数据写回文件
# # # # # # # # #         with open(file_path, 'w', encoding='utf-8') as f:
# # # # # # # # #             json.dump(data, f, ensure_ascii=False, indent=4)
        
# # # # # # # # #         print("统计完成，已更新JSON文件。")
# # # # # # # # #         # 打印统计结果
# # # # # # # # #         print("\n统计结果:")
# # # # # # # # #         for key, count in difference_counts.items():
# # # # # # # # #             ratio = count / total_questions * 100
# # # # # # # # #             print(f"{key}: 数量 {count}，占比 {round(ratio, 2)}%")
            
# # # # # # # # #     except Exception as e:
# # # # # # # # #         print(f"处理过程中发生错误: {str(e)}")

# # # # # # # # # if __name__ == "__main__":
# # # # # # # # #     calculate_and_update_ratios()



# # # # # # # # #添加百分号


# # # # # # # # import json
# # # # # # # # import os

# # # # # # # # # 文件路径
# # # # # # # # file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\pg_mysql_conclusion.json"


# # # # # # # # def add_percent_to_ratio():
# # # # # # # #     try:
# # # # # # # #         # 检查文件是否存在
# # # # # # # #         if not os.path.exists(file_path):
# # # # # # # #             print(f"错误: 文件 {file_path} 不存在")
# # # # # # # #             return

# # # # # # # #         # 读取 JSON 文件
# # # # # # # #         with open(file_path, 'r', encoding='utf-8') as f:
# # # # # # # #             data = json.load(f)

# # # # # # # #         # 遍历 JSON 数据，寻找包含 statistic 且其下有 ratio 字段的结构
# # # # # # # #         def traverse(obj):
# # # # # # # #             if isinstance(obj, dict):
# # # # # # # #                 for key, value in obj.items():
# # # # # # # #                     if key == "statistic" and "ratio" in value:
# # # # # # # #                         # 为 ratio 值添加百分号，保留两位小数（可根据实际需求调整）
# # # # # # # #                         value["ratio"] = f"{round(value['ratio'], 2)}%"
# # # # # # # #                     else:
# # # # # # # #                         traverse(value)
# # # # # # # #             elif isinstance(obj, list):
# # # # # # # #                 for item in obj:
# # # # # # # #                     traverse(item)

# # # # # # # #         traverse(data)

# # # # # # # #         # 将更新后的数据写回文件
# # # # # # # #         with open(file_path, 'w', encoding='utf-8') as f:
# # # # # # # #             json.dump(data, f, ensure_ascii=False, indent=4)

# # # # # # # #         print("已为 ratio 字段添加百分号，文件已更新。")

# # # # # # # #     except Exception as e:
# # # # # # # #         print(f"处理过程中发生错误: {str(e)}")


# # # # # # # # if __name__ == "__main__":
# # # # # # # #     add_percent_to_ratio()



# # # # # # # #提取比例


# # # # # # # # import json
# # # # # # # # import os

# # # # # # # # # 源文件路径
# # # # # # # # source_file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\conclude\pg_mysql_conclusion.json"
# # # # # # # # # 目标文件夹路径
# # # # # # # # target_dir = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result"
# # # # # # # # # 目标文件路径
# # # # # # # # target_file_path = os.path.join(target_dir, "radio.json")

# # # # # # # # try:
# # # # # # # #     # 读取源JSON文件
# # # # # # # #     with open(source_file_path, 'r', encoding='utf-8') as f:
# # # # # # # #         data = json.load(f)
    
# # # # # # # #     # 提取比例信息和相应的列表名
# # # # # # # #     results = []
    
# # # # # # # #     # 递归查找所有包含statistic的字段及其对应的键名
# # # # # # # #     def find_ratios_with_names(obj, parent_key=None):
# # # # # # # #         if isinstance(obj, dict):
# # # # # # # #             # 遍历字典中的所有键值对
# # # # # # # #             for key, value in obj.items():
# # # # # # # #                 current_key = key if parent_key is None else f"{parent_key}.{key}"
                
# # # # # # # #                 # 如果当前值是包含statistic的字典
# # # # # # # #                 if key == "statistic" and isinstance(value, dict):
# # # # # # # #                     if "ratio" in value:
# # # # # # # #                         results.append({
# # # # # # # #                             "list_name": parent_key,  # 记录包含statistic的列表名
# # # # # # # #                             "ratio": value["ratio"],
# # # # # # # #                             "count": value.get("count")
# # # # # # # #                         })
# # # # # # # #                 # 继续递归查找
# # # # # # # #                 else:
# # # # # # # #                     find_ratios_with_names(value, current_key)
                    
# # # # # # # #         elif isinstance(obj, list):
# # # # # # # #             # 如果是列表，递归处理每个元素，并记录索引
# # # # # # # #             for index, item in enumerate(obj):
# # # # # # # #                 current_key = f"{parent_key}[{index}]" if parent_key else f"[{index}]"
# # # # # # # #                 find_ratios_with_names(item, current_key)
    
# # # # # # # #     # 执行查找
# # # # # # # #     find_ratios_with_names(data)
    
# # # # # # # #     # 生成目标JSON数据
# # # # # # # #     result_data = {
# # # # # # # #         "extracted_data": results,
# # # # # # # #         "total_extracted": len(results)
# # # # # # # #     }
    
# # # # # # # #     # 写入目标文件
# # # # # # # #     with open(target_file_path, 'w', encoding='utf-8') as f:
# # # # # # # #         json.dump(result_data, f, ensure_ascii=False, indent=4)
    
# # # # # # # #     print(f"成功提取数据，共找到 {len(results)} 条记录")
# # # # # # # #     print(f"结果已保存至：{target_file_path}")

# # # # # # # # except FileNotFoundError:
# # # # # # # #     print(f"错误：源文件不存在 - {source_file_path}")
# # # # # # # # except json.JSONDecodeError:
# # # # # # # #     print(f"错误：源文件不是有效的JSON格式 - {source_file_path}")
# # # # # # # # except Exception as e:
# # # # # # # #     print(f"发生错误：{str(e)}")



# # # # # # # #分类提取


# # # # # # # import json
# # # # # # # import os

# # # # # # # # 源文件路径
# # # # # # # source_file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\conclude\pg_mysql_conclusion.json"
# # # # # # # # 目标文件夹路径
# # # # # # # target_dir = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result"
# # # # # # # # 目标文件路径
# # # # # # # target_file_path = os.path.join(target_dir, "radio2.json")

# # # # # # # try:
# # # # # # #     # 读取源JSON文件
# # # # # # #     with open(source_file_path, 'r', encoding='utf-8') as f:
# # # # # # #         data = json.load(f)
    
# # # # # # #     # 提取count大于3的比例信息和相应的列表名
# # # # # # #     results = []
    
# # # # # # #     # 递归查找所有包含statistic的字段及其对应的键名
# # # # # # #     def find_filtered_ratios(obj, parent_key=None):
# # # # # # #         if isinstance(obj, dict):
# # # # # # #             # 遍历字典中的所有键值对
# # # # # # #             for key, value in obj.items():
# # # # # # #                 current_key = key if parent_key is None else f"{parent_key}.{key}"
                
# # # # # # #                 # 如果当前值是包含statistic的字典
# # # # # # #                 if key == "statistic" and isinstance(value, dict):
# # # # # # #                     # 检查是否包含必要字段且count大于3
# # # # # # #                     if "ratio" in value and "count" in value:
# # # # # # #                         try:
# # # # # # #                             count = int(value["count"])
# # # # # # #                             if count > 3:
# # # # # # #                                 results.append({
# # # # # # #                                     "list_name": parent_key,  # 记录包含statistic的列表名
# # # # # # #                                     "ratio": value["ratio"],
# # # # # # #                                     "count": count
# # # # # # #                                 })
# # # # # # #                         except (ValueError, TypeError):
# # # # # # #                             # 处理count无法转换为整数的情况
# # # # # # #                             print(f"警告：在 {parent_key} 中发现无效的count值: {value['count']}")
# # # # # # #                 # 继续递归查找
# # # # # # #                 else:
# # # # # # #                     find_filtered_ratios(value, current_key)
                    
# # # # # # #         elif isinstance(obj, list):
# # # # # # #             # 如果是列表，递归处理每个元素，并记录索引
# # # # # # #             for index, item in enumerate(obj):
# # # # # # #                 current_key = f"{parent_key}[{index}]" if parent_key else f"[{index}]"
# # # # # # #                 find_filtered_ratios(item, current_key)
    
# # # # # # #     # 执行查找
# # # # # # #     find_filtered_ratios(data)
    
# # # # # # #     # 生成目标JSON数据
# # # # # # #     result_data = {
# # # # # # #         "extracted_data": results,
# # # # # # #         "total_extracted": len(results),
# # # # # # #         "filter_condition": "count > 3"
# # # # # # #     }
    
# # # # # # #     # 写入目标文件
# # # # # # #     with open(target_file_path, 'w', encoding='utf-8') as f:
# # # # # # #         json.dump(result_data, f, ensure_ascii=False, indent=4)
    
# # # # # # #     print(f"成功提取数据，共找到 {len(results)} 条满足条件的记录（count > 3）")
# # # # # # #     print(f"结果已保存至：{target_file_path}")

# # # # # # # except FileNotFoundError:
# # # # # # #     print(f"错误：源文件不存在 - {source_file_path}")
# # # # # # # except json.JSONDecodeError:
# # # # # # #     print(f"错误：源文件不是有效的JSON格式 - {source_file_path}")
# # # # # # # except Exception as e:
# # # # # # #     print(f"发生错误：{str(e)}")
    
    
    
# # # # # # #画柱状图



# # # # # import json
# # # # # import os
# # # # # import matplotlib.pyplot as plt
# # # # # import numpy as np

# # # # # # 文件路径
# # # # # file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\radio2.json"

# # # # # # 设置中文字体，确保中文正常显示
# # # # # plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
# # # # # plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# # # # # try:
# # # # #     # 读取JSON数据
# # # # #     with open(file_path, 'r', encoding='utf-8') as f:
# # # # #         data = json.load(f)
    
# # # # #     # 提取列表名和比例数据
# # # # #     extracted_data = data.get('extracted_data', [])
# # # # #     if not extracted_data:
# # # # #         print("警告：未找到有效数据")
# # # # #         exit()
    
# # # # #     # 解析列表名和比例（将百分比字符串转为浮点数）
# # # # #     list_names = [item['list_name'] for item in extracted_data]
# # # # #     ratios = [float(item['ratio'].strip('%')) for item in extracted_data]  # 去除百分号并转为数字
    
# # # # #     # 创建画布（根据数据量动态调整宽度）
# # # # #     fig_width = max(12, len(list_names) * 0.8)  # 数据越多，画布越宽
# # # # #     fig, ax = plt.subplots(figsize=(fig_width, 8))
    
# # # # #     # 绘制柱状图
# # # # #     x_pos = np.arange(len(list_names))
# # # # #     bars = ax.bar(x_pos, ratios, color='#5DA5DA', edgecolor='gray', alpha=0.8)  # 使用更柔和的蓝色
    
# # # # #     # 在柱子上方添加百分比标签
# # # # #     for i, bar in enumerate(bars):
# # # # #         height = bar.get_height()
# # # # #         ax.text(
# # # # #             bar.get_x() + bar.get_width() / 2,  # x坐标（柱子中心）
# # # # #             height + 0.5,  # y坐标（柱子顶部+偏移）
# # # # #             f'{ratios[i]:.2f}%',  # 显示文本（保留两位小数）
# # # # #             ha='center',  # 水平居中
# # # # #             va='bottom',  # 垂直靠下
# # # # #             fontsize=9,
# # # # #             color='#333333'
# # # # #         )
    
# # # # #     # 设置图表标题（指定为“语法问题比例统计”）和坐标轴标签
# # # # #     ax.set_title('语法问题比例统计', fontsize=16, pad=20, fontweight='bold')
# # # # #     ax.set_xlabel('问题类型', fontsize=12, labelpad=10)  # 将x轴标签改为更贴合的“问题类型”
# # # # #     ax.set_ylabel('比例（%）', fontsize=12, labelpad=10)
    
# # # # #     # 设置x轴刻度和标签（旋转避免重叠）
# # # # #     ax.set_xticks(x_pos)
# # # # #     ax.set_xticklabels(list_names, rotation=45, ha='right', fontsize=10, rotation_mode='anchor')
    
# # # # #     # 设置y轴范围（从0开始，留10%的余量）
# # # # #     ax.set_ylim(0, max(ratios) * 1.1)
    
# # # # #     # 添加网格线（仅y轴，更清晰）
# # # # #     ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    
# # # # #     # 隐藏顶部和右侧边框，使图表更简洁
# # # # #     ax.spines['top'].set_visible(False)
# # # # #     ax.spines['right'].set_visible(False)
    
# # # # #     # 调整布局，避免标签被截断
# # # # #     plt.tight_layout()
    
# # # # #     # 保存图表（可选，如需保存可取消注释）
# # # # #     save_path = os.path.join(os.path.dirname(file_path), '语法问题比例统计.png')
# # # # #     # plt.savefig(save_path, dpi=300, bbox_inches='tight')
# # # # #     # print(f"图表已保存至：{save_path}")
    
# # # # #     # 显示图表
# # # # #     plt.show()

# # # # # except FileNotFoundError:
# # # # #     print(f"错误：文件不存在 - {file_path}")
# # # # # except json.JSONDecodeError:
# # # # #     print(f"错误：文件格式不正确，不是有效的JSON - {file_path}")
# # # # # except KeyError as e:
# # # # #     print(f"错误：数据中缺少必要字段 - {e}")
# # # # # except Exception as e:
# # # # #     print(f"发生错误：{str(e)}")


# # # # #画统计图优化
# # # # import json
# # # # import os
# # # # import matplotlib.pyplot as plt
# # # # import numpy as np

# # # # # 文件路径
# # # # file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\radio2.json"

# # # # # 设置中文字体，确保中文正常显示
# # # # plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
# # # # plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# # # # try:
# # # #     # 读取JSON数据
# # # #     with open(file_path, 'r', encoding='utf-8') as f:
# # # #         data = json.load(f)
    
# # # #     # 提取数据并检查有效性
# # # #     extracted_data = data.get('extracted_data', [])
# # # #     if not extracted_data:
# # # #         print("警告：未找到有效数据")
# # # #         exit()
    
# # # #     # 解析数据并转换比例为浮点数（方便排序）
# # # #     parsed_data = []
# # # #     for item in extracted_data:
# # # #         list_name = item['list_name']
# # # #         ratio = float(item['ratio'].strip('%'))  # 去除百分号并转为数字
# # # #         parsed_data.append({'list_name': list_name, 'ratio': ratio})
    
# # # #     # 按比例从大到小排序
# # # #     sorted_data = sorted(parsed_data, key=lambda x: x['ratio'], reverse=True)
    
# # # #     # 提取排序后的列表名和比例
# # # #     list_names = [item['list_name'] for item in sorted_data]
# # # #     ratios = [item['ratio'] for item in sorted_data]
    
# # # #     # 创建画布（根据数据量动态调整宽度）
# # # #     fig_width = max(12, len(list_names) * 0.8)  # 数据越多，画布越宽
# # # #     fig, ax = plt.subplots(figsize=(fig_width, 8))
    
# # # #     # 绘制柱状图（使用渐变色增强视觉层次）
# # # #     x_pos = np.arange(len(list_names))
# # # #     bars = ax.bar(
# # # #         x_pos, 
# # # #         ratios, 
# # # #         color=plt.cm.viridis(np.linspace(0, 0.8, len(list_names))),  # 渐变色
# # # #         edgecolor='gray', 
# # # #         alpha=0.8
# # # #     )
    
# # # #     # 在柱子上方添加百分比标签（保留两位小数）
# # # #     for i, bar in enumerate(bars):
# # # #         height = bar.get_height()
# # # #         ax.text(
# # # #             bar.get_x() + bar.get_width() / 2,  # 柱子中心x坐标
# # # #             height + 0.5,  # 柱子顶部上方
# # # #             f'{ratios[i]:.2f}%',  # 显示百分比
# # # #             ha='center', 
# # # #             va='bottom', 
# # # #             fontsize=9,
# # # #             color='#333333'
# # # #         )
    
# # # #     # 设置图表标题和坐标轴标签
# # # #     ax.set_title('语法问题比例统计', fontsize=16, pad=20, fontweight='bold')
# # # #     ax.set_xlabel('问题类型', fontsize=12, labelpad=10)
# # # #     ax.set_ylabel('比例（%）', fontsize=12, labelpad=10)
    
# # # #     # 设置x轴刻度和标签（旋转避免重叠）
# # # #     ax.set_xticks(x_pos)
# # # #     ax.set_xticklabels(list_names, rotation=45, ha='right', fontsize=10, rotation_mode='anchor')
    
# # # #     # 设置y轴范围（从0开始，留10%余量）
# # # #     ax.set_ylim(0, max(ratios) * 1.1)
    
# # # #     # 添加网格线和美化边框
# # # #     ax.yaxis.grid(True, linestyle='--', alpha=0.7)
# # # #     ax.spines['top'].set_visible(False)
# # # #     ax.spines['right'].set_visible(False)
    
# # # #     # 调整布局，避免标签截断
# # # #     plt.tight_layout()
    
# # # #     # 保存图表（可选，取消注释即可保存）
# # # #     save_path = os.path.join(os.path.dirname(file_path), '语法问题比例统计（排序后）.png')
# # # #     # plt.savefig(save_path, dpi=300, bbox_inches='tight')
# # # #     # print(f"图表已保存至：{save_path}")
    
# # # #     # 显示图表
# # # #     plt.show()

# # # # except FileNotFoundError:
# # # #     print(f"错误：文件不存在 - {file_path}")
# # # # except json.JSONDecodeError:
# # # #     print(f"错误：文件格式不正确，不是有效的JSON - {file_path}")
# # # # except KeyError as e:
# # # #     print(f"错误：数据中缺少必要字段 - {e}")
# # # # except Exception as e:
# # # #     print(f"发生错误：{str(e)}")


# # # #画柱状图再次优化
# # # # import json
# # # # import os
# # # # import matplotlib.pyplot as plt
# # # # import numpy as np

# # # # # 文件路径
# # # # file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\radio2.json"

# # # # # 设置中文字体，确保中文正常显示
# # # # plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
# # # # plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# # # # try:
# # # #     # 读取JSON数据
# # # #     with open(file_path, 'r', encoding='utf-8') as f:
# # # #         data = json.load(f)
    
# # # #     # 提取数据并检查有效性
# # # #     extracted_data = data.get('extracted_data', [])
# # # #     if not extracted_data:
# # # #         print("警告：未找到有效数据")
# # # #         exit()
    
# # # #     # 解析数据并转换比例为浮点数（方便排序）
# # # #     parsed_data = []
# # # #     for item in extracted_data:
# # # #         list_name = item['list_name']
# # # #         ratio = float(item['ratio'].strip('%'))  # 去除百分号并转为数字
# # # #         parsed_data.append({'list_name': list_name, 'ratio': ratio})
    
# # # #     # 分离"其他"类别和普通类别
# # # #     other_category = None
# # # #     normal_categories = []
# # # #     for item in parsed_data:
# # # #         if item['list_name'] == "其它(count<3)":
# # # #             other_category = item
# # # #         else:
# # # #             normal_categories.append(item)
    
# # # #     # 普通类别按比例从大到小排序
# # # #     sorted_normal = sorted(normal_categories, key=lambda x: x['ratio'], reverse=True)
    
# # # #     # 合并数据（普通类别+其他类别）
# # # #     if other_category:
# # # #         sorted_data = sorted_normal + [other_category]
# # # #     else:
# # # #         sorted_data = sorted_normal
    
# # # #     # 提取排序后的列表名和比例
# # # #     list_names = [item['list_name'] for item in sorted_data]
# # # #     ratios = [item['ratio'] for item in sorted_data]
    
# # # #     # 创建画布（根据数据量动态调整宽度）
# # # #     fig_width = max(12, len(list_names) * 0.8)  # 数据越多，画布越宽
# # # #     fig, ax = plt.subplots(figsize=(fig_width, 8))
    
# # # #     # 绘制柱状图（使用渐变色增强视觉层次）
# # # #     x_pos = np.arange(len(list_names))
# # # #     bars = ax.bar(
# # # #         x_pos, 
# # # #         ratios, 
# # # #         color=plt.cm.viridis(np.linspace(0, 0.8, len(list_names))),  # 渐变色
# # # #         edgecolor='gray', 
# # # #         alpha=0.8
# # # #     )
    
# # # #     # 为"其他"类别柱子单独设置颜色（若存在）
# # # #     if other_category:
# # # #         bars[-1].set_color('#FFA07A')  # 浅橙色突出"其他"类别
    
# # # #     # 在柱子上方添加百分比标签（保留两位小数）
# # # #     for i, bar in enumerate(bars):
# # # #         height = bar.get_height()
# # # #         ax.text(
# # # #             bar.get_x() + bar.get_width() / 2,  # 柱子中心x坐标
# # # #             height + 0.5,  # 柱子顶部上方
# # # #             f'{ratios[i]:.2f}%',  # 显示百分比
# # # #             ha='center', 
# # # #             va='bottom', 
# # # #             fontsize=9,
# # # #             color='#333333'
# # # #         )
    
# # # #     # 设置图表标题和坐标轴标签
# # # #     ax.set_title('语法问题比例统计', fontsize=16, pad=20, fontweight='bold')
# # # #     ax.set_xlabel('问题类型', fontsize=12, labelpad=10)
# # # #     ax.set_ylabel('比例（%）', fontsize=12, labelpad=10)
    
# # # #     # 设置x轴刻度和标签（旋转避免重叠）
# # # #     ax.set_xticks(x_pos)
# # # #     ax.set_xticklabels(list_names, rotation=45, ha='right', fontsize=10, rotation_mode='anchor')
    
# # # #     # 设置y轴范围（从0开始，留10%余量）
# # # #     ax.set_ylim(0, max(ratios) * 1.1)
    
# # # #     # 添加网格线和美化边框
# # # #     ax.yaxis.grid(True, linestyle='--', alpha=0.7)
# # # #     ax.spines['top'].set_visible(False)
# # # #     ax.spines['right'].set_visible(False)
    
# # # #     # 调整布局，避免标签截断
# # # #     plt.tight_layout()
    
# # # #     # 保存图表（可选，取消注释即可保存）
# # # #     save_path = os.path.join(os.path.dirname(file_path), '语法问题比例统计（排序后）.png')
# # # #     # plt.savefig(save_path, dpi=300, bbox_inches='tight')
# # # #     # print(f"图表已保存至：{save_path}")
    
# # # #     # 显示图表
# # # #     plt.show()

# # # # except FileNotFoundError:
# # # #     print(f"错误：文件不存在 - {file_path}")
# # # # except json.JSONDecodeError:
# # # #     print(f"错误：文件格式不正确，不是有效的JSON - {file_path}")
# # # # except KeyError as e:
# # # #     print(f"错误：数据中缺少必要字段 - {e}")
# # # # except Exception as e:
# # # #     print(f"发生错误：{str(e)}")

# # # #再次优化

# import json
# import os
# import matplotlib.pyplot as plt
# import numpy as np

# # 文件路径
# file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\radio2.json"
# # 输出文件夹路径（指定为conclude文件夹）
# output_dir = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\conclude"

# # 确保输出文件夹存在，不存在则创建
# os.makedirs(output_dir, exist_ok=True)

# # 设置中文字体，确保中文正常显示
# plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
# plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# try:
#     # 读取JSON数据
#     with open(file_path, 'r', encoding='utf-8') as f:
#         data = json.load(f)
    
#     # 提取数据并检查有效性
#     extracted_data = data.get('extracted_data', [])
#     if not extracted_data:
#         print("警告：未找到有效数据")
#         exit()
    
#     # 解析数据并转换比例为浮点数（方便排序）
#     parsed_data = []
#     for item in extracted_data:
#         list_name = item['list_name']
#         ratio = float(item['ratio'].strip('%'))  # 去除百分号并转为数字
#         parsed_data.append({'list_name': list_name, 'ratio': ratio})
    
#     # 分离"其他"类别和普通类别
#     other_category = None
#     normal_categories = []
#     for item in parsed_data:
#         if item['list_name'] == "其它(count<3)":
#             other_category = item
#         else:
#             normal_categories.append(item)
    
#     # 普通类别按比例从大到小排序
#     sorted_normal = sorted(normal_categories, key=lambda x: x['ratio'], reverse=True)
    
#     # 合并数据（普通类别+其他类别）
#     if other_category:
#         sorted_data = sorted_normal + [other_category]
#     else:
#         sorted_data = sorted_normal
    
#     # 提取排序后的列表名和比例
#     list_names = [item['list_name'] for item in sorted_data]
#     ratios = [item['ratio'] for item in sorted_data]
    
#     # 创建画布（根据数据量动态调整宽度）
#     fig_width = max(12, len(list_names) * 0.8)  # 数据越多，画布越宽
#     fig, ax = plt.subplots(figsize=(fig_width, 8))
    
#     # 绘制柱状图（使用渐变色增强视觉层次）
#     x_pos = np.arange(len(list_names))
#     bars = ax.bar(
#         x_pos, 
#         ratios, 
#         color=plt.cm.viridis(np.linspace(0, 0.8, len(list_names))),  # 渐变色
#         edgecolor='gray', 
#         alpha=0.8
#     )
    
#     # 为"其他"类别柱子单独设置颜色（若存在）
#     if other_category:
#         bars[-1].set_color('#FFA07A')  # 浅橙色突出"其他"类别
    
#     # 在柱子上方添加百分比标签（保留两位小数）
#     for i, bar in enumerate(bars):
#         height = bar.get_height()
#         ax.text(
#             bar.get_x() + bar.get_width() / 2,  # 柱子中心x坐标
#             height + 0.5,  # 柱子顶部上方
#             f'{ratios[i]:.2f}%',  # 显示百分比
#             ha='center', 
#             va='bottom', 
#             fontsize=9,
#             color='#333333'
#         )
    
#     # 设置图表标题和坐标轴标签
#     ax.set_title('语法问题比例统计', fontsize=16, pad=20, fontweight='bold')
#     ax.set_xlabel('问题类型', fontsize=12, labelpad=10)
#     ax.set_ylabel('比例（%）', fontsize=12, labelpad=10)
    
#     # 设置x轴刻度和标签（旋转避免重叠）
#     ax.set_xticks(x_pos)
#     ax.set_xticklabels(list_names, rotation=45, ha='right', fontsize=10, rotation_mode='anchor')
    
#     # 设置y轴范围（从0开始，留10%余量）
#     ax.set_ylim(0, max(ratios) * 1.1)
    
#     # 添加网格线和美化边框
#     ax.yaxis.grid(True, linestyle='--', alpha=0.7)
#     ax.spines['top'].set_visible(False)
#     ax.spines['right'].set_visible(False)
    
#     # 调整布局，避免标签截断
#     plt.tight_layout()
    
#     # 保存图表到指定的conclude文件夹
#     save_path = os.path.join(output_dir, '语法问题比例统计（排序后）.png')
#     plt.savefig(save_path, dpi=300, bbox_inches='tight')
#     print(f"图表已成功保存至：{save_path}")
    
#     # 显示图表
#     plt.show()

# except FileNotFoundError:
#     print(f"错误：源文件不存在 - {file_path}")
# except json.JSONDecodeError:
#     print(f"错误：源文件不是有效的JSON格式 - {file_path}")
# except KeyError as e:
#     print(f"错误：数据中缺少必要字段 - {e}")
# except Exception as e:
#     print(f"发生错误：{str(e)}")    
    
# # # # # import json
# # # # # import os
# # # # # import re

# # # # # def extract_sum_ratios_with_small_count(file_path):
# # # # #     """
# # # # #     统计JSON文件中count值小于3的所有列表的ratio总和
    
# # # # #     参数:
# # # # #         file_path: JSON文件的路径
        
# # # # #     返回:
# # # # #         符合条件的ratio总和
# # # # #     """
# # # # #     try:
# # # # #         # 检查文件是否存在
# # # # #         if not os.path.exists(file_path):
# # # # #             print(f"错误: 文件 '{file_path}' 不存在")
# # # # #             return 0
        
# # # # #         # 打开并解析JSON文件
# # # # #         with open(file_path, 'r', encoding='utf-8') as f:
# # # # #             data = json.load(f)
        
# # # # #         # 确保数据是一个字典（根据样例结构）
# # # # #         if not isinstance(data, dict):
# # # # #             print("错误: JSON数据不是一个字典")
# # # # #             return 0
        
# # # # #         # 初始化总和
# # # # #         total_ratio = 0.0
        
# # # # #         # 遍历字典中的每个键值对
# # # # #         for key, value in data.items():
# # # # #             # 检查值是否为列表且不为空
# # # # #             if isinstance(value, list) and len(value) > 0:
# # # # #                 # 检查列表第一个元素是否包含statistic
# # # # #                 first_item = value[0]
# # # # #                 if isinstance(first_item, dict) and 'statistic' in first_item:
# # # # #                     statistic = first_item['statistic']
# # # # #                     if isinstance(statistic, dict):
# # # # #                         # 检查是否包含count和ratio字段
# # # # #                         if 'count' in statistic and 'ratio' in statistic:
# # # # #                             count_value = statistic['count']
# # # # #                             ratio_value = statistic['ratio']
                            
# # # # #                             # 确保count是数字且小于3
# # # # #                             if isinstance(count_value, (int, float)) and count_value < 3:
# # # # #                                 # 提取百分比中的数值
# # # # #                                 match = re.search(r'(\d+\.\d+)%', ratio_value)
# # # # #                                 if match:
# # # # #                                     ratio_num = float(match.group(1))
# # # # #                                     total_ratio += ratio_num
# # # # #                                     print(f"列表 '{key}': count={count_value}, ratio={ratio_num}%，累计总和={total_ratio}%")
# # # # #                                 else:
# # # # #                                     print(f"警告: 列表 '{key}' 的ratio格式不正确: {ratio_value}")
        
# # # # #         return total_ratio
    
# # # # #     except json.JSONDecodeError:
# # # # #         print("错误: 无法解析JSON文件，文件格式可能不正确")
# # # # #         return 0
# # # # #     except Exception as e:
# # # # #         print(f"发生错误: {str(e)}")
# # # # #         return 0

# # # # # if __name__ == "__main__":
# # # # #     # 指定JSON文件路径
# # # # #     json_file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\conclude\pg_mysql_conclusion.json"
    
# # # # #     # 调用正确的函数名
# # # # #     result = extract_sum_ratios_with_small_count(json_file_path)
    
# # # # #     # 输出结果
# # # # #     print(f"\n所有count值小于3的列表的ratio总和为: {result}%")


# # # #去除[0]

# # # # import json
# # # # import os

# # # # def remove_suffix_from_listname(file_path):
# # # #     """
# # # #     处理JSON文件，去除所有list_name字段结尾的'[0]'后缀
# # # #     支持顶层为列表或字典的JSON结构
    
# # # #     参数:
# # # #         file_path: JSON文件的路径
        
# # # #     返回:
# # # #         处理成功返回True，否则返回False
# # # #     """
# # # #     try:
# # # #         # 检查文件是否存在
# # # #         if not os.path.exists(file_path):
# # # #             print(f"错误: 文件 '{file_path}' 不存在")
# # # #             return False
        
# # # #         # 打开并解析JSON文件
# # # #         with open(file_path, 'r', encoding='utf-8') as f:
# # # #             data = json.load(f)
        
# # # #         # 确定需要处理的数据列表
# # # #         items_to_process = []
        
# # # #         # 检查数据类型并准备要处理的项目列表
# # # #         if isinstance(data, list):
# # # #             # 如果是列表，直接使用列表中的元素
# # # #             items_to_process = data
# # # #         elif isinstance(data, dict):
# # # #             # 如果是字典，处理字典中的所有值
# # # #             # 检查字典的值是否为列表
# # # #             for key, value in data.items():
# # # #                 if isinstance(value, list):
# # # #                     items_to_process.extend(value)
# # # #                 else:
# # # #                     # 如果值不是列表，直接添加这个值（如果是字典）
# # # #                     if isinstance(value, dict):
# # # #                         items_to_process.append(value)
# # # #         else:
# # # #             print("错误: JSON数据既不是列表也不是字典")
# # # #             return False
        
# # # #         # 统计处理的条目数量
# # # #         processed_count = 0
        
# # # #         # 遍历需要处理的每个元素
# # # #         for item in items_to_process:
# # # #             # 检查是否包含list_name字段
# # # #             if isinstance(item, dict) and 'list_name' in item:
# # # #                 original_name = item['list_name']
# # # #                 # 检查是否以'[0]'结尾
# # # #                 if original_name.endswith('[0]'):
# # # #                     # 去除结尾的'[0]'
# # # #                     item['list_name'] = original_name[:-3]
# # # #                     processed_count += 1
# # # #                     print(f"已处理: {original_name} -> {item['list_name']}")
        
# # # #         # 将处理后的数据写回文件
# # # #         with open(file_path, 'w', encoding='utf-8') as f:
# # # #             json.dump(data, f, ensure_ascii=False, indent=4)
        
# # # #         print(f"处理完成，共修改了 {processed_count} 个条目")
# # # #         return True
    
# # # #     except json.JSONDecodeError:
# # # #         print("错误: 无法解析JSON文件，文件格式可能不正确")
# # # #         return False
# # # #     except Exception as e:
# # # #         print(f"发生错误: {str(e)}")
# # # #         return False

# # # # if __name__ == "__main__":
# # # #     # 指定JSON文件路径
# # # #     json_file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\radio2.json"
    
# # # #     # 执行处理
# # # #     remove_suffix_from_listname(json_file_path)

# # #统计出现的方言问题的种类

# # # import json

# # # # JSON 文件路径
# # # json_file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\conclude\pg_mysql_conclusion.json"

# # # try:
# # #     # 打开并加载 JSON 文件
# # #     with open(json_file_path, 'r', encoding='utf-8') as file:
# # #         data = json.load(file)
    
# # #     # 检查数据类型是否为字典（根据提供的JSON结构）
# # #     if isinstance(data, dict):
# # #         # 字典的键名就是方言问题类型
# # #         dialect_issues = set(data.keys())
        
# # #         # 输出结果
# # #         print(len(dialect_issues))
# # #         print(f"方言问题总共有 {len(dialect_issues)} 种")
# # #         print("具体的方言问题包括:")
# # #         for issue in sorted(dialect_issues):
# # #             print(f"- {issue}")
# # #     else:
# # #         print(f"JSON数据格式不符合预期，类型为: {type(data)}")

# # # except FileNotFoundError:
# # #     print(f"文件 {json_file_path} 未找到")
# # # except json.JSONDecodeError:
# # #     print(f"文件 {json_file_path} 不是有效的 JSON 格式")
# # # except Exception as e:
# # #     print(f"处理文件时发生错误: {e}")
    
    
# # #统计do.json中的问题数目

# # import json

# # # JSON文件路径 191
# # json_file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\run_result\do.json"

# # try:
# #     # 打开并加载JSON文件
# #     with open(json_file_path, 'r', encoding='utf-8') as file:
# #         data = json.load(file)
    
# #     # 检查数据是否为列表类型（根据提供的文件样式）
# #     if isinstance(data, list):
# #         # 统计包含"question"字段的条目数量
# #         question_count = 0
# #         for item in data:
# #             if isinstance(item, dict) and "question" in item:
# #                 question_count += 1
        
# #         # 输出结果
# #         print(f"文件中共有 {question_count} 个question")
# #     else:
# #         print(f"JSON数据格式不符合预期，类型为: {type(data)}")

# # except FileNotFoundError:
# #     print(f"文件 {json_file_path} 未找到")
# # except json.JSONDecodeError:
# #     print(f"文件 {json_file_path} 不是有效的JSON格式")
# # except Exception as e:
# #     print(f"处理文件时发生错误: {e}")
    
    
    
# #合并同类项

# import json
# import os
# import requests
# import socket
# from time import sleep
# from collections import defaultdict

# # 增加网络诊断函数
# def check_network_connection():
#     """检查网络连接和API访问能力"""
#     print("\n正在进行网络诊断...")
    
#     # 检查基本网络连接
#     try:
#         socket.create_connection(("www.baidu.com", 80), timeout=10)
#         print("✓ 基本网络连接正常")
#     except Exception as e:
#         print(f"✗ 基本网络连接失败: {str(e)}")
#         return False
    
#     # 检查API域名解析
#     api_host = "api.deepseek.com"
#     try:
#         socket.gethostbyname(api_host)
#         print(f"✓ 成功解析API域名 {api_host}")
#     except Exception as e:
#         print(f"✗ 无法解析API域名 {api_host}: {str(e)}")
#         return False
    
#     # 尝试连接API端口
#     try:
#         socket.create_connection((api_host, 443), timeout=10)
#         print(f"✓ 成功连接到 {api_host} 端口443")
#     except Exception as e:
#         print(f"✗ 无法连接到 {api_host} 端口443: {str(e)}")
#         return False
    
#     print("网络诊断通过，具备访问API的基本条件\n")
#     return True

# def load_json_file(file_path):
#     """加载JSON文件并验证有效性"""
#     if not os.path.exists(file_path):
#         print(f"错误：文件不存在 - {file_path}")
#         return None
#     if not os.path.isfile(file_path):
#         print(f"错误：不是有效文件 - {file_path}")
#         return None

#     try:
#         with open(file_path, 'r', encoding='utf-8') as f:
#             return json.load(f)
#     except json.JSONDecodeError as e:
#         print(f"错误：JSON解析失败 - {str(e)}（文件：{file_path}）")
#         return None
#     except Exception as e:
#         print(f"错误：加载文件失败 - {str(e)}（文件：{file_path}）")
#         return None

# def save_json_file(data, file_path, backup=True):
#     """保存JSON文件并创建备份"""
#     try:
#         # 创建备份文件
#         if backup and os.path.exists(file_path):
#             backup_path = f"{file_path}.bak"
#             with open(file_path, 'r', encoding='utf-8') as f_in, \
#                  open(backup_path, 'w', encoding='utf-8') as f_out:
#                 f_out.write(f_in.read())
#             print(f"已创建备份文件：{backup_path}")
        
#         # 保存处理后的数据
#         with open(file_path, 'w', encoding='utf-8') as f:
#             json.dump(data, f, ensure_ascii=False, indent=2)
#         print(f"文件已保存至：{file_path}")
#         return True
#     except Exception as e:
#         print(f"错误：保存文件失败 - {str(e)}")
#         return False

# def collect_all_differences(data):
#     """收集文件中所有出现的difference类型"""
#     if not data or not isinstance(data, list):
#         return []
    
#     all_diffs = set()
#     for item in data:
#         if "syntax_differences" in item and isinstance(item["syntax_differences"], list):
#             for diff in item["syntax_differences"]:
#                 if "difference" in diff:
#                     all_diffs.add(diff["difference"])
#     return sorted(list(all_diffs))

# def query_deepseek_reasoner_global(diff_types, max_retries=5):  # 增加重试次数
#     """调用deepseek-reasoner模型对所有差异类型进行全局分组，取粗粒度名称"""
#     API_URL = "https://api.deepseek.com/chat/completions"
#     MODEL_NAME = "deepseek-chat"
#     API_KEY = "sk-578f63b08e74438692e3ebdb42b49934"  # 替换为你的有效API密钥

#     if not API_KEY:
#         print("错误：请设置有效的API_KEY")
#         return None

#     # 检查网络连接
#     if not check_network_connection():
#         print("网络连接存在问题，无法调用API")
#         return None

#     prompt = f"""
#     任务：对以下所有PostgreSQL与MySQL的语法差异类型进行全局分组，将类似含义的合并为一组，每组取一个更粗粒度、更通用的名称作为组键。
#     差异类型列表：{diff_types}
    
#     要求：
#     1. 仅输出JSON格式，不包含任何额外文本（如解释、标记等）。
#     2. JSON为对象类型，键为合并后的粗粒度通用名称（选择更宽泛、更具包容性的名称），值为该组包含的所有相关差异类型列表。
#     3. 分组依据为语义关联性，即使不完全相同但属于同一大类的也应合并。
#     4. 组键应选择颗粒度大的名称，例如将["NULL处理语法", "排序选项", "NULLS排序处理"]合并为"NULL值排序与处理"。
#     5. 确保最终每个组的名称都具有明确的类别代表性，且各组名称之间无重叠含义。
#     """

#     # 增加请求会话和超时设置
#     session = requests.Session()
#     adapter = requests.adapters.HTTPAdapter(
#         max_retries=requests.packages.urllib3.util.retry.Retry(
#             total=3,
#             backoff_factor=1,
#             status_forcelist=[429, 500, 502, 503, 504]
#         )
#     )
#     session.mount("https://", adapter)

#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {API_KEY}"
#     }

#     payload = {
#         "model": MODEL_NAME,
#         "messages": [{"role": "user", "content": prompt}],
#         "max_tokens": 1500,
#         "temperature": 0.1
#     }

#     for retry in range(max_retries):
#         try:
#             response = session.post(
#                 API_URL,
#                 headers=headers,
#                 json=payload,
#                 timeout=30  # 延长超时时间
#             )

#             # 处理API响应状态码
#             if response.status_code == 401:
#                 print("错误：API密钥无效或已过期（401）")
#                 return None
#             if response.status_code == 429:
#                 wait_time = 2 ** retry
#                 print(f"警告：请求频率超限，{wait_time}秒后重试...")
#                 sleep(wait_time)
#                 continue
#             if response.status_code != 200:
#                 print(f"错误：API请求失败（状态码：{response.status_code}），响应：{response.text[:200]}")
#                 return None

#             # 解析模型输出
#             result = response.json()
#             if not result.get("choices") or len(result["choices"]) == 0:
#                 print("错误：API返回格式异常（无有效结果）")
#                 return None

#             model_output = result["choices"][0]["message"]["content"].strip()
#             model_output = model_output.replace("```json", "").replace("```", "").strip()
#             return json.loads(model_output)

#         except requests.exceptions.Timeout:
#             print(f"警告：请求超时，第{retry + 1}次重试...")
#         except requests.exceptions.ConnectionError as e:
#             print(f"警告：网络连接错误({str(e)})，第{retry + 1}次重试...")
#         except json.JSONDecodeError:
#             print(f"警告：模型返回非JSON格式，第{retry + 1}次重试...")
#         except Exception as e:
#             print(f"错误：请求过程异常 - {str(e)}")

#         if retry < max_retries - 1:
#             sleep(2)  # 延长重试间隔

#     print(f"错误：已达最大重试次数（{max_retries}次）")
#     return None

# def merge_similar_types_global(data, global_mapping):
#     """基于全局映射表合并所有条目中的类似差异类型"""
#     if not data or not isinstance(data, list) or not global_mapping:
#         return data

#     merged_data = []
#     total_items = len(data)

#     for item_idx, item in enumerate(data, 1):
#         print(f"\n处理第{item_idx}/{total_items}条数据...")
        
#         if "syntax_differences" not in item or not isinstance(item["syntax_differences"], list):
#             merged_data.append(item)
#             continue

#         # 按全局映射表分组差异
#         grouped_diffs = defaultdict(list)
#         for diff in item["syntax_differences"]:
#             if "difference" not in diff:
#                 grouped_diffs["其他差异"].append(diff)
#                 continue
                
#             original_diff = diff["difference"]
#             # 找到对应的粗粒度名称
#             coarse_diff = None
#             for key, values in global_mapping.items():
#                 if original_diff in values:
#                     coarse_diff = key
#                     break
#             # 如果没找到映射，使用原始值
#             if not coarse_diff:
#                 coarse_diff = original_diff
                
#             grouped_diffs[coarse_diff].append(diff)

#         # 合并同组差异详情
#         merged_differences = []
#         for coarse_type, diffs in grouped_diffs.items():
#             if len(diffs) == 1:
#                 # 单个差异项，更新为粗粒度名称
#                 merged_diff = diffs[0].copy()
#                 merged_diff["difference"] = coarse_type
#                 merged_differences.append(merged_diff)
#             else:
#                 # 多个差异项，合并详情
#                 merged_diff = {
#                     "difference": coarse_type,
#                     "detail": "; ".join([d.get("detail", "") for d in diffs if d.get("detail", "")]),
#                     "question_causing_substring": "; ".join([d.get("question_causing_substring", "") for d in diffs if d.get("question_causing_substring", "")]),
#                     "postgres_differing_substring": "; ".join([d.get("postgres_differing_substring", "") for d in diffs if d.get("postgres_differing_substring", "")]),
#                     "mysql_differing_substring": "; ".join([d.get("mysql_differing_substring", "") for d in diffs if d.get("mysql_differing_substring", "")])
#                 }
#                 merged_differences.append(merged_diff)

#         # 更新causing_part字段
#         updated_item = item.copy()
#         updated_item["syntax_differences"] = merged_differences
        
#         if "causing_part" in updated_item:
#             causing_part = updated_item["causing_part"]
#             # 替换为粗粒度名称
#             for coarse_type, original_types in global_mapping.items():
#                 for original_type in original_types:
#                     if original_type in causing_part:
#                         causing_part = causing_part.replace(original_type, coarse_type)
#             updated_item["causing_part"] = causing_part

#         merged_data.append(updated_item)
#         print(f"已完成合并，合并后差异类型：{[d['difference'] for d in merged_differences]}")

#     return merged_data

# def get_fallback_mapping(diff_types):
#     """当API调用失败时使用的备选映射方案"""
#     print("\n使用备选映射方案...")
#     # 基于常见的PostgreSQL与MySQL差异创建的默认映射
#     default_mapping = {
#         "NULL值处理与排序": [
#             "NULL值排序", "NULLS排序处理", "NULL处理语法", 
#             "排序选项", "NULL值排序处理", "NULLS排序"
#         ],
#         "标识符引用方式": [
#             "标识符引用", "标识符引用方式", "标识符引号使用",
#             "引号使用差异", "标识符命名规范"
#         ],
#         "函数与操作符差异": [
#             "函数支持差异", "字符串函数差异", "日期函数差异",
#             "聚合函数差异", "操作符使用差异"
#         ],
#         " LIMIT/OFFSET 语法": [
#             "LIMIT语法", "OFFSET用法", "分页语法差异",
#             "LIMIT与OFFSET"
#         ],
#         "数据类型差异": [
#             "类型定义差异", "数值类型差异", "字符串类型差异",
#             "日期类型差异", "特殊类型支持"
#         ]
#     }
    
#     # 为未匹配的差异类型创建"其他差异"组
#     fallback_mapping = default_mapping.copy()
#     unmatched = []
    
#     for diff in diff_types:
#         matched = False
#         for group in default_mapping.values():
#             if diff in group:
#                 matched = True
#                 break
#         if not matched:
#             unmatched.append(diff)
    
#     if unmatched:
#         fallback_mapping["其他差异"] = unmatched
    
#     return fallback_mapping

# def main():
#     # 目标文件路径
#     file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\conclude\postgres_mysql_difference.json"
    
#     # 加载数据
#     data = load_json_file(file_path)
#     if not data:
#         print("无法加载数据，程序退出")
#         return
    
#     # 收集所有差异类型
#     all_diffs = collect_all_differences(data)
#     print(f"已收集所有差异类型，共{len(all_diffs)}种：{all_diffs}")
    
#     if len(all_diffs) <= 1:
#         print("差异类型数量不足，无需合并")
#         return
    
#     # 获取全局分组映射（粗粒度）
#     print("正在调用模型进行全局差异类型分组...")
#     global_grouping = query_deepseek_reasoner_global(all_diffs)
    
#     # 如果API调用失败，使用备选方案
#     if not global_grouping:
#         print("API调用失败，尝试使用备选映射方案")
#         global_grouping = get_fallback_mapping(all_diffs)
    
#     print("全局差异类型分组结果：")
#     for coarse_type, specific_types in global_grouping.items():
#         print(f"  {coarse_type}: {specific_types}")
    
#     # 基于全局映射合并所有差异
#     merged_data = merge_similar_types_global(data, global_grouping)
    
#     # 保存结果
#     save_json_file(merged_data, file_path)

# if __name__ == "__main__":
#     main()
    
#去除标识符部分


# import json
# import os

# # 定义要处理的文件路径
# file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\conclude\postgres_mysql_difference.json"

# # 定义需要移除的difference值
# target_differences = {
#     "标识符引用",
#     "标识符引用方式",
#     "标识符引用符",
#     "标识符引用符号",
#     "标识符引用语法",
#     "条件表达式中的标识符引用",
#     "子查询中的标识符引用"
# }

# # 中文连接词和可能的分隔符
# separators = ["与", "和", "及", "、", "，", "的差异"]

# def clean_causing_part(causing_part, removed_terms):
#     """仅移除causing_part中与被删除差异完全匹配的部分"""
#     if not causing_part or not removed_terms:
#         return causing_part
    
#     # 保存处理后的部分
#     result = causing_part
    
#     # 先处理带连接词的情况
#     for term in removed_terms:
#         # 检查并移除"术语+连接词"的情况（如"标识符引用方式与"）
#         for sep in separators:
#             if f"{term}{sep}" in result:
#                 result = result.replace(f"{term}{sep}", "")
#             # 检查并移除"连接词+术语"的情况（如"与标识符引用方式"）
#             if f"{sep}{term}" in result:
#                 result = result.replace(f"{sep}{term}", "")
        
#         # 检查并移除单独出现的术语
#         if term in result:
#             result = result.replace(term, "")
    
#     # 清理可能产生的多余分隔符和空格
#     for sep in separators:
#         # 处理连续的分隔符
#         while f"{sep}{sep}" in result:
#             result = result.replace(f"{sep}{sep}", sep)
#         # 处理首尾的分隔符
#         if result.startswith(sep):
#             result = result[1:]
#         if result.endswith(sep):
#             result = result[:-1]
    
#     return result.strip()

# try:
#     # 读取JSON文件
#     with open(file_path, 'r', encoding='utf-8') as file:
#         data = json.load(file)
    
#     # 检查数据是否为列表
#     if not isinstance(data, list):
#         raise ValueError("JSON文件的根元素不是一个列表")
    
#     # 新建一个列表用于保存处理后的有效条目
#     filtered_data = []
    
#     # 处理每个条目
#     for item in data:
#         # 检查是否包含syntax_differences且为列表
#         if "syntax_differences" in item and isinstance(item["syntax_differences"], list):
#             # 记录被移除的差异术语
#             removed_terms = set()
#             for diff in item["syntax_differences"]:
#                 if "difference" in diff and diff["difference"] in target_differences:
#                     removed_terms.add(diff["difference"])
            
#             # 过滤掉需要移除的差异条目
#             filtered_diffs = [
#                 diff for diff in item["syntax_differences"]
#                 if "difference" in diff and diff["difference"] not in target_differences
#             ]
            
#             # 仅保留syntax_differences不为空的条目
#             if filtered_diffs:
#                 # 更新差异列表
#                 item["syntax_differences"] = filtered_diffs
                
#                 # 更新causing_part（如果存在）
#                 if "causing_part" in item:
#                     item["causing_part"] = clean_causing_part(item["causing_part"], removed_terms)
                
#                 filtered_data.append(item)
#         else:
#             # 对于没有syntax_differences的条目，直接保留
#             filtered_data.append(item)
    
#     # 创建备份文件
#     backup_path = f"{file_path}.backup"
#     if not os.path.exists(backup_path):
#         with open(backup_path, 'w', encoding='utf-8') as backup_file:
#             json.dump(data, backup_file, ensure_ascii=False, indent=2)
#         print(f"已创建备份文件: {backup_path}")
    
#     # 保存修改后的内容
#     with open(file_path, 'w', encoding='utf-8') as file:
#         json.dump(filtered_data, file, ensure_ascii=False, indent=2)
    
#     print(f"处理完成，已更新文件: {file_path}")
#     print(f"原始条目数量: {len(data)}，处理后条目数量: {len(filtered_data)}")

# except FileNotFoundError:
#     print(f"错误: 找不到文件 {file_path}")
# except json.JSONDecodeError:
#     print(f"错误: 文件 {file_path} 不是有效的JSON格式")
# except Exception as e:
#     print(f"处理过程中发生错误: {str(e)}")
    