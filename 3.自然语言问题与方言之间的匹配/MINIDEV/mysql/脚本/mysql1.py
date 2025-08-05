# # # # import json

# # # # # 输入文件路径
# # # # input_file_path = r"C:\copy\code\minidev\MINIDEV\mini_dev_mysql.json"
# # # # # 输出文件路径
# # # # output_file_path = r"C:\copy\code\minidev\MINIDEV\mysql.json"

# # # # try:
# # # #     # 读取输入 JSON 文件内容
# # # #     with open(input_file_path, 'r', encoding='utf-8') as file:
# # # #         data = json.load(file)

# # # #     # 提取所需字段，构建新的数据列表
# # # #     result = []
# # # #     for item in data:
# # # #         extracted = {
# # # #             "db_id": item.get("db_id"),
# # # #             "question": item.get("question"),
# # # #             "SQL": item.get("SQL")
# # # #         }
# # # #         result.append(extracted)

# # # #     # 将提取后的数据写入新的 JSON 文件
# # # #     with open(output_file_path, 'w', encoding='utf-8') as output_file:
# # # #         json.dump(result, output_file, ensure_ascii=False, indent=4)

# # # #     print(f"已成功提取数据并保存到 {output_file_path}")
# # # # except FileNotFoundError:
# # # #     print(f"错误：未找到文件 {input_file_path}")
# # # # except json.JSONDecodeError:
# # # #     print(f"错误：文件 {input_file_path} 不是有效的 JSON 格式")
# # # # except Exception as e:
# # # #     print(f"处理过程中发生错误：{e}")


# # # #2.
# # # # import json

# # # # # 读取 JSON 文件
# # # # json_file_path = r"C:\copy\code\minidev\MINIDEV\mysql\mysql.json"
# # # # with open(json_file_path, 'r', encoding='utf-8') as file:
# # # #     data = json.load(file)

# # # # # 提取 SQL 并处理
# # # # sql_statements = []
# # # # for item in data:
# # # #     sql = item.get('SQL')
# # # #     if sql:
# # # #         # 去除末尾可能存在的分号，再统一添加，确保只有一个分号结尾
# # # #         sql = sql.rstrip(';') + ';'  
# # # #         sql_statements.append(sql)

# # # # # 写入 SQL 文件
# # # # sql_file_path = r"C:\copy\code\minidev\MINIDEV\mysql\mysql.sql"
# # # # with open(sql_file_path, 'w', encoding='utf-8') as sql_file:
# # # #     for stmt in sql_statements:
# # # #         sql_file.write(stmt + '\n')

# # # # print(f"已生成 {sql_file_path}，共处理 {len(sql_statements)} 条 SQL 语句")
# # #     #  db_config = {
# # #     #     'host': 'localhost',      # 数据库主机地址
# # #     #     'database': 'BIRD',    # 数据库名称
# # #     #     'user': 'root',  # 数据库用户名
# # #     #     'password': 'xuhongming3410',  # 数据库密码
# # #     #     'port': 3306              # 数据库端口，默认3306可省略
# # #     # }
# # # #3.
# # import mysql.connector
# # from mysql.connector import Error
# # import json
# # import os
# # import re

# # def classify_sql_execution():
# #     # 配置路径信息
# #     sql_file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg.sql"
# #     true_json_path = r"C:\copy\code\minidev\MINIDEV\pg\true.json"
# #     false_json_path = r"C:\copy\code\minidev\MINIDEV\pg\false.json"
    
# #     # 数据库连接配置 - 请根据实际情况修改
# #     db_config = {
# #         'host': 'localhost',      # 数据库主机地址
# #         'database': 'BIRD',    # 数据库名称
# #         'user': 'root',  # 数据库用户名
# #         'password': 'xuhongming3410',  # 数据库密码
# #         'port': 3306              # 数据库端口，默认3306可省略
# #     }
    
# #     # 初始化结果列表
# #     successful_queries = []
# #     failed_queries = []
    
# #     connection = None
# #     cursor = None
    
# #     try:
# #         # 确保输出目录存在
# #         os.makedirs(os.path.dirname(true_json_path), exist_ok=True)
        
# #         # 读取并解析SQL文件
# #         with open(sql_file_path, 'r', encoding='utf-8') as f:
# #             sql_content = f.read()
        
# #         # 处理SQL内容，分割为单个语句，处理注释和空行
# #         # 移除单行注释
# #         sql_content = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
# #         # 分割SQL语句
# #         sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
# #         if not sql_statements:
# #             print("SQL文件中没有有效的SQL语句")
# #             return
        
# #         # 连接数据库
# #         connection = mysql.connector.connect(**db_config)
# #         cursor = connection.cursor()
        
# #         # 执行每个SQL语句
# #         for idx, sql in enumerate(sql_statements, 1):
# #             try:
# #                 # 执行SQL语句
# #                 cursor.execute(sql)
# #                 # 对于DML语句提交事务
# #                 if sql.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE', 'ALTER', 'CREATE')):
# #                     connection.commit()
                
# #                 # 记录成功执行的语句
# #                 successful_queries.append({
# #                     "id": idx,
# #                     "sql": sql,
# #                     "message": "执行成功"
# #                 })
# #                 print(f"语句 {idx} 执行成功")
                
# #             except Error as e:
# #                 # 记录执行失败的语句及错误信息
# #                 failed_queries.append({
# #                     "id": idx,
# #                     "sql": sql,
# #                     "error": str(e),
# #                     "error_code": e.errno
# #                 })
# #                 print(f"语句 {idx} 执行失败: {str(e)}")
# #                 # 回滚事务以防影响后续执行
# #                 if connection:
# #                     connection.rollback()
        
# #         # 保存成功执行的语句
# #         with open(true_json_path, 'w', encoding='utf-8') as f:
# #             json.dump(successful_queries, f, ensure_ascii=False, indent=2)
        
# #         # 保存执行失败的语句
# #         with open(false_json_path, 'w', encoding='utf-8') as f:
# #             json.dump(failed_queries, f, ensure_ascii=False, indent=2)
        
# #         print(f"\n处理完成！")
# #         print(f"成功执行的语句: {len(successful_queries)} 条，已保存到 {true_json_path}")
# #         print(f"执行失败的语句: {len(failed_queries)} 条，已保存到 {false_json_path}")
        
# #     except FileNotFoundError:
# #         print(f"错误：找不到SQL文件 - {sql_file_path}")
# #     except Error as e:
# #         print(f"数据库连接错误：{str(e)}")
# #     except Exception as e:
# #         print(f"发生意外错误：{str(e)}")
# #     finally:
# #         # 确保资源正确释放
# #         if cursor:
# #             cursor.close()
# #         if connection and connection.is_connected():
# #             connection.close()

# # if __name__ == "__main__":
# #     classify_sql_execution()
    
    

# # #4.
# # import json
# # import os

# # def find_matching_sql_entries():
# #     # 文件路径配置
# #     pg_json_path = r"C:\copy\code\minidev\MINIDEV\pg\pg.json"
# #     false_json_path = r"C:\copy\code\minidev\MINIDEV\pg\false.json"
# #     undo_json_path = r"C:\copy\code\minidev\MINIDEV\pg\undo.json"
    
# #     try:
# #         # 确保输出目录存在
# #         os.makedirs(os.path.dirname(undo_json_path), exist_ok=True)
        
# #         # 读取pg.json文件
# #         with open(pg_json_path, 'r', encoding='utf-8') as f:
# #             try:
# #                 pg_data = json.load(f)
# #                 # 确保读取的数据是列表类型
# #                 if not isinstance(pg_data, list):
# #                     print(f"错误：{pg_json_path} 内容不是有效的列表格式")
# #                     return
# #             except json.JSONDecodeError as e:
# #                 print(f"错误：解析 {pg_json_path} 失败 - {str(e)}")
# #                 return
        
# #         # 读取false.json文件
# #         with open(false_json_path, 'r', encoding='utf-8') as f:
# #             try:
# #                 false_data = json.load(f)
# #                 # 确保读取的数据是列表类型
# #                 if not isinstance(false_data, list):
# #                     print(f"错误：{false_json_path} 内容不是有效的列表格式")
# #                     return
# #             except json.JSONDecodeError as e:
# #                 print(f"错误：解析 {false_json_path} 失败 - {str(e)}")
# #                 return
        
# #         # 提取false.json中所有的sql语句（统一转为小写用于比对，去除多余空格）
# #         false_sql_set = set()
# #         for item in false_data:
# #             if isinstance(item, dict) and 'sql' in item:
# #                 # 标准化SQL语句：去除多余空格并转为小写，提高匹配准确性
# #                 normalized_sql = ' '.join(item['sql'].strip().lower().split())
# #                 false_sql_set.add(normalized_sql)
        
# #         # 查找pg.json中与false.json中sql匹配的条目
# #         matching_entries = []
# #         for entry in pg_data:
# #             if isinstance(entry, dict) and 'SQL' in entry:
# #                 # 标准化pg.json中的SQL语句
# #                 normalized_pg_sql = ' '.join(entry['SQL'].strip().lower().split())
# #                 if normalized_pg_sql in false_sql_set:
# #                     matching_entries.append(entry)
        
# #         # 保存匹配结果到undo.json
# #         with open(undo_json_path, 'w', encoding='utf-8') as f:
# #             json.dump(matching_entries, f, ensure_ascii=False, indent=2)
        
# #         print(f"处理完成！")
# #         print(f"共找到 {len(matching_entries)} 条匹配的SQL语句")
# #         print(f"结果已保存到：{undo_json_path}")
        
# #     except FileNotFoundError as e:
# #         print(f"错误：找不到文件 - {str(e)}")
# #     except Exception as e:
# #         print(f"发生意外错误：{str(e)}")

# # if __name__ == "__main__":
# #     find_matching_sql_entries()
    
    
# #5.
# import json
# import os
# import re

# def find_matching_sql():
#     # 配置文件路径
#     pg_json_path = r"C:\copy\code\minidev\MINIDEV\pg\pg.json"
#     true_json_path = r"C:\copy\code\minidev\MINIDEV\pg\true.json"
#     do_json_path = r"C:\copy\code\minidev\MINIDEV\pg\do.json"
    
#     try:
#         # 确保输出目录存在
#         os.makedirs(os.path.dirname(do_json_path), exist_ok=True)
        
#         # 读取pg.json文件
#         with open(pg_json_path, 'r', encoding='utf-8') as f:
#             try:
#                 pg_data = json.load(f)
#                 if not isinstance(pg_data, list):
#                     print(f"错误：{pg_json_path} 内容应为列表格式")
#                     return
#             except json.JSONDecodeError as e:
#                 print(f"解析 {pg_json_path} 失败：{str(e)}")
#                 return
        
#         # 读取true.json文件
#         with open(true_json_path, 'r', encoding='utf-8') as f:
#             try:
#                 true_data = json.load(f)
#                 if not isinstance(true_data, list):
#                     print(f"错误：{true_json_path} 内容应为列表格式")
#                     return
#             except json.JSONDecodeError as e:
#                 print(f"解析 {true_json_path} 失败：{str(e)}")
#                 return
        
#         # 标准化处理true.json中的sql语句，用于比对
#         def normalize_sql(sql):
#             # 去除注释、多余空格和空行，统一转为小写
#             sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)  # 移除单行注释
#             sql = re.sub(r'\s+', ' ', sql).strip().lower()  # 合并空格并转为小写
#             return sql
        
#         # 提取true.json中所有标准化后的sql语句
#         true_sql_set = set()
#         for item in true_data:
#             if isinstance(item, dict) and 'sql' in item:
#                 normalized = normalize_sql(item['sql'])
#                 true_sql_set.add(normalized)
        
#         # 查找pg.json中匹配的条目
#         matching_items = []
#         for item in pg_data:
#             if isinstance(item, dict) and 'SQL' in item:
#                 normalized_pg_sql = normalize_sql(item['SQL'])
#                 if normalized_pg_sql in true_sql_set:
#                     matching_items.append(item)
        
#         # 保存结果到do.json
#         with open(do_json_path, 'w', encoding='utf-8') as f:
#             json.dump(matching_items, f, ensure_ascii=False, indent=2)
        
#         print(f"处理完成！")
#         print(f"共找到 {len(matching_items)} 条匹配的SQL语句")
#         print(f"结果已保存至：{do_json_path}")
        
#     except FileNotFoundError as e:
#         print(f"文件未找到：{str(e)}")
#     except Exception as e:
#         print(f"发生错误：{str(e)}")

# if __name__ == "__main__":
#     find_matching_sql()
        
        
        
#6.


