# # # # # # # # # # # # # # #1.
# # # # # # # # # # # # # # import json
# # # # # # # # # # # # # # import os

# # # # # # # # # # # # # # def extract_sqlite_data():
# # # # # # # # # # # # # #         # 源文件路径
# # # # # # # # # # # # # #         source_path = r"C:\copy\code\minidev\MINIDEV\mini_dev_sqlite.json"
        
# # # # # # # # # # # # # #         # 目标文件夹和文件路径
# # # # # # # # # # # # # #         target_folder = r"C:\copy\code\minidev\MINIDEV\sqlite"
# # # # # # # # # # # # # #         target_path = os.path.join(target_folder, "sqlite.json")
        
# # # # # # # # # # # # # #         try:
# # # # # # # # # # # # # #             # 确保目标文件夹存在
# # # # # # # # # # # # # #             os.makedirs(target_folder, exist_ok=True)
            
# # # # # # # # # # # # # #             # 读取源文件
# # # # # # # # # # # # # #             with open(source_path, 'r', encoding='utf-8') as f:
# # # # # # # # # # # # # #                 source_data = json.load(f)
            
# # # # # # # # # # # # # #             # 提取需要的字段
# # # # # # # # # # # # # #             extracted_data = []
# # # # # # # # # # # # # #             # 检查源数据是否为列表
# # # # # # # # # # # # # #             if isinstance(source_data, list):
# # # # # # # # # # # # # #                 for item in source_data:
# # # # # # # # # # # # # #                     # 只提取包含所需字段的项
# # # # # # # # # # # # # #                     if all(key in item for key in ["db_id", "question", "SQL"]):
# # # # # # # # # # # # # #                         extracted_item = {
# # # # # # # # # # # # # #                             "db_id": item["db_id"],
# # # # # # # # # # # # # #                             "question": item["question"],
# # # # # # # # # # # # # #                             "SQL": item["SQL"]
# # # # # # # # # # # # # #                         }
# # # # # # # # # # # # # #                         extracted_data.append(extracted_item)
# # # # # # # # # # # # # #             else:
# # # # # # # # # # # # # #                 # 如果源数据是单个对象而不是列表
# # # # # # # # # # # # # #                 if all(key in source_data for key in ["db_id", "question", "SQL"]):
# # # # # # # # # # # # # #                     extracted_data = [{
# # # # # # # # # # # # # #                         "db_id": source_data["db_id"],
# # # # # # # # # # # # # #                         "question": source_data["question"],
# # # # # # # # # # # # # #                         "SQL": source_data["SQL"]
# # # # # # # # # # # # # #                     }]
            
# # # # # # # # # # # # # #             # 保存提取的数据到目标文件
# # # # # # # # # # # # # #             with open(target_path, 'w', encoding='utf-8') as f:
# # # # # # # # # # # # # #                 json.dump(extracted_data, f, ensure_ascii=False, indent=2)
            
# # # # # # # # # # # # # #             print(f"成功提取数据并保存到: {target_path}")
# # # # # # # # # # # # # #             print(f"共提取了 {len(extracted_data)} 条记录")
            
# # # # # # # # # # # # # #         except FileNotFoundError:
# # # # # # # # # # # # # #             print(f"错误: 源文件未找到 - {source_path}")
# # # # # # # # # # # # # #         except json.JSONDecodeError:
# # # # # # # # # # # # # #             print(f"错误: 源文件不是有效的JSON格式")
# # # # # # # # # # # # # #         except Exception as e:
# # # # # # # # # # # # # #             print(f"发生错误: {str(e)}")

# # # # # # # # # # # # # # if __name__ == "__main__":
# # # # # # # # # # # # # #         extract_sqlite_data()
    
    
    
# # # # # # # # # # # # # #2.

# # # # # # # # # # # # # import json

# # # # # # # # # # # # # # 读取 JSON 文件路径
# # # # # # # # # # # # # json_file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite.json"
# # # # # # # # # # # # # # 要保存的 SQL 文件路径
# # # # # # # # # # # # # sql_file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite.sql"

# # # # # # # # # # # # # try:
# # # # # # # # # # # # #     # 打开并读取 JSON 文件
# # # # # # # # # # # # #     with open(json_file_path, 'r', encoding='utf-8') as json_file:
# # # # # # # # # # # # #         data = json.load(json_file)

# # # # # # # # # # # # #     # 提取 "SQL" 字段内容
# # # # # # # # # # # # #     sql_contents = []
# # # # # # # # # # # # #     for item in data:
# # # # # # # # # # # # #         sql = item.get("SQL")
# # # # # # # # # # # # #         if sql:
# # # # # # # # # # # # #             sql_contents.append(sql)

# # # # # # # # # # # # #     # 将提取的 SQL 内容写入.sql 文件
# # # # # # # # # # # # #     with open(sql_file_path, 'w', encoding='utf-8') as sql_file:
# # # # # # # # # # # # #         for sql in sql_contents:
# # # # # # # # # # # # #             sql_file.write(sql + '\n')  # 每个 SQL 语句后换行，模拟类似图中的格式

# # # # # # # # # # # # #     print(f"已成功提取 SQL 并保存到 {sql_file_path}")
# # # # # # # # # # # # # except FileNotFoundError:
# # # # # # # # # # # # #     print(f"文件 {json_file_path} 未找到，请检查路径是否正确。")
# # # # # # # # # # # # # except json.JSONDecodeError:
# # # # # # # # # # # # #     print(f"解析 {json_file_path} 时发生错误，文件可能不是有效的 JSON 格式。")
# # # # # # # # # # # # # except Exception as e:
# # # # # # # # # # # # #     print(f"发生意外错误：{e}")


# # # # # # # # # # # # #3.

# # # # # # # # # # # # # import os

# # # # # # # # # # # # # def add_semicolons_to_sql():
# # # # # # # # # # # # #     # 文件路径
# # # # # # # # # # # # #     sql_file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite.sql"
    
# # # # # # # # # # # # #     try:
# # # # # # # # # # # # #         # 读取SQL文件内容
# # # # # # # # # # # # #         with open(sql_file_path, 'r', encoding='utf-8') as file:
# # # # # # # # # # # # #             content = file.read()
        
# # # # # # # # # # # # #         # 按行分割内容
# # # # # # # # # # # # #         lines = content.split('\n')
        
# # # # # # # # # # # # #         # 处理每一行，确保以分号结尾
# # # # # # # # # # # # #         processed_lines = []
# # # # # # # # # # # # #         for line in lines:
# # # # # # # # # # # # #             # 去除行首尾空白字符
# # # # # # # # # # # # #             stripped_line = line.strip()
# # # # # # # # # # # # #             if stripped_line:  # 跳过空行
# # # # # # # # # # # # #                 # 如果不以分号结尾，则添加分号
# # # # # # # # # # # # #                 if not stripped_line.endswith(';'):
# # # # # # # # # # # # #                     processed_lines.append(stripped_line + ';')
# # # # # # # # # # # # #                 else:
# # # # # # # # # # # # #                     processed_lines.append(stripped_line)
# # # # # # # # # # # # #             else:
# # # # # # # # # # # # #                 processed_lines.append(line)  # 保留空行
        
# # # # # # # # # # # # #         # 将处理后的内容写回文件
# # # # # # # # # # # # #         with open(sql_file_path, 'w', encoding='utf-8') as file:
# # # # # # # # # # # # #             file.write('\n'.join(processed_lines))
        
# # # # # # # # # # # # #         print(f"已成功处理SQL文件，确保所有语句以分号结尾：{sql_file_path}")
    
# # # # # # # # # # # # #     except FileNotFoundError:
# # # # # # # # # # # # #         print(f"错误：未找到文件 {sql_file_path}")
# # # # # # # # # # # # #     except Exception as e:
# # # # # # # # # # # # #         print(f"处理文件时发生错误：{str(e)}")

# # # # # # # # # # # # # if __name__ == "__main__":
# # # # # # # # # # # # #     add_semicolons_to_sql()
    




# # # # # # # # # # # # #4
# # # # # # # # # # # # import mysql.connector
# # # # # # # # # # # # from mysql.connector import Error
# # # # # # # # # # # # import json
# # # # # # # # # # # # import os
# # # # # # # # # # # # import re

# # # # # # # # # # # # def classify_sql_execution():
# # # # # # # # # # # #     # 配置路径信息
# # # # # # # # # # # #     sql_file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite.sql"
# # # # # # # # # # # #     true_json_path = r"C:\copy\code\minidev\MINIDEV\sqlite\true.json"
# # # # # # # # # # # #     false_json_path = r"C:\copy\code\minidev\MINIDEV\sqlite\false.json"
    
# # # # # # # # # # # #     # 数据库连接配置 - 请根据实际情况修改
# # # # # # # # # # # #     db_config = {
# # # # # # # # # # # #         'host': 'localhost',      # 数据库主机地址
# # # # # # # # # # # #         'database': 'BIRD',    # 数据库名称
# # # # # # # # # # # #         'user': 'root',  # 数据库用户名
# # # # # # # # # # # #         'password': 'xuhongming3410',  # 数据库密码
# # # # # # # # # # # #         'port': 3306              # 数据库端口，默认3306可省略
# # # # # # # # # # # #     }
    
# # # # # # # # # # # #     # 初始化结果列表
# # # # # # # # # # # #     successful_queries = []
# # # # # # # # # # # #     failed_queries = []
    
# # # # # # # # # # # #     connection = None
# # # # # # # # # # # #     cursor = None
    
# # # # # # # # # # # #     try:
# # # # # # # # # # # #         # 确保输出目录存在
# # # # # # # # # # # #         os.makedirs(os.path.dirname(true_json_path), exist_ok=True)
        
# # # # # # # # # # # #         # 读取并解析SQL文件
# # # # # # # # # # # #         with open(sql_file_path, 'r', encoding='utf-8') as f:
# # # # # # # # # # # #             sql_content = f.read()
        
# # # # # # # # # # # #         # 处理SQL内容，分割为单个语句，处理注释和空行
# # # # # # # # # # # #         # 移除单行注释
# # # # # # # # # # # #         sql_content = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
# # # # # # # # # # # #         # 分割SQL语句
# # # # # # # # # # # #         sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
# # # # # # # # # # # #         if not sql_statements:
# # # # # # # # # # # #             print("SQL文件中没有有效的SQL语句")
# # # # # # # # # # # #             return
        
# # # # # # # # # # # #         # 连接数据库
# # # # # # # # # # # #         connection = mysql.connector.connect(**db_config)
# # # # # # # # # # # #         cursor = connection.cursor()
        
# # # # # # # # # # # #         # 执行每个SQL语句
# # # # # # # # # # # #         for idx, sql in enumerate(sql_statements, 1):
# # # # # # # # # # # #             try:
# # # # # # # # # # # #                 # 执行SQL语句
# # # # # # # # # # # #                 cursor.execute(sql)
# # # # # # # # # # # #                 # 对于DML语句提交事务
# # # # # # # # # # # #                 if sql.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE', 'ALTER', 'CREATE')):
# # # # # # # # # # # #                     connection.commit()
                
# # # # # # # # # # # #                 # 记录成功执行的语句
# # # # # # # # # # # #                 successful_queries.append({
# # # # # # # # # # # #                     "id": idx,
# # # # # # # # # # # #                     "sql": sql,
# # # # # # # # # # # #                     "message": "执行成功"
# # # # # # # # # # # #                 })
# # # # # # # # # # # #                 print(f"语句 {idx} 执行成功")
                
# # # # # # # # # # # #             except Error as e:
# # # # # # # # # # # #                 # 记录执行失败的语句及错误信息
# # # # # # # # # # # #                 failed_queries.append({
# # # # # # # # # # # #                     "id": idx,
# # # # # # # # # # # #                     "sql": sql,
# # # # # # # # # # # #                     "error": str(e),
# # # # # # # # # # # #                     "error_code": e.errno
# # # # # # # # # # # #                 })
# # # # # # # # # # # #                 print(f"语句 {idx} 执行失败: {str(e)}")
# # # # # # # # # # # #                 # 回滚事务以防影响后续执行
# # # # # # # # # # # #                 if connection:
# # # # # # # # # # # #                     connection.rollback()
        
# # # # # # # # # # # #         # 保存成功执行的语句
# # # # # # # # # # # #         with open(true_json_path, 'w', encoding='utf-8') as f:
# # # # # # # # # # # #             json.dump(successful_queries, f, ensure_ascii=False, indent=2)
        
# # # # # # # # # # # #         # 保存执行失败的语句
# # # # # # # # # # # #         with open(false_json_path, 'w', encoding='utf-8') as f:
# # # # # # # # # # # #             json.dump(failed_queries, f, ensure_ascii=False, indent=2)
        
# # # # # # # # # # # #         print(f"\n处理完成！")
# # # # # # # # # # # #         print(f"成功执行的语句: {len(successful_queries)} 条，已保存到 {true_json_path}")
# # # # # # # # # # # #         print(f"执行失败的语句: {len(failed_queries)} 条，已保存到 {false_json_path}")
        
# # # # # # # # # # # #     except FileNotFoundError:
# # # # # # # # # # # #         print(f"错误：找不到SQL文件 - {sql_file_path}")
# # # # # # # # # # # #     except Error as e:
# # # # # # # # # # # #         print(f"数据库连接错误：{str(e)}")
# # # # # # # # # # # #     except Exception as e:
# # # # # # # # # # # #         print(f"发生意外错误：{str(e)}")
# # # # # # # # # # # #     finally:
# # # # # # # # # # # #         # 确保资源正确释放
# # # # # # # # # # # #         if cursor:
# # # # # # # # # # # #             cursor.close()
# # # # # # # # # # # #         if connection and connection.is_connected():
# # # # # # # # # # # #             connection.close()

# # # # # # # # # # # # if __name__ == "__main__":
# # # # # # # # # # # #     classify_sql_execution()
    
    
# # # # # # # # # # # #5.


# # # # # # # # # # # import json
# # # # # # # # # # # import os

# # # # # # # # # # # def extract_matching_sql_dicts():
# # # # # # # # # # #     # 文件路径配置
# # # # # # # # # # #     sqlite_json_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite.json"
# # # # # # # # # # #     true_json_path = r"C:\copy\code\minidev\MINIDEV\sqlite\true.json"
# # # # # # # # # # #     false_json_path = r"C:\copy\code\minidev\MINIDEV\sqlite\false.json"
# # # # # # # # # # #     result_folder = r"C:\copy\code\minidev\MINIDEV\sqlite\result"
# # # # # # # # # # #     do_json_path = os.path.join(result_folder, "do.json")
# # # # # # # # # # #     undo_json_path = os.path.join(result_folder, "undo.json")
    
# # # # # # # # # # #     try:
# # # # # # # # # # #         # 确保结果文件夹存在
# # # # # # # # # # #         os.makedirs(result_folder, exist_ok=True)
        
# # # # # # # # # # #         # 读取sqlite.json数据
# # # # # # # # # # #         with open(sqlite_json_path, 'r', encoding='utf-8') as f:
# # # # # # # # # # #             sqlite_data = json.load(f)
# # # # # # # # # # #             if not isinstance(sqlite_data, list):
# # # # # # # # # # #                 print("错误: sqlite.json中的数据不是列表格式")
# # # # # # # # # # #                 return
        
# # # # # # # # # # #         # 读取true.json并提取sql语句集合
# # # # # # # # # # #         with open(true_json_path, 'r', encoding='utf-8') as f:
# # # # # # # # # # #             true_data = json.load(f)
# # # # # # # # # # #             true_sqls = {item['sql'].strip() for item in true_data if 'sql' in item}
        
# # # # # # # # # # #         # 读取false.json并提取sql语句集合
# # # # # # # # # # #         with open(false_json_path, 'r', encoding='utf-8') as f:
# # # # # # # # # # #             false_data = json.load(f)
# # # # # # # # # # #             false_sqls = {item['sql'].strip() for item in false_data if 'sql' in item}
        
# # # # # # # # # # #         # 筛选匹配的数据
# # # # # # # # # # #         do_data = []  # 与true.json中的sql匹配
# # # # # # # # # # #         undo_data = []  # 与false.json中的sql匹配
        
# # # # # # # # # # #         for item in sqlite_data:
# # # # # # # # # # #             if 'SQL' in item:
# # # # # # # # # # #                 sql_content = item['SQL'].strip()
# # # # # # # # # # #                 if sql_content in true_sqls:
# # # # # # # # # # #                     do_data.append(item)
# # # # # # # # # # #                 if sql_content in false_sqls:
# # # # # # # # # # #                     undo_data.append(item)
        
# # # # # # # # # # #         # 保存结果
# # # # # # # # # # #         with open(do_json_path, 'w', encoding='utf-8') as f:
# # # # # # # # # # #             json.dump(do_data, f, ensure_ascii=False, indent=2)
        
# # # # # # # # # # #         with open(undo_json_path, 'w', encoding='utf-8') as f:
# # # # # # # # # # #             json.dump(undo_data, f, ensure_ascii=False, indent=2)
        
# # # # # # # # # # #         print(f"处理完成:")
# # # # # # # # # # #         print(f"- 与true.json匹配的记录数: {len(do_data)}, 已保存到 {do_json_path}")
# # # # # # # # # # #         print(f"- 与false.json匹配的记录数: {len(undo_data)}, 已保存到 {undo_json_path}")
        
# # # # # # # # # # #     except FileNotFoundError as e:
# # # # # # # # # # #         print(f"错误: 未找到文件 - {e.filename}")
# # # # # # # # # # #     except json.JSONDecodeError as e:
# # # # # # # # # # #         print(f"错误: JSON解析失败 - {e}")
# # # # # # # # # # #     except Exception as e:
# # # # # # # # # # #         print(f"发生意外错误: {str(e)}")

# # # # # # # # # # # if __name__ == "__main__":
# # # # # # # # # # #     extract_matching_sql_dicts()
        
        

# # # # # # # # # # #6.


# # # # # # # # # # import json
# # # # # # # # # # import os

# # # # # # # # # # def rename_json_key(file_path, old_key, new_key):
# # # # # # # # # #         """
# # # # # # # # # #         重命名JSON文件中的指定键
        
# # # # # # # # # #         参数:
# # # # # # # # # #             file_path (str): JSON文件路径
# # # # # # # # # #             old_key (str): 要替换的旧键名
# # # # # # # # # #             new_key (str): 替换后的新键名
# # # # # # # # # #         """
# # # # # # # # # #         # 检查文件是否存在
# # # # # # # # # #         if not os.path.exists(file_path):
# # # # # # # # # #             print(f"错误: 文件 '{file_path}' 不存在")
# # # # # # # # # #             return
        
# # # # # # # # # #         try:
# # # # # # # # # #             # 读取JSON文件
# # # # # # # # # #             with open(file_path, 'r', encoding='utf-8') as file:
# # # # # # # # # #                 data = json.load(file)
            
# # # # # # # # # #             # 递归替换键名的函数
# # # # # # # # # #             def replace_key(obj):
# # # # # # # # # #                 if isinstance(obj, dict):
# # # # # # # # # #                     new_obj = {}
# # # # # # # # # #                     for key, value in obj.items():
# # # # # # # # # #                         # 替换键名，如果匹配的话
# # # # # # # # # #                         if key == old_key:
# # # # # # # # # #                             new_obj[new_key] = replace_key(value)
# # # # # # # # # #                         else:
# # # # # # # # # #                             new_obj[key] = replace_key(value)
# # # # # # # # # #                     return new_obj
# # # # # # # # # #                 elif isinstance(obj, list):
# # # # # # # # # #                     # 如果是列表，递归处理每个元素
# # # # # # # # # #                     return [replace_key(item) for item in obj]
# # # # # # # # # #                 else:
# # # # # # # # # #                     # 其他类型直接返回
# # # # # # # # # #                     return obj
            
# # # # # # # # # #             # 执行替换
# # # # # # # # # #             modified_data = replace_key(data)
            
# # # # # # # # # #             # 创建备份文件
# # # # # # # # # #             backup_path = f"{file_path}.backup"
# # # # # # # # # #             with open(backup_path, 'w', encoding='utf-8') as backup_file:
# # # # # # # # # #                 json.dump(data, backup_file, ensure_ascii=False, indent=4)
# # # # # # # # # #             print(f"已创建备份文件: {backup_path}")
            
# # # # # # # # # #             # 写入修改后的数据
# # # # # # # # # #             with open(file_path, 'w', encoding='utf-8') as file:
# # # # # # # # # #                 json.dump(modified_data, file, ensure_ascii=False, indent=4)
            
# # # # # # # # # #             print(f"成功将键 '{old_key}' 替换为 '{new_key}'")
            
# # # # # # # # # #         except json.JSONDecodeError:
# # # # # # # # # #             print(f"错误: 文件 '{file_path}' 不是有效的JSON格式")
# # # # # # # # # #         except Exception as e:
# # # # # # # # # #             print(f"处理文件时发生错误: {str(e)}")

# # # # # # # # # # if __name__ == "__main__":
# # # # # # # # # #         # 目标文件路径
# # # # # # # # # #         file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\undo.json"
# # # # # # # # # #         # 要替换的旧键和新键
# # # # # # # # # #         old_key = "SQL"
# # # # # # # # # #         new_key = "sqlite"
        
# # # # # # # # # #         # 执行替换操作
# # # # # # # # # #         rename_json_key(file_path, old_key, new_key)
    
    
    
# # # # # # # # # #7.



# # # # # # # # # import json
# # # # # # # # # import os

# # # # # # # # # def main():
# # # # # # # # #     # 定义文件路径
# # # # # # # # #     pg_json_path = r"C:\copy\code\minidev\MINIDEV\mysql\mysql1.json"
# # # # # # # # #     undo_json_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\undo.json"
    
# # # # # # # # #     try:
# # # # # # # # #         # 读取pg.json文件
# # # # # # # # #         with open(pg_json_path, 'r', encoding='utf-8') as f:
# # # # # # # # #             pg_data = json.load(f)
        
# # # # # # # # #         # 读取undo.json文件
# # # # # # # # #         with open(undo_json_path, 'r', encoding='utf-8') as f:
# # # # # # # # #             undo_data = json.load(f)
            
# # # # # # # # #     except FileNotFoundError as e:
# # # # # # # # #         print(f"错误：找不到文件 - {e.filename}")
# # # # # # # # #         return
# # # # # # # # #     except json.JSONDecodeError:
# # # # # # # # #         print("错误：文件不是有效的JSON格式")
# # # # # # # # #         return
# # # # # # # # #     except Exception as e:
# # # # # # # # #         print(f"读取文件时发生错误：{str(e)}")
# # # # # # # # #         return
    
# # # # # # # # #     # 创建pg数据中问题到SQL的映射
# # # # # # # # #     question_to_sql = {}
# # # # # # # # #     for item in pg_data:
# # # # # # # # #         if "question" in item and "SQL" in item:
# # # # # # # # #             question_to_sql[item["question"]] = item["SQL"]
    
# # # # # # # # #     # 统计添加的postgres数量
# # # # # # # # #     added_count = 0
    
# # # # # # # # #     # 处理undo数据，添加postgres字段
# # # # # # # # #     for item in undo_data:
# # # # # # # # #         if "question" in item and item["question"] in question_to_sql:
# # # # # # # # #             # 只添加不存在的postgres字段
# # # # # # # # #             if "postgres" not in item:
# # # # # # # # #                 item["postgres"] = question_to_sql[item["question"]]
# # # # # # # # #                 added_count += 1
    
# # # # # # # # #     try:
# # # # # # # # #         # 保存修改后的undo.json
# # # # # # # # #         with open(undo_json_path, 'w', encoding='utf-8') as f:
# # # # # # # # #             json.dump(undo_data, f, ensure_ascii=False, indent=4)
        
# # # # # # # # #         print(f"操作完成，共向 {undo_json_path} 添加了 {added_count} 个postgres字段")
        
# # # # # # # # #     except Exception as e:
# # # # # # # # #         print(f"写入文件时发生错误：{str(e)}")
# # # # # # # # #         return

# # # # # # # # # if __name__ == "__main__":
# # # # # # # # #     main()
    
    
    
# # # # # # # # #13.修正postgres


# # # # # # # # import json
# # # # # # # # import os

# # # # # # # # def load_json_file(file_path):
# # # # # # # #     """加载JSON文件并返回数据"""
# # # # # # # #     try:
# # # # # # # #         with open(file_path, 'r', encoding='utf-8') as f:
# # # # # # # #             return json.load(f)
# # # # # # # #     except FileNotFoundError:
# # # # # # # #         print(f"错误：文件 {file_path} 未找到")
# # # # # # # #         return None
# # # # # # # #     except json.JSONDecodeError:
# # # # # # # #         print(f"错误：文件 {file_path} 不是有效的JSON格式")
# # # # # # # #         return None
# # # # # # # #     except Exception as e:
# # # # # # # #         print(f"加载文件 {file_path} 时发生错误：{str(e)}")
# # # # # # # #         return None

# # # # # # # # def save_json_file(data, file_path):
# # # # # # # #     """保存数据到JSON文件"""
# # # # # # # #     try:
# # # # # # # #         # 创建目录（如果不存在）
# # # # # # # #         os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
# # # # # # # #         with open(file_path, 'w', encoding='utf-8') as f:
# # # # # # # #             json.dump(data, f, ensure_ascii=False, indent=4)
# # # # # # # #         print(f"文件已成功保存到 {file_path}")
# # # # # # # #         return True
# # # # # # # #     except Exception as e:
# # # # # # # #         print(f"保存文件 {file_path} 时发生错误：{str(e)}")
# # # # # # # #         return False

# # # # # # # # def update_postgres_statements(mysql_file, undo_file):
# # # # # # # #     """
# # # # # # # #     找到两个JSON文件中question相同的条目，
# # # # # # # #     将undo.json中的postgres语句替换为mysql1.json中的SQL语句
# # # # # # # #     """
# # # # # # # #     # 加载两个JSON文件
# # # # # # # #     mysql_data = load_json_file(mysql_file)
# # # # # # # #     undo_data = load_json_file(undo_file)
    
# # # # # # # #     if not mysql_data or not undo_data:
# # # # # # # #         return False
    
# # # # # # # #     # 创建mysql数据中question到SQL的映射字典
# # # # # # # #     question_to_sql = {}
# # # # # # # #     for item in mysql_data:
# # # # # # # #         # 检查是否包含所需的嵌套结构
# # # # # # # #         if "question" in item and isinstance(item["question"], dict) and "question" in item["question"] and "SQL" in item:
# # # # # # # #             question = item["question"]["question"]
# # # # # # # #             sql = item["SQL"]
# # # # # # # #             question_to_sql[question] = sql
    
# # # # # # # #     # 统计匹配和更新的数量
# # # # # # # #     matched_count = 0
# # # # # # # #     updated_count = 0
    
# # # # # # # #     # 处理undo数据
# # # # # # # #     for item in undo_data:
# # # # # # # #         if "question" in item and "postgres" in item:
# # # # # # # #             question = item["question"]
# # # # # # # #             # 检查是否有匹配的question
# # # # # # # #             if question in question_to_sql:
# # # # # # # #                 matched_count += 1
# # # # # # # #                 # 只有当值不同时才更新
# # # # # # # #                 if item["postgres"] != question_to_sql[question]:
# # # # # # # #                     item["postgres"] = question_to_sql[question]
# # # # # # # #                     updated_count += 1
    
# # # # # # # #     print(f"找到 {matched_count} 个匹配的question")
# # # # # # # #     print(f"更新了 {updated_count} 个postgres语句")
    
# # # # # # # #     # 保存更新后的undo数据
# # # # # # # #     return save_json_file(undo_data, undo_file)

# # # # # # # # if __name__ == "__main__":
# # # # # # # #     # 定义文件路径
# # # # # # # #     mysql_file_path = r"C:\copy\code\minidev\MINIDEV\mysql\mysql1.json"
# # # # # # # #     undo_file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\undo.json"
    
# # # # # # # #     # 执行更新操作
# # # # # # # #     print("开始更新postgres语句...")
# # # # # # # #     success = update_postgres_statements(mysql_file_path, undo_file_path)
    
# # # # # # # #     if success:
# # # # # # # #         print("操作完成！")
# # # # # # # #     else:
# # # # # # # #         print("操作失败！")


# # # # # # # #14



# # # # # # # import json
# # # # # # # import os
# # # # # # # import re

# # # # # # # def load_json(file_path):
# # # # # # #     """加载JSON文件内容，增加详细错误信息"""
# # # # # # #     try:
# # # # # # #         with open(file_path, 'r', encoding='utf-8') as f:
# # # # # # #             return json.load(f)
# # # # # # #     except FileNotFoundError:
# # # # # # #         print(f"错误：文件不存在 - {file_path}")
# # # # # # #         return None
# # # # # # #     except json.JSONDecodeError as e:
# # # # # # #         print(f"错误：JSON格式解析失败 - {file_path}，位置：{e.pos}，原因：{e.msg}")
# # # # # # #         return None
# # # # # # #     except Exception as e:
# # # # # # #         print(f"加载文件 {file_path} 出错: {str(e)}")
# # # # # # #         return None

# # # # # # # def save_json(data, file_path):
# # # # # # #     """保存数据到JSON文件"""
# # # # # # #     try:
# # # # # # #         os.makedirs(os.path.dirname(file_path), exist_ok=True)
# # # # # # #         with open(file_path, 'w', encoding='utf-8') as f:
# # # # # # #             json.dump(data, f, ensure_ascii=False, indent=4)
# # # # # # #         print(f"已成功保存到 {file_path}")
# # # # # # #         return True
# # # # # # #     except Exception as e:
# # # # # # #         print(f"保存文件 {file_path} 出错: {str(e)}")
# # # # # # #         return False

# # # # # # # def normalize_text(text):
# # # # # # #     """标准化文本（去除空格、标点、大小写统一），提高匹配成功率"""
# # # # # # #     if not text:
# # # # # # #         return ""
# # # # # # #     # 去除多余空格和标点
# # # # # # #     text = re.sub(r'\s+', ' ', text).strip()
# # # # # # #     text = re.sub(r'[^\w\s]', '', text)
# # # # # # #     # 转为小写
# # # # # # #     return text.lower()

# # # # # # # def add_sql_to_undo():
# # # # # # #     # 定义文件路径
# # # # # # #     mysql_path = r"C:\copy\code\minidev\MINIDEV\mysql\mysql1.json"
# # # # # # #     undo_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\undo.json"
    
# # # # # # #     # 加载两个JSON文件
# # # # # # #     mysql_data = load_json(mysql_path)
# # # # # # #     undo_data = load_json(undo_path)
    
# # # # # # #     if not mysql_data or not undo_data:
# # # # # # #         print("无法继续处理，数据加载失败")
# # # # # # #         return False

# # # # # # #     # 验证数据格式
# # # # # # #     if not isinstance(mysql_data, list):
# # # # # # #         print(f"错误：mysql1.json 不是列表格式（实际格式：{type(mysql_data)}）")
# # # # # # #         return False
# # # # # # #     if not isinstance(undo_data, list):
# # # # # # #         print(f"错误：undo.json 不是列表格式（实际格式：{type(undo_data)}）")
# # # # # # #         return False

# # # # # # #     # 创建问题到SQL的映射（同时存储原始问题用于日志）
# # # # # # #     question_sql_map = {}
# # # # # # #     raw_questions = []  # 存储mysql1.json中的原始问题用于排查
# # # # # # #     for idx, item in enumerate(mysql_data):
# # # # # # #         try:
# # # # # # #             # 兼容嵌套和非嵌套的question结构
# # # # # # #             if "question" in item:
# # # # # # #                 if isinstance(item["question"], dict) and "question" in item["question"]:
# # # # # # #                     raw_question = item["question"]["question"]
# # # # # # #                 else:
# # # # # # #                     raw_question = item["question"]  # 非嵌套结构兼容
                
# # # # # # #                 if not isinstance(raw_question, str):
# # # # # # #                     print(f"mysql1.json 第{idx+1}条：question不是字符串（类型：{type(raw_question)}）")
# # # # # # #                     continue
                
# # # # # # #                 sql = item.get("SQL")
# # # # # # #                 if not sql or not isinstance(sql, str):
# # # # # # #                     print(f"mysql1.json 第{idx+1}条：SQL不存在或不是字符串")
# # # # # # #                     continue
                
# # # # # # #                 normalized_question = normalize_text(raw_question)
# # # # # # #                 question_sql_map[normalized_question] = {
# # # # # # #                     "sql": sql,
# # # # # # #                     "raw_question": raw_question
# # # # # # #                 }
# # # # # # #                 raw_questions.append(raw_question)
        
# # # # # # #         except Exception as e:
# # # # # # #             print(f"mysql1.json 第{idx+1}条处理失败：{str(e)}")

# # # # # # #     print(f"从mysql1.json中提取了 {len(question_sql_map)} 个有效(question, SQL)对")
# # # # # # #     if len(question_sql_map) == 0:
# # # # # # #         print("警告：未从mysql1.json中提取到任何有效数据，请检查其格式")
# # # # # # #         return False

# # # # # # #     # 处理undo.json中的每个条目
# # # # # # #     total_matched = 0
# # # # # # #     total_added = 0
# # # # # # #     undo_questions = []  # 存储undo.json中的原始问题用于排查

# # # # # # #     for idx, item in enumerate(undo_data):
# # # # # # #         try:
# # # # # # #             if "question" not in item:
# # # # # # #                 print(f"undo.json 第{idx+1}条：缺少question字段")
# # # # # # #                 continue
            
# # # # # # #             raw_question = item["question"]
# # # # # # #             if not isinstance(raw_question, str):
# # # # # # #                 print(f"undo.json 第{idx+1}条：question不是字符串（类型：{type(raw_question)}）")
# # # # # # #                 continue
            
# # # # # # #             undo_questions.append(raw_question)
# # # # # # #             normalized_question = normalize_text(raw_question)

# # # # # # #             # 检查是否有匹配的问题
# # # # # # #             if normalized_question in question_sql_map:
# # # # # # #                 total_matched += 1
# # # # # # #                 matched_sql = question_sql_map[normalized_question]["sql"]
# # # # # # #                 matched_raw = question_sql_map[normalized_question]["raw_question"]

# # # # # # #                 # 检查是否已经存在SQL键
# # # # # # #                 if "SQL" not in item:
# # # # # # #                     item["SQL"] = matched_sql
# # # # # # #                     total_added += 1
# # # # # # #                     print(f"匹配成功：undo第{idx+1}条 与 mysql1中问题匹配\n"
# # # # # # #                           f"原始问题：{raw_question[:50]}...\n"
# # # # # # #                           f"匹配的mysql问题：{matched_raw[:50]}...")
# # # # # # #                 else:
# # # # # # #                     print(f"注意：undo第{idx+1}条已存在SQL键，未修改")
        
# # # # # # #         except Exception as e:
# # # # # # #             print(f"undo.json 第{idx+1}条处理失败：{str(e)}")

# # # # # # #     # 输出排查信息
# # # # # # #     print("\n==== 匹配排查信息 ====")
# # # # # # #     print(f"mysql1.json中共有 {len(raw_questions)} 个问题")
# # # # # # #     print(f"undo.json中共有 {len(undo_questions)} 个问题")
# # # # # # #     print(f"归一化后匹配成功：{total_matched} 个")
# # # # # # #     print(f"新增SQL键值对：{total_added} 个")

# # # # # # #     # 保存更新后的undo.json
# # # # # # #     return save_json(undo_data, undo_path)

# # # # # # # if __name__ == "__main__":
# # # # # # #     print("开始执行添加SQL键值对操作...")
# # # # # # #     result = add_sql_to_undo()
# # # # # # #     if result:
# # # # # # #         print("操作成功完成")
# # # # # # #     else:
# # # # # # #         print("操作失败")
    
    
    
# # # # # # import json
# # # # # # import os

# # # # # # def load_json(file_path):
# # # # # #     """加载JSON文件内容"""
# # # # # #     try:
# # # # # #         with open(file_path, 'r', encoding='utf-8') as f:
# # # # # #             return json.load(f)
# # # # # #     except FileNotFoundError:
# # # # # #         print(f"错误：文件 {file_path} 未找到")
# # # # # #         return None
# # # # # #     except json.JSONDecodeError:
# # # # # #         print(f"错误：文件 {file_path} 不是有效的JSON格式")
# # # # # #         return None
# # # # # #     except Exception as e:
# # # # # #         print(f"加载文件 {file_path} 时发生错误：{str(e)}")
# # # # # #         return None

# # # # # # def save_json(data, file_path):
# # # # # #     """保存数据到JSON文件"""
# # # # # #     try:
# # # # # #         # 确保目录存在
# # # # # #         os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
# # # # # #         with open(file_path, 'w', encoding='utf-8') as f:
# # # # # #             json.dump(data, f, ensure_ascii=False, indent=4)
# # # # # #         print(f"文件已成功保存到 {file_path}")
# # # # # #         return True
# # # # # #     except Exception as e:
# # # # # #         print(f"保存文件 {file_path} 时发生错误：{str(e)}")
# # # # # #         return False

# # # # # # def remove_postgres_fields(json_file_path):
# # # # # #     """移除JSON文件中所有条目的"postgres"字段"""
# # # # # #     # 加载JSON数据
# # # # # #     data = load_json(json_file_path)
# # # # # #     if data is None:
# # # # # #         return False
    
# # # # # #     # 检查数据是否为列表
# # # # # #     if not isinstance(data, list):
# # # # # #         print("错误：JSON数据不是列表格式")
# # # # # #         return False
    
# # # # # #     # 统计移除的字段数量
# # # # # #     removed_count = 0
    
# # # # # #     # 遍历每个条目并移除"postgres"字段
# # # # # #     for item in data:
# # # # # #         if isinstance(item, dict) and "postgres" in item:
# # # # # #             del item["postgres"]
# # # # # #             removed_count += 1
    
# # # # # #     print(f"共移除了 {removed_count} 个 'postgres' 字段")
    
# # # # # #     # 保存修改后的数据
# # # # # #     return save_json(data, json_file_path)

# # # # # # if __name__ == "__main__":
# # # # # #     # 定义目标文件路径
# # # # # #     target_file = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\undo.json"
    
# # # # # #     print(f"开始移除 {target_file} 中的 'postgres' 字段...")
# # # # # #     success = remove_postgres_fields(target_file)
    
# # # # # #     if success:
# # # # # #         print("操作完成！")
# # # # # #     else:
# # # # # #         print("操作失败！")




# # # # # # import json
# # # # # # import os

# # # # # # def load_json(file_path):
# # # # # #     """加载JSON文件内容"""
# # # # # #     try:
# # # # # #         with open(file_path, 'r', encoding='utf-8') as f:
# # # # # #             return json.load(f)
# # # # # #     except FileNotFoundError:
# # # # # #         print(f"错误：文件 {file_path} 未找到")
# # # # # #         return None
# # # # # #     except json.JSONDecodeError:
# # # # # #         print(f"错误：文件 {file_path} 不是有效的JSON格式")
# # # # # #         return None
# # # # # #     except Exception as e:
# # # # # #         print(f"加载文件 {file_path} 时发生错误：{str(e)}")
# # # # # #         return None

# # # # # # def save_json(data, file_path):
# # # # # #     """保存数据到JSON文件"""
# # # # # #     try:
# # # # # #         # 确保目录存在
# # # # # #         os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
# # # # # #         with open(file_path, 'w', encoding='utf-8') as f:
# # # # # #             json.dump(data, f, ensure_ascii=False, indent=4)
# # # # # #         print(f"文件已成功保存到 {file_path}")
# # # # # #         return True
# # # # # #     except Exception as e:
# # # # # #         print(f"保存文件 {file_path} 时发生错误：{str(e)}")
# # # # # #         return False

# # # # # # def rename_key_in_json(json_data, old_key, new_key):
# # # # # #     """
# # # # # #     递归地将JSON数据中的旧键名改为新键名
# # # # # #     """
# # # # # #     if isinstance(json_data, dict):
# # # # # #         # 处理字典类型
# # # # # #         new_dict = {}
# # # # # #         for key, value in json_data.items():
# # # # # #             if key == old_key:
# # # # # #                 # 替换键名
# # # # # #                 new_dict[new_key] = rename_key_in_json(value, old_key, new_key)
# # # # # #             else:
# # # # # #                 new_dict[key] = rename_key_in_json(value, old_key, new_key)
# # # # # #         return new_dict
# # # # # #     elif isinstance(json_data, list):
# # # # # #         # 处理列表类型
# # # # # #         return [rename_key_in_json(item, old_key, new_key) for item in json_data]
# # # # # #     else:
# # # # # #         # 其他类型直接返回
# # # # # #         return json_data

# # # # # # def rename_sql_to_mysql(json_file_path):
# # # # # #     """将JSON文件中的"SQL"键名改为"mysql" """
# # # # # #     # 加载JSON数据
# # # # # #     data = load_json(json_file_path)
# # # # # #     if data is None:
# # # # # #         return False
    
# # # # # #     # 统计修改的键数量
# # # # # #     count = 0
    
# # # # # #     # 定义一个辅助函数来计数修改的键
# # # # # #     def count_rename(json_data, old_key, new_key):
# # # # # #         nonlocal count
# # # # # #         if isinstance(json_data, dict):
# # # # # #             if old_key in json_data:
# # # # # #                 count += 1
# # # # # #             # 递归处理所有值
# # # # # #             for value in json_data.values():
# # # # # #                 count_rename(value, old_key, new_key)
# # # # # #         elif isinstance(json_data, list):
# # # # # #             for item in json_data:
# # # # # #                 count_rename(item, old_key, new_key)
    
# # # # # #     # 先计数有多少个键需要修改
# # # # # #     count_rename(data, "SQL", "mysql")
    
# # # # # #     # 执行键名修改
# # # # # #     modified_data = rename_key_in_json(data, "SQL", "mysql")
    
# # # # # #     print(f"共修改了 {count} 个 'SQL' 键名为 'mysql'")
    
# # # # # #     # 保存修改后的数据
# # # # # #     return save_json(modified_data, json_file_path)

# # # # # # if __name__ == "__main__":
# # # # # #     # 定义目标文件路径
# # # # # #     target_file = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\undo.json"
    
# # # # # #     print(f"开始将 {target_file} 中的 'SQL' 键名改为 'mysql'...")
# # # # # #     success = rename_sql_to_mysql(target_file)
    
# # # # # #     if success:
# # # # # #         print("操作完成！")
# # # # # #     else:
# # # # # #         print("操作失败！")



# # # # # #15.



# # import json
# # import requests
# # import os
# # from time import sleep


# # def load_undo_json(file_path):
# #     """加载待分析的undo.json文件，增加文件路径验证"""
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
# #         print(f"错误：JSON解析失败 - {str(e)}（文件：{file_path}）")
# #         return None
# #     except Exception as e:
# #         print(f"错误：加载文件失败 - {str(e)}（文件：{file_path}）")
# #         return None


# # def query_deepseek_reasoner(question, sqlite_sql, mysql_sql, max_retries=3):
# #     """调用deepseek-reasoner模型分析SQLite和MySQL语法差异，增加重试机制和格式校验"""
# #     # 配置API参数（参考Deepseek官方文档）
# #     API_URL = "https://api.deepseek.com/chat/completions"
# #     MODEL_NAME = "deepseek-chat"  # 模型名称必须指定
# #     API_KEY = ""  # 替换为你的有效密钥
    
# #     # 构建提示词（明确格式要求，减少模型输出错误）
# #     prompt = f"""
# #     任务：分析SQLite和MySQL语句的语法差异及对应的自然语言原因。
# #     自然语言问题：{question}
# #     SQLite语句：{sqlite_sql}
# #     MySQL语句：{mysql_sql}
    
# #     要求：
# #     1. 仅输出JSON格式，不包含任何额外文本、解释或标记（如```json）。
# #     2. JSON包含两个字段：
# #        - syntax_differences：数组，列举语法差异（如数据类型支持、函数差异、约束差异等）。
# #        - causing_part：字符串，描述导致差异的自然语言问题部分（如"日期时间函数的使用"）。
# #     3. 差异描述需准确，例如："SQLite使用AUTOINCREMENT关键字需配合INTEGER PRIMARY KEY，MySQL可直接在任何整数类型使用AUTO_INCREMENT"。
# #     """
    
# #     headers = {
# #         "Content-Type": "application/json",
# #         "Authorization": f"Bearer {API_KEY}"  # 确保格式正确
# #     }
    
# #     # 构建符合API要求的请求体（OpenAI兼容格式）
# #     payload = {
# #         "model": MODEL_NAME,
# #         "messages": [{"role": "user", "content": prompt}],  # 必须用messages字段
# #         "max_tokens": 500,
# #         "temperature": 0.0  # 降低随机性，确保输出稳定
# #     }
    
# #     # 带重试的请求逻辑（处理临时网络错误）
# #     for retry in range(max_retries):
# #         try:
# #             response = requests.post(
# #                 API_URL,
# #                 headers=headers,
# #                 json=payload,
# #                 timeout=30  # 设置超时时间
# #             )
            
# #             # 处理HTTP错误状态码
# #             if response.status_code == 401:
# #                 print("错误：API密钥无效或已过期（401）")
# #                 return None  # 密钥错误无需重试
# #             if response.status_code == 429:
# #                 print(f"警告：请求频率超限，等待{2 ** retry}秒后重试...")
# #                 sleep(2 ** retry)  # 指数退避重试
# #                 continue
# #             if response.status_code != 200:
# #                 print(f"错误：API请求失败（状态码：{response.status_code}），响应：{response.text[:200]}")
# #                 return None
            
# #             # 解析响应内容
# #             result = response.json()
# #             # 验证响应结构
# #             if not all(key in result for key in ["choices"]) or len(result["choices"]) == 0:
# #                 print("错误：API返回格式异常（无choices字段）")
# #                 return None
            
# #             # 提取并清洗模型输出（去除可能的多余字符）
# #             model_output = result["choices"][0]["message"]["content"].strip()
# #             # 移除可能的代码块标记（如```json）
# #             model_output = model_output.replace("```json", "").replace("```", "").strip()
            
# #             # 解析为JSON
# #             try:
# #                 return json.loads(model_output)
# #             except json.JSONDecodeError as e:
# #                 print(f"错误：模型输出JSON解析失败 - {str(e)}，原始输出：{model_output[:200]}")
# #                 return None
            
# #         except requests.exceptions.Timeout:
# #             print(f"警告：请求超时，第{retry+1}次重试...")
# #         except requests.exceptions.ConnectionError:
# #             print(f"警告：网络连接错误，第{retry+1}次重试...")
# #         except Exception as e:
# #             print(f"错误：请求过程异常 - {str(e)}")
# #             if retry < max_retries - 1:
# #                 sleep(1)
# #                 continue
    
# #     # 超过最大重试次数
# #     print(f"错误：已达到最大重试次数（{max_retries}次），请求失败")
# #     return None


# # def main():
# #     # 定义文件路径
# #     input_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\undo.json"
# #     output_dir = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result"
# #     output_path = os.path.join(output_dir, "sqlite_mysql_difference.json")
    
# #     # 确保输出目录存在
# #     os.makedirs(output_dir, exist_ok=True)
    
# #     # 加载输入数据
# #     data = load_undo_json(input_path)
# #     if not data:
# #         print("无法加载输入数据，程序退出")
# #         return

# #     # 初始化统计变量
# #     total = len(data)
# #     valid_count = 0
# #     invalid_count = 0
# #     success_count = 0
# #     fail_count = 0
# #     results = []

# #     # 处理每个问题
# #     for i, item in enumerate(data, 1):
# #         # 详细检查每个必要字段
# #         missing_fields = []
# #         required_fields = ['question', 'sqlite', 'mysql']
# #         for field in required_fields:
# #             if field not in item:
# #                 missing_fields.append(field)
# #             # 检查字段是否为空值
# #             elif item[field] in (None, "", " "):
# #                 missing_fields.append(f"{field}（为空值）")

# #         # 处理无效数据
# #         if missing_fields:
# #             invalid_count += 1
# #             print(f"跳过无效数据（第{i}/{total}条）：缺少或无效的字段 - {', '.join(missing_fields)}")
# #             # 记录无效数据（可选）
# #             results.append({
# #                 "index": i,
# #                 "status": "无效数据",
# #                 "reason": f"缺少或无效的字段：{', '.join(missing_fields)}",
# #                 "原始数据": item  # 保留原始数据便于排查
# #             })
# #             continue

# #         # 处理有效数据
# #         valid_count += 1
# #         question = item['question']
# #         sqlite_sql = item['sqlite']
# #         mysql_sql = item['mysql']
        
# #         print(f"\n处理进度：{i}/{total} - 问题：{question[:60]}...")
# #         diff_info = query_deepseek_reasoner(question, sqlite_sql, mysql_sql)
        
# #         if diff_info:
# #             success_count += 1
# #             results.append({
# #                 "index": i,
# #                 "status": "成功",
# #                 "question": question,
# #                 "sqlite_sql": sqlite_sql,
# #                 "mysql_sql": mysql_sql,
# #                 "syntax_differences": diff_info.get("syntax_differences", []),
# #                 "causing_part": diff_info.get("causing_part", "")
# #             })
# #             print(f"处理成功：已获取差异信息（累计成功：{success_count}）")
# #         else:
# #             fail_count += 1
# #             results.append({
# #                 "index": i,
# #                 "status": "分析失败",
# #                 "question": question,
# #                 "sqlite_sql": sqlite_sql,
# #                 "mysql_sql": mysql_sql,
# #                 "syntax_differences": ["分析失败"],
# #                 "causing_part": "无法确定"
# #             })
# #             print(f"处理失败：无法获取差异信息（累计失败：{fail_count}）")
    
# #     # 保存结果到JSON文件
# #     try:
# #         with open(output_path, 'w', encoding='utf-8') as f:
# #             json.dump(results, f, ensure_ascii=False, indent=2)
# #         print(f"\n所有任务处理完成，结果已保存到：{output_path}")
# #         # 输出详细统计信息
# #         print(f"总数据量：{total}条")
# #         print(f"有效数据：{valid_count}条（成功：{success_count}条，失败：{fail_count}条）")
# #         print(f"无效数据：{invalid_count}条（缺少必要字段或字段为空）")
# #     except Exception as e:
# #         print(f"错误：保存结果文件失败 - {str(e)}")


# # if __name__ == "__main__":
# #     main()



# # # # #16.



# # # import json
# # # import os
# # # from shutil import copy2

# # # def rename_key_in_json(file_path, old_key, new_key):
# # #     """
# # #     将JSON文件中指定的键名批量替换为新键名
    
# # #     参数:
# # #         file_path (str): JSON文件路径
# # #         old_key (str): 需要替换的旧键名
# # #         new_key (str): 替换后的新键名
# # #     """
# # #     # 验证文件是否存在
# # #     if not os.path.exists(file_path):
# # #         print(f"错误：文件不存在 - {file_path}")
# # #         return False
    
# # #     # 验证是否为有效文件
# # #     if not os.path.isfile(file_path):
# # #         print(f"错误：{file_path} 不是有效文件")
# # #         return False
    
# # #     # 创建备份文件（在原文件名后添加.bak后缀）
# # #     backup_path = f"{file_path}.bak"
# # #     try:
# # #         copy2(file_path, backup_path)
# # #         print(f"已创建备份文件：{backup_path}")
# # #     except Exception as e:
# # #         print(f"警告：创建备份文件失败 - {str(e)}，将继续执行但不保证数据安全")
    
# # #     # 读取并解析JSON文件
# # #     try:
# # #         with open(file_path, 'r', encoding='utf-8') as f:
# # #             data = json.load(f)
# # #     except json.JSONDecodeError as e:
# # #         print(f"错误：JSON解析失败 - {str(e)}（文件：{file_path}）")
# # #         return False
# # #     except Exception as e:
# # #         print(f"错误：读取文件失败 - {str(e)}（文件：{file_path}）")
# # #         return False
    
# # #     # 检查数据类型（支持列表和字典两种格式）
# # #     if isinstance(data, list):
# # #         items = data
# # #     elif isinstance(data, dict):
# # #         items = [data]  # 包装为列表统一处理
# # #     else:
# # #         print(f"错误：JSON数据格式不支持（必须是列表或字典）")
# # #         return False
    
# # #     # 统计替换数量
# # #     replace_count = 0
    
# # #     # 遍历所有项目并替换键名
# # #     for item in items:
# # #         if isinstance(item, dict) and old_key in item:
# # #             # 将旧键值存入新键
# # #             item[new_key] = item[old_key]
# # #             # 删除旧键
# # #             del item[old_key]
# # #             replace_count += 1
    
# # #     # 保存修改后的内容
# # #     try:
# # #         with open(file_path, 'w', encoding='utf-8') as f:
# # #             json.dump(data, f, ensure_ascii=False, indent=2)
# # #         print(f"文件处理完成：{file_path}")
# # #         print(f"成功替换 {replace_count} 处 '{old_key}' 为 '{new_key}'")
# # #         return True
# # #     except Exception as e:
# # #         print(f"错误：保存文件失败 - {str(e)}（文件：{file_path}）")
# # #         return False


# # # if __name__ == "__main__":
# # #     # 定义文件路径和需要替换的键名
# # #     json_file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\do.json"
# # #     old_key_name = "SQL"
# # #     new_key_name = "sqlite"
    
# # #     # 执行替换操作
# # #     rename_key_in_json(json_file_path, old_key_name, new_key_name)




# # #17.


# # import json
# # import os
# # import re
# # from shutil import copy2

# # def normalize_text(text):
# #     """标准化文本，去除空格、标点和大小写差异，提高匹配率"""
# #     if not text:
# #         return ""
# #     # 转换为小写
# #     text = text.lower()
# #     # 移除所有标点和空格
# #     text = re.sub(r'[^\w\s]', '', text)
# #     text = re.sub(r'\s+', ' ', text).strip()
# #     return text

# # def load_json_file(file_path):
# #     """加载JSON文件并返回解析后的数据"""
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
# #         print(f"错误：JSON解析失败 - {str(e)}（文件：{file_path}）")
# #         return None
# #     except Exception as e:
# #         print(f"错误：加载文件失败 - {str(e)}（文件：{file_path}）")
# #         return None


# # def supplement_mysql_statements(mysql_source_path, target_path):
# #     """根据question键匹配，将mysql语句补充到目标文件中"""
# #     # 加载源文件和目标文件数据
# #     mysql_data = load_json_file(mysql_source_path)
# #     target_data = load_json_file(target_path)
    
# #     if not mysql_data or not target_data:
# #         print("无法加载源文件或目标文件，程序退出")
# #         return
    
# #     # 验证数据格式是否为列表
# #     if not isinstance(mysql_data, list):
# #         print("错误：mysql源文件数据必须是列表格式")
# #         return
# #     if not isinstance(target_data, list):
# #         print("错误：目标文件数据必须是列表格式")
# #         return
    
# #     # 提取源文件中的question（支持多种可能的键名）
# #     question_to_mysql = {}
# #     source_questions = []
# #     for item in mysql_data:
# #         if not isinstance(item, dict):
# #             continue
        
# #         # 支持多种可能的question键名（如"Question"、"problem"等）
# #         question_keys = ["question", "Question", "problem", "query"]
# #         question_text = None
# #         for key in question_keys:
# #             if key in item and item[key]:
# #                 question_text = str(item[key])
# #                 break
        
# #         # 支持多种可能的mysql键名
# #         mysql_keys = ["mysql", "MySQL", "sql", "SQL"]
# #         mysql_stmt = None
# #         for key in mysql_keys:
# #             if key in item and item[key]:
# #                 mysql_stmt = str(item[key])
# #                 break
        
# #         if question_text and mysql_stmt:
# #             normalized = normalize_text(question_text)
# #             question_to_mysql[normalized] = {
# #                 "original_question": question_text,
# #                 "mysql_stmt": mysql_stmt
# #             }
# #             source_questions.append(question_text[:50] + "...")  # 记录前50字符
    
# #     print(f"已从mysql源文件中加载 {len(question_to_mysql)} 条有效记录")
# #     if len(source_questions) > 0:
# #         print(f"源文件部分question示例：{source_questions[:3]}")  # 显示前3个示例

# #     # 创建目标文件备份
# #     backup_path = f"{target_path}.bak"
# #     try:
# #         copy2(target_path, backup_path)
# #         print(f"已创建目标文件备份：{backup_path}")
# #     except Exception as e:
# #         print(f"警告：创建备份文件失败 - {str(e)}，继续执行但存在风险")
    
# #     # 遍历目标文件数据，补充mysql语句
# #     updated_count = 0
# #     target_questions = []  # 用于记录目标文件中的question
# #     no_mysql_count = 0     # 目标文件中缺少mysql的条目数

# #     for item in target_data:
# #         if not isinstance(item, dict):
# #             continue
        
# #         # 提取目标文件中的question
# #         target_question = item.get("question", "")
# #         if target_question:
# #             target_questions.append(target_question[:50] + "...")
        
# #         # 检查是否缺少mysql语句
# #         current_mysql = item.get("mysql", "")
# #         if not current_mysql:
# #             no_mysql_count += 1

# #         # 尝试匹配
# #         if target_question:
# #             normalized_target = normalize_text(target_question)
# #             # 精确匹配标准化后的文本
# #             if normalized_target in question_to_mysql:
# #                 source_info = question_to_mysql[normalized_target]
# #                 item["mysql"] = source_info["mysql_stmt"]
# #                 updated_count += 1
# #                 print(f"匹配成功：\n目标question：{target_question[:50]}...\n源question：{source_info['original_question'][:50]}...")

# #     # 输出匹配诊断信息
# #     print("\n===== 匹配诊断 =====")
# #     print(f"目标文件总条目数：{len(target_data)}")
# #     print(f"目标文件中缺少mysql的条目数：{no_mysql_count}")
# #     print(f"源文件可用的question数量：{len(question_to_mysql)}")
# #     if len(target_questions) > 0:
# #         print(f"目标文件部分question示例：{target_questions[:3]}")

# #     # 保存更新后的目标文件
# #     try:
# #         with open(target_path, 'w', encoding='utf-8') as f:
# #             json.dump(target_data, f, ensure_ascii=False, indent=2)
# #         print(f"\n目标文件已更新并保存：{target_path}")
# #         print(f"成功补充 {updated_count} 条mysql语句")
# #     except Exception as e:
# #         print(f"错误：保存目标文件失败 - {str(e)}")


# # if __name__ == "__main__":
# #     # 定义文件路径
# #     mysql_source_file = r"C:\copy\code\minidev\MINIDEV\mysql\mysql1.json"
# #     target_file = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\do.json"
    
# #     # 执行补充操作
# #     supplement_mysql_statements(mysql_source_file, target_file)



# #17.



# import json
# import os
# import re
# from shutil import copy2

# def normalize_text(text):
#     """标准化文本，去除空格、标点和大小写差异，提高匹配率"""
#     if not text:
#         return ""
#     # 转换为小写
#     text = text.lower()
#     # 移除所有标点和空格
#     text = re.sub(r'[^\w\s]', '', text)
#     text = re.sub(r'\s+', ' ', text).strip()
#     return text

# def load_json_file(file_path):
#     """加载JSON文件并返回解析后的数据"""
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


# def supplement_mysql_statements(mysql_source_path, target_path):
#     """根据question键匹配，将mysql语句补充到目标文件中，并输出未匹配的question"""
#     # 加载源文件和目标文件数据
#     mysql_data = load_json_file(mysql_source_path)
#     target_data = load_json_file(target_path)
    
#     if not mysql_data or not target_data:
#         print("无法加载源文件或目标文件，程序退出")
#         return
    
#     # 验证数据格式是否为列表
#     if not isinstance(mysql_data, list):
#         print("错误：mysql源文件数据必须是列表格式")
#         return
#     if not isinstance(target_data, list):
#         print("错误：目标文件数据必须是列表格式")
#         return
    
#     # 提取源文件中的question（支持多种可能的键名）
#     question_to_mysql = {}
#     source_questions = []
#     for item in mysql_data:
#         if not isinstance(item, dict):
#             continue
        
#         # 支持多种可能的question键名
#         question_keys = ["question", "Question", "problem", "query"]
#         question_text = None
#         for key in question_keys:
#             if key in item and item[key]:
#                 question_text = str(item[key])
#                 break
        
#         # 支持多种可能的mysql键名
#         mysql_keys = ["mysql", "MySQL", "sql", "SQL"]
#         mysql_stmt = None
#         for key in mysql_keys:
#             if key in item and item[key]:
#                 mysql_stmt = str(item[key])
#                 break
        
#         if question_text and mysql_stmt:
#             normalized = normalize_text(question_text)
#             question_to_mysql[normalized] = {
#                 "original_question": question_text,
#                 "mysql_stmt": mysql_stmt
#             }
#             source_questions.append(question_text[:50] + "...")  # 记录前50字符
    
#     print(f"已从mysql源文件中加载 {len(question_to_mysql)} 条有效记录")
#     if len(source_questions) > 0:
#         print(f"源文件部分question示例：{source_questions[:3]}")

#     # 创建目标文件备份
#     backup_path = f"{target_path}.bak"
#     try:
#         copy2(target_path, backup_path)
#         print(f"已创建目标文件备份：{backup_path}")
#     except Exception as e:
#         print(f"警告：创建备份文件失败 - {str(e)}，继续执行但存在风险")
    
#     # 遍历目标文件数据，补充mysql语句
#     updated_count = 0
#     target_questions = []  # 目标文件中的question示例
#     no_mysql_count = 0     # 目标文件中缺少mysql的条目数
#     unmatched_questions = []  # 新增：存储未匹配的question信息
    
#     for idx, item in enumerate(target_data, 1):  # 新增索引，方便定位
#         if not isinstance(item, dict):
#             continue
        
#         # 提取目标文件中的question
#         target_question = item.get("question", "")
#         current_mysql = item.get("mysql", "")
        
#         # 记录目标question示例
#         if target_question and len(target_questions) < 3:
#             target_questions.append(target_question[:50] + "...")
        
#         # 统计缺少mysql的条目
#         if not current_mysql:
#             no_mysql_count += 1
        
#         # 尝试匹配
#         if target_question:
#             normalized_target = normalize_text(target_question)
#             if normalized_target in question_to_mysql:
#                 source_info = question_to_mysql[normalized_target]
#                 item["mysql"] = source_info["mysql_stmt"]
#                 updated_count += 1
#                 print(f"匹配成功（序号{idx}）：\n目标question：{target_question[:50]}...\n源question：{source_info['original_question'][:50]}...")
#             else:
#                 # 新增：记录未匹配的question
#                 unmatched_questions.append({
#                     "序号": idx,
#                     "question": target_question,
#                     "normalized_question": normalized_target,
#                     "原因": "源文件中无匹配的标准化question"
#                 })
#         else:
#             # 新增：记录无question的条目
#             if isinstance(item, dict):
#                 unmatched_questions.append({
#                     "序号": idx,
#                     "question": "无（目标条目缺少question键）",
#                     "normalized_question": "",
#                     "原因": "目标文件条目缺少question键"
#                 })

#     # 输出匹配诊断信息
#     print("\n===== 匹配诊断 =====")
#     print(f"目标文件总条目数：{len(target_data)}")
#     print(f"目标文件中缺少mysql的条目数：{no_mysql_count}")
#     print(f"源文件可用的question数量：{len(question_to_mysql)}")
#     if len(target_questions) > 0:
#         print(f"目标文件部分question示例：{target_questions[:3]}")
    
#     # 新增：输出未匹配的question信息
#     print(f"\n===== 未匹配的question信息 =====")
#     print(f"未匹配的question总数：{len(unmatched_questions)}")
#     for info in unmatched_questions[:10]:  # 显示前10条，避免输出过长
#         print(f"\n序号：{info['序号']}")
#         print(f"原始question：{info['question'][:200]}...")  # 截断长文本
#         if info["normalized_question"]:
#             print(f"标准化后：{info['normalized_question'][:200]}...")
#         print(f"原因：{info['原因']}")
#     if len(unmatched_questions) > 10:
#         print(f"\n... 还有 {len(unmatched_questions) - 10} 条未显示")

#     # 保存更新后的目标文件
#     try:
#         with open(target_path, 'w', encoding='utf-8') as f:
#             json.dump(target_data, f, ensure_ascii=False, indent=2)
#         print(f"\n目标文件已更新并保存：{target_path}")
#         print(f"成功补充 {updated_count} 条mysql语句")
#     except Exception as e:
#         print(f"错误：保存目标文件失败 - {str(e)}")


# if __name__ == "__main__":
#     # 定义文件路径
#     mysql_source_file = r"C:\copy\code\minidev\MINIDEV\mysql\mysql1.json"
#     target_file = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\do.json"
    
#     # 执行补充操作
#     supplement_mysql_statements(mysql_source_file, target_file)



###重新生成mysql和sqlite之间差异的文件


import json
import requests
import os
from time import sleep


def load_undo_json(file_path):
    """加载待分析的undo.json文件，增加文件路径验证"""
    if not os.path.exists(file_path):
        print(f"错误：文件不存在 - {file_path}")
        return None
    if not os.path.isfile(file_path):
        print(f"错误：不是有效文件 - {file_path}")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误：JSON解析失败 - {str(e)}（文件：{file_path}）")
        return None
    except Exception as e:
        print(f"错误：加载文件失败 - {str(e)}（文件：{file_path}）")
        return None


def query_diff_analyzer(question, mysql_sql, sqlite_sql, max_retries=3):
    """调用模型分析MySQL和SQLite语法差异，明确每个差异项的字段结构"""
    API_URL = "https://api.deepseek.com/chat/completions"
    MODEL_NAME = "deepseek-chat"  # 模型名称
    API_KEY = ""  # 替换为有效密钥

    # 构建提示词（明确每个差异项的5个字段 + 示例引导）
    prompt = f"""
    任务：分析MySQL和SQLite语句的语法差异，提取细粒度差异片段。
    自然语言问题：{question}
    MySQL语句：{mysql_sql}
    SQLite语句：{sqlite_sql}

    要求：
    1. 仅输出JSON格式（无多余文本），结构如下：
       {{
         "syntax_differences": [
           {{
             "difference": "差异类别（如日期函数语法）",
             "detail": "具体差异描述（如MySQL用CURRENT_DATE(), SQLite用DATE('now')）",
             "question_causing_substring": "问题中导致该差异的子串（原问题精确片段）",
             "mysql_differing_substring": "MySQL语句中对应差异的子串（原SQL精确片段）",
             "sqlite_differing_substring": "SQLite语句中对应差异的子串（原SQL精确片段）"
           }},
           ...
         ],
         "causing_part": "整体差异的自然语言概括（如日期函数与字符串处理差异）"
       }}
    2. 子字符串必须是原文本的**精确片段**（不得修改/概括），例如：
       - 问题子串："如何获取当前日期"
       - MySQL子串："CURRENT_DATE()"
       - SQLite子串："DATE('now')"
    3. 差异描述需准确，如："MySQL使用CURRENT_DATE()函数获取当前日期，SQLite使用DATE('now')"。

    参考示例（仅格式参考，无需复制）：
    问题："如何获取当前时间和自增主键"
    MySQL："SELECT NOW(), AUTO_INCREMENT FROM information_schema.tables;"
    SQLite："SELECT DATETIME('now'), sqlite_sequence.seq FROM sqlite_sequence;"
    期望输出（简化）：
    {{
      "syntax_differences": [
        {{
          "difference": "当前时间函数",
          "detail": "MySQL用NOW()，SQLite用DATETIME('now')",
          "question_causing_substring": "获取当前时间",
          "mysql_differing_substring": "NOW()",
          "sqlite_differing_substring": "DATETIME('now')"
        }},
        {{
          "difference": "自增主键查询",
          "detail": "MySQL查询information_schema.tables的AUTO_INCREMENT，SQLite查询sqlite_sequence的seq",
          "question_causing_substring": "自增主键",
          "mysql_differing_substring": "AUTO_INCREMENT FROM information_schema.tables",
          "sqlite_differing_substring": "sqlite_sequence.seq FROM sqlite_sequence"
        }}
      ],
      "causing_part": "时间函数与系统表查询差异"
    }}
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1200,
        "temperature": 0.1
    }

    # 带重试的请求逻辑
    for retry in range(max_retries):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            if response.status_code == 401:
                print("错误：API密钥无效（401）")
                return None
            if response.status_code == 429:
                sleep(2 ** retry)
                continue
            if response.status_code != 200:
                print(f"API失败（{response.status_code}）：{response.text[:200]}")
                return None

            result = response.json()
            if not result.get("choices"):
                print("响应无choices字段")
                return None

            model_output = result["choices"][0]["message"]["content"].strip()
            model_output = model_output.replace("```json", "").replace("```", "").strip()
            return json.loads(model_output)

        except requests.exceptions.Timeout:
            print(f"超时，第{retry+1}次重试...")
        except requests.exceptions.ConnectionError:
            print(f"网络错误，第{retry+1}次重试...")
        except json.JSONDecodeError as e:
            print(f"JSON解析失败：{e}，输出：{model_output[:200]}")
            return None
        except Exception as e:
            print(f"请求异常：{e}")
            if retry < max_retries - 1:
                sleep(1)

    print("达到最大重试次数，请求失败")
    return None


def main():
    input_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\run_result\undo.json"
    # 修改输出目录为指定路径
    output_dir = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\conclude"
    # 确保输出目录存在（若不存在则创建）
    os.makedirs(output_dir, exist_ok=True)
    # 定义输出文件路径
    output_path = os.path.join(output_dir, "sqlite_mysql_difference.json")

    data = load_undo_json(input_path)
    if not data:
        return

    total = len(data)
    results = []
    for i, item in enumerate(data, 1):
        # 检查必要字段是否存在
        required_fields = ['question', 'mysql', 'sqlite']
        if not all(key in item for key in required_fields):
            missing = [key for key in required_fields if key not in item]
            print(f"跳过无效数据（{i}/{total}）：缺少字段 {missing}")
            continue

        question = item['question']
        mysql_sql = item['mysql']
        sqlite_sql = item['sqlite']

        print(f"\n处理 {i}/{total}：{question[:60]}...")
        diff_info = query_diff_analyzer(question, mysql_sql, sqlite_sql)

        if diff_info:
            # 确保字段存在（模型可能漏填，设默认值）
            for diff in diff_info.get("syntax_differences", []):
                diff.setdefault("question_causing_substring", "")
                diff.setdefault("mysql_differing_substring", "")
                diff.setdefault("sqlite_differing_substring", "")

            results.append({
                "question": question,
                "mysql_sql": mysql_sql,
                "sqlite_sql": sqlite_sql,
                "syntax_differences": diff_info.get("syntax_differences", []),
                "causing_part": diff_info.get("causing_part", "")
            })
            print("处理成功：差异信息已提取")
        else:
            results.append({
                "question": question,
                "mysql_sql": mysql_sql,
                "sqlite_sql": sqlite_sql,
                "syntax_differences": [{"difference": "分析失败", "detail": "", "question_causing_substring": "", "mysql_differing_substring": "", "sqlite_differing_substring": ""}],
                "causing_part": "无法确定"
            })
            print("处理失败：未获取有效差异")

    # 保存结果
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        success = sum(1 for r in results if r["syntax_differences"][0]["difference"] != "分析失败")
        print(f"\n结果保存至：{output_path}")
        print(f"成功：{success} 条，失败：{len(results)-success} 条")
    except Exception as e:
        print(f"保存失败：{e}")


if __name__ == "__main__":
    main()