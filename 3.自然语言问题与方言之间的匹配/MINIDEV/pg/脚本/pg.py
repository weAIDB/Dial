# # # # # # # import json

# # # # # # # # 读取文件路径
# # # # # # # input_file_path = r"C:\copy\code\minidev\MINIDEV\mini_dev_postgresql.json"
# # # # # # # output_file_path = r"C:\copy\code\minidev\MINIDEV\pg.json"

# # # # # # # # 用于存储提取的数据
# # # # # # # result = []

# # # # # # # # 读取输入的 JSON 文件
# # # # # # # with open(input_file_path, 'r', encoding='utf-8') as file:
# # # # # # #     data = json.load(file)
# # # # # # #     for item in data:
# # # # # # #         extracted = {
# # # # # # #             "db_id": item.get("db_id"),
# # # # # # #             "question": item.get("question"),
# # # # # # #             "SQL": item.get("SQL")
# # # # # # #         }
# # # # # # #         result.append(extracted)

# # # # # # # # 将提取的数据写入新的 JSON 文件
# # # # # # # with open(output_file_path, 'w', encoding='utf-8') as output_file:
# # # # # # #     json.dump(result, output_file, ensure_ascii=False, indent=4)


# # # # # # #6.


# # # # # # import json
# # # # # # import os

# # # # # # def extract_and_format_sql(input_json_path, output_sql_path):
# # # # # #     """
# # # # # #     从JSON文件中提取SQL语句，确保每个语句末尾都有分号，然后保存到SQL文件
    
# # # # # #     参数:
# # # # # #         input_json_path: 输入的JSON文件路径
# # # # # #         output_sql_path: 输出的SQL文件路径
# # # # # #     """
# # # # # #     try:
# # # # # #         # 检查输入文件是否存在
# # # # # #         if not os.path.exists(input_json_path):
# # # # # #             print(f"错误：输入文件不存在 - {input_json_path}")
# # # # # #             return False
        
# # # # # #         # 读取JSON文件内容
# # # # # #         with open(input_json_path, 'r', encoding='utf-8') as f:
# # # # # #             try:
# # # # # #                 data = json.load(f)
# # # # # #             except json.JSONDecodeError as e:
# # # # # #                 print(f"错误：JSON文件解析失败 - {str(e)}")
# # # # # #                 return False
        
# # # # # #         # 验证数据格式是否为列表
# # # # # #         if not isinstance(data, list):
# # # # # #             print(f"错误：JSON内容不是列表类型")
# # # # # #             return False
        
# # # # # #         # 提取并处理SQL语句
# # # # # #         sql_statements = []
# # # # # #         for item in data:
# # # # # #             # 检查是否包含SQL字段
# # # # # #             if isinstance(item, dict) and 'SQL' in item and isinstance(item['SQL'], str):
# # # # # #                 sql = item['SQL'].strip()
# # # # # #                 # 如果语句末尾没有分号，则添加
# # # # # #                 if not sql.endswith(';'):
# # # # # #                     sql += ';'
# # # # # #                 sql_statements.append(sql)
# # # # # #             else:
# # # # # #                 print(f"警告：跳过无效条目 - {item}")
        
# # # # # #         # 确保输出目录存在
# # # # # #         output_dir = os.path.dirname(output_sql_path)
# # # # # #         os.makedirs(output_dir, exist_ok=True)
        
# # # # # #         # 保存到SQL文件
# # # # # #         with open(output_sql_path, 'w', encoding='utf-8') as f:
# # # # # #             # 每个SQL语句占一行
# # # # # #             f.write('\n'.join(sql_statements))
        
# # # # # #         print(f"成功提取并处理了 {len(sql_statements)} 条SQL语句")
# # # # # #         print(f"结果已保存至：{output_sql_path}")
# # # # # #         return True
    
# # # # # #     except Exception as e:
# # # # # #         print(f"处理过程中发生错误：{str(e)}")
# # # # # #         return False

# # # # # # if __name__ == "__main__":
# # # # # #     # 定义文件路径
# # # # # #     input_json = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\undo.json"
# # # # # #     output_sql = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\sql\pg_mysql.sql"
    
# # # # # #     # 执行提取和格式化操作
# # # # # #     extract_and_format_sql(input_json, output_sql)


# # # # # #7.


# # # # # import json
# # # # # import os

# # # # # def extract_and_format_sql(input_json_path, output_sql_path):
# # # # #     """
# # # # #     从JSON文件中提取SQL语句，确保每个语句末尾都有分号，然后保存到SQL文件
    
# # # # #     参数:
# # # # #         input_json_path: 输入的JSON文件路径
# # # # #         output_sql_path: 输出的SQL文件路径
# # # # #     """
# # # # #     try:
# # # # #         # 检查输入文件是否存在
# # # # #         if not os.path.exists(input_json_path):
# # # # #             print(f"错误：输入文件不存在 - {input_json_path}")
# # # # #             return False
        
# # # # #         # 读取JSON文件内容
# # # # #         with open(input_json_path, 'r', encoding='utf-8') as f:
# # # # #             try:
# # # # #                 data = json.load(f)
# # # # #             except json.JSONDecodeError as e:
# # # # #                 print(f"错误：JSON文件解析失败 - {str(e)}")
# # # # #                 return False
        
# # # # #         # 验证数据格式是否为列表
# # # # #         if not isinstance(data, list):
# # # # #             print(f"错误：JSON内容不是列表类型")
# # # # #             return False
        
# # # # #         # 提取并处理SQL语句
# # # # #         sql_statements = []
# # # # #         for item in data:
# # # # #             # 检查是否包含SQL字段
# # # # #             if isinstance(item, dict) and 'SQL' in item and isinstance(item['SQL'], str):
# # # # #                 sql = item['SQL'].strip()
# # # # #                 # 如果语句末尾没有分号，则添加
# # # # #                 if not sql.endswith(';'):
# # # # #                     sql += ';'
# # # # #                 sql_statements.append(sql)
# # # # #             else:
# # # # #                 print(f"警告：跳过无效条目 - {item}")
        
# # # # #         # 确保输出目录存在
# # # # #         output_dir = os.path.dirname(output_sql_path)
# # # # #         os.makedirs(output_dir, exist_ok=True)
        
# # # # #         # 保存到SQL文件
# # # # #         with open(output_sql_path, 'w', encoding='utf-8') as f:
# # # # #             # 每个SQL语句占一行
# # # # #             f.write('\n'.join(sql_statements))
        
# # # # #         print(f"成功提取并处理了 {len(sql_statements)} 条SQL语句")
# # # # #         print(f"结果已保存至：{output_sql_path}")
# # # # #         return True
    
# # # # #     except Exception as e:
# # # # #         print(f"处理过程中发生错误：{str(e)}")
# # # # #         return False

# # # # # if __name__ == "__main__":
# # # # #     # 定义文件路径（针对do.json和pg_mysql_do.sql）
# # # # #     input_json = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\do.json"
# # # # #     output_sql = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\sql\pg_mysql_do.sql"
    
# # # # #     # 执行提取和格式化操作
# # # # #     extract_and_format_sql(input_json, output_sql)




# # # # #8.
# # # # import sqlglot
# # # # import os

# # # # def convert_pgsql_to_mysql(input_path, output_path):
# # # #     """
# # # #     使用sqlglot将PostgreSQL语句转换为MySQL语句
    
# # # #     参数:
# # # #         input_path: 输入的PostgreSQL SQL文件路径
# # # #         output_path: 输出的MySQL SQL文件路径
# # # #     """
# # # #     try:
# # # #         # 检查输入文件是否存在
# # # #         if not os.path.exists(input_path):
# # # #             print(f"错误：输入文件不存在 - {input_path}")
# # # #             return False
        
# # # #         # 读取PostgreSQL SQL文件内容
# # # #         with open(input_path, 'r', encoding='utf-8') as f:
# # # #             pgsql_content = f.read()
        
# # # #         # 分割SQL语句（处理分号分隔的多个语句）
# # # #         pgsql_statements = [stmt.strip() for stmt in pgsql_content.split(';') if stmt.strip()]
        
# # # #         # 转换每个SQL语句
# # # #         mysql_statements = []
# # # #         error_count = 0
        
# # # #         for i, stmt in enumerate(pgsql_statements, 1):
# # # #             try:
# # # #                 # 从PostgreSQL转换为MySQL，注意方言名称应为"postgres"
# # # #                 mysql_stmt = sqlglot.transpile(
# # # #                     stmt,
# # # #                     read="postgres",  # 修正方言名称
# # # #                     write="mysql",
# # # #                     pretty=True  # 格式化输出
# # # #                 )[0]
# # # #                 mysql_statements.append(mysql_stmt)
# # # #             except Exception as e:
# # # #                 error_count += 1
# # # #                 print(f"警告：第{i}条语句转换失败 - {str(e)}")
# # # #                 print(f"原始语句：{stmt}")
# # # #                 # 将原始语句添加到结果中，便于后续手动处理
# # # #                 mysql_statements.append(f"-- 转换失败的原始语句：\n-- {stmt.replace('--', '##')}")
        
# # # #         # 确保输出目录存在
# # # #         output_dir = os.path.dirname(output_path)
# # # #         os.makedirs(output_dir, exist_ok=True)
        
# # # #         # 保存转换后的MySQL语句
# # # #         with open(output_path, 'w', encoding='utf-8') as f:
# # # #             # 每个语句用分号分隔并换行
# # # #             f.write(';\n\n'.join(mysql_statements) + ';')
        
# # # #         print(f"转换完成！共处理{len(pgsql_statements)}条语句，成功{len(pgsql_statements)-error_count}条，失败{error_count}条")
# # # #         print(f"结果已保存至：{output_path}")
# # # #         return True
    
# # # #     except Exception as e:
# # # #         print(f"处理过程中发生错误：{str(e)}")
# # # #         return False

# # # # if __name__ == "__main__":
# # # #     # 定义文件路径
# # # #     input_sql_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\sql\pg_mysql.sql"
# # # #     output_sql_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\sql\pg2mysql.sql"
    
# # # #     # 提示用户需要安装sqlglot
# # # #     print("注意：请确保已安装sqlglot库，如未安装，请先运行：pip install sqlglot")
    
# # # #     # 执行转换操作
# # # #     convert_pgsql_to_mysql(input_sql_path, output_sql_path)


# # # #8


# # # import json
# # # import os

# # # def rename_sql_key(input_path, output_path=None):
# # #     """
# # #     将JSON文件中所有字典的"SQL"键名替换为"postgres"
    
# # #     参数:
# # #         input_path: 输入的JSON文件路径
# # #         output_path: 输出的JSON文件路径，默认覆盖原文件
# # #     """
# # #     try:
# # #         # 检查输入文件是否存在
# # #         if not os.path.exists(input_path):
# # #             print(f"错误：输入文件不存在 - {input_path}")
# # #             return False
        
# # #         # 读取JSON文件内容
# # #         with open(input_path, 'r', encoding='utf-8') as f:
# # #             try:
# # #                 data = json.load(f)
# # #             except json.JSONDecodeError as e:
# # #                 print(f"错误：JSON文件解析失败 - {str(e)}")
# # #                 return False
        
# # #         # 验证数据格式是否为列表
# # #         if not isinstance(data, list):
# # #             print(f"错误：JSON内容不是列表类型")
# # #             return False
        
# # #         # 替换每个字典中的"SQL"键为"postgres"
# # #         modified_count = 0
# # #         for item in data:
# # #             if isinstance(item, dict) and "SQL" in item:
# # #                 # 将"SQL"键的值赋给"postgres"键
# # #                 item["postgres"] = item["SQL"]
# # #                 # 删除原"SQL"键
# # #                 del item["SQL"]
# # #                 modified_count += 1
        
# # #         # 如果未指定输出路径，则覆盖原文件
# # #         if output_path is None:
# # #             output_path = input_path
# # #         else:
# # #             # 确保输出目录存在
# # #             output_dir = os.path.dirname(output_path)
# # #             os.makedirs(output_dir, exist_ok=True)
        
# # #         # 保存修改后的内容
# # #         with open(output_path, 'w', encoding='utf-8') as f:
# # #             json.dump(data, f, ensure_ascii=False, indent=2)
        
# # #         print(f"处理完成，共修改了 {modified_count} 个条目")
# # #         print(f"结果已保存至：{output_path}")
# # #         return True
    
# # #     except Exception as e:
# # #         print(f"处理过程中发生错误：{str(e)}")
# # #         return False

# # # if __name__ == "__main__":
# # #     # 定义文件路径
# # #     input_json_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\undo.json"
    
# # #     # 执行键名替换操作（默认覆盖原文件）
# # #     # 如果需要保留原文件，可以指定output_path参数，例如：
# # #     # output_json_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\undo_modified.json"
# # #     # rename_sql_key(input_json_path, output_json_path)
    
# # #     # 直接修改原文件
# # #     rename_sql_key(input_json_path)


# # #9.


# # import json
# # import os

# # def load_json_file(file_path):
# #     """加载JSON文件并返回数据，包含错误处理"""
# #     try:
# #         if not os.path.exists(file_path):
# #             print(f"错误：文件不存在 - {file_path}")
# #             return None
        
# #         with open(file_path, 'r', encoding='utf-8') as f:
# #             return json.load(f)
    
# #     except json.JSONDecodeError as e:
# #         print(f"错误：JSON解析失败 {file_path} - {str(e)}")
# #         return None
# #     except Exception as e:
# #         print(f"错误：加载文件 {file_path} 失败 - {str(e)}")
# #         return None

# # def save_json_file(data, file_path):
# #     """保存数据到JSON文件"""
# #     try:
# #         output_dir = os.path.dirname(file_path)
# #         os.makedirs(output_dir, exist_ok=True)
        
# #         with open(file_path, 'w', encoding='utf-8') as f:
# #             json.dump(data, f, ensure_ascii=False, indent=2)
# #         return True
# #     except Exception as e:
# #         print(f"错误：保存文件 {file_path} 失败 - {str(e)}")
# #         return False

# # def match_by_question_and_merge(mysql_json_path, undo_json_path):
# #     """
# #     从mysql1.json提取question和SQL，与undo.json中的question匹配，
# #     将匹配的SQL添加到undo.json中，键名为mysql
# #     """
# #     # 加载两个JSON文件
# #     mysql_data = load_json_file(mysql_json_path)
# #     undo_data = load_json_file(undo_json_path)
    
# #     if not mysql_data or not undo_data:
# #         return False
    
# #     # 验证数据格式
# #     if not isinstance(mysql_data, list) or not isinstance(undo_data, list):
# #         print("错误：JSON数据必须是列表类型")
# #         return False
    
# #     # 构建mysql数据的question映射（question内容 -> SQL值）
# #     # 去除前后空格用于匹配，同时保留原始SQL值
# #     mysql_question_map = {}
# #     for item in mysql_data:
# #         if (isinstance(item, dict) and 
# #             "question" in item and isinstance(item["question"], str) and 
# #             "SQL" in item and isinstance(item["SQL"], str)):
# #             question_key = item["question"].strip()
# #             mysql_question_map[question_key] = item["SQL"]
    
# #     print(f"从mysql1.json中提取了 {len(mysql_question_map)} 条带question的SQL语句")
    
# #     # 遍历undo.json，查找匹配项并添加mysql键
# #     matched_count = 0
# #     for item in undo_data:
# #         # 检查是否包含question键
# #         if isinstance(item, dict) and "question" in item and isinstance(item["question"], str):
# #             question = item["question"].strip()
# #             # 查找匹配的mysql SQL
# #             if question in mysql_question_map:
# #                 # 添加mysql键
# #                 item["mysql"] = mysql_question_map[question]
# #                 matched_count += 1
    
# #     print(f"找到 {matched_count} 条匹配的question，已添加对应的mysql SQL到undo.json中")
    
# #     # 保存修改后的undo.json
# #     return save_json_file(undo_data, undo_json_path)

# # if __name__ == "__main__":
# #     # 定义文件路径
# #     mysql_json_path = r"C:\copy\code\minidev\MINIDEV\mysql\mysql1.json"
# #     undo_json_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\undo.json"
    
# #     # 执行匹配和合并操作
# #     match_by_question_and_merge(mysql_json_path, undo_json_path)
# #     print("操作完成")
    
    
    
# #10.


# import json

# def process_json_data(data):
#     """递归处理JSON数据，去除mysql字段中的换行符"""
#     if isinstance(data, dict):
#         # 处理字典类型
#         for key, value in data.items():
#             if key == "mysql" and isinstance(value, str):
#                 # 去除换行符
#                 data[key] = value.replace("\\n", "").replace("\n", "")
#             else:
#                 # 递归处理其他字段
#                 process_json_data(value)
#     elif isinstance(data, list):
#         # 处理列表类型
#         for item in data:
#             process_json_data(item)
#     # 其他类型不处理

# def main():
#     # 文件路径
#     file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\undo.json"
    
#     try:
#         # 读取JSON文件
#         with open(file_path, 'r', encoding='utf-8') as f:
#             try:
#                 json_data = json.load(f)
#             except json.JSONDecodeError as e:
#                 print(f"JSON解析错误: {e}")
#                 return
        
#         # 处理数据
#         process_json_data(json_data)
        
#         # 保存修改后的文件（覆盖原文件）
#         with open(file_path, 'w', encoding='utf-8') as f:
#             json.dump(json_data, f, ensure_ascii=False, indent=2)
        
#         print(f"已成功去除mysql语句中的换行符，文件已更新: {file_path}")
    
#     except FileNotFoundError:
#         print(f"错误: 找不到文件 {file_path}")
#     except Exception as e:
#         print(f"处理文件时发生错误: {str(e)}")

# if __name__ == "__main__":
#     main()
    

    
#12.


import json
import os

def load_json_file(file_path):
    """加载JSON文件并返回数据"""
    if not os.path.exists(file_path):
        print(f"错误：文件不存在 - {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"错误：{file_path} 不是有效的JSON文件")
        return None
    except Exception as e:
        print(f"加载{file_path}时出错：{str(e)}")
        return None

def save_json_file(data, file_path):
    """保存数据到JSON文件"""
    try:
        # 确保输出目录存在
        dir_name = os.path.dirname(file_path)
        os.makedirs(dir_name, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"文件已保存到：{file_path}")
        return True
    except Exception as e:
        print(f"保存文件时出错：{str(e)}")
        return False

def replace_mysql_statements(undo_path, mysql1_path, output_path=None):
    """
    将undo.json中与mysql1.json问题相同的条目，其"mysql"字段替换为mysql1.json中的"SQL"字段
    """
    # 加载两个JSON文件的数据
    undo_data = load_json_file(undo_path)
    mysql1_data = load_json_file(mysql1_path)
    
    if not undo_data or not mysql1_data:
        return False
    
    # 创建mysql1数据的问题到SQL的映射（提高查询效率）
    question_to_sql = {}
    for item in mysql1_data:
        if "question" in item and "SQL" in item:
            question = item["question"].strip()  # 去除首尾空格，确保匹配准确性
            question_to_sql[question] = item["SQL"]
    
    # 遍历undo_data，替换匹配的mysql语句
    replaced_count = 0
    for item in undo_data:
        if "question" in item and "mysql" in item:
            question = item["question"].strip()
            # 检查是否存在匹配的问题
            if question in question_to_sql:
                # 替换mysql字段的值
                item["mysql"] = question_to_sql[question]
                replaced_count += 1
                print(f"已替换问题：{question[:50]}...")  # 打印部分问题，避免过长
    
    print(f"替换完成，共处理 {replaced_count} 条匹配记录")
    
    # 保存结果（默认覆盖原undo.json，可指定输出路径）
    if output_path:
        return save_json_file(undo_data, output_path)
    else:
        # 询问是否覆盖原文件
        confirm = input(f"是否覆盖原文件 {undo_path}？(y/n): ").strip().lower()
        if confirm == 'y':
            return save_json_file(undo_data, undo_path)
        else:
            print("已取消保存，可通过指定output_path参数保存到新文件")
            return False

if __name__ == "__main__":
    # 定义文件路径
    undo_json_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\undo.json"
    mysql1_json_path = r"C:\copy\code\minidev\MINIDEV\mysql\mysql1.json"
    
    # 可选：指定输出路径（不指定则询问是否覆盖原文件）
    # output_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\undo_updated.json"
    
    # 执行替换操作
    replace_mysql_statements(
        undo_path=undo_json_path,
        mysql1_path=mysql1_json_path
        # output_path=output_path  # 取消注释可指定输出到新文件
    )