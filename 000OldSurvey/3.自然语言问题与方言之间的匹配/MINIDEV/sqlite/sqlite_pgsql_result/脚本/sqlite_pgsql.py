# # # # # # # import psycopg2
# # # # # # # import json
# # # # # # # import os
# # # # # # # import re
# # # # # # # from psycopg2 import errors
# # # # # # # import logging
# # # # # # # from datetime import datetime

# # # # # # # # 配置日志
# # # # # # # logging.basicConfig(
# # # # # # #     level=logging.INFO,
# # # # # # #     format='%(asctime)s - %(levelname)s - %(message)s',
# # # # # # #     handlers=[
# # # # # # #         logging.FileHandler('sql_execution.log', encoding='utf-8'),
# # # # # # #         logging.StreamHandler()
# # # # # # #     ]
# # # # # # # )

# # # # # # # def split_sql_commands(sql_content):
# # # # # # #     """
# # # # # # #     改进的SQL命令分割函数，能更好地处理复杂SQL语句
# # # # # # #     处理字符串、注释和特殊SQL块中的分号
# # # # # # #     """
# # # # # # #     # 移除注释（单行和多行）
# # # # # # #     # 先处理多行注释 /* ... */
# # # # # # #     sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
# # # # # # #     # 再处理单行注释 -- ...
# # # # # # #     sql_content = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
    
# # # # # # #     commands = []
# # # # # # #     current_command = []
# # # # # # #     in_string = None  # 记录当前是否在字符串中，以及字符串使用的引号类型
    
# # # # # # #     for line in sql_content.split('\n'):
# # # # # # #         stripped_line = line.strip()
# # # # # # #         if not stripped_line and not current_command:
# # # # # # #             continue
            
# # # # # # #         i = 0
# # # # # # #         line_length = len(line)
        
# # # # # # #         while i < line_length:
# # # # # # #             # 检查是否进入或退出字符串
# # # # # # #             if line[i] in ["'", '"']:
# # # # # # #                 if in_string == line[i]:
# # # # # # #                     in_string = None
# # # # # # #                 elif in_string is None:
# # # # # # #                     in_string = line[i]
# # # # # # #                 i += 1
# # # # # # #             # 当不在字符串中且遇到分号时，判断为命令结束
# # # # # # #             elif line[i] == ';' and in_string is None:
# # # # # # #                 # 提取到分号为止的内容
# # # # # # #                 current_line_part = line[:i+1]
# # # # # # #                 current_command.append(current_line_part)
# # # # # # #                 # 合并当前命令并添加到列表
# # # # # # #                 command = '\n'.join(current_command).strip()
# # # # # # #                 if command:
# # # # # # #                     commands.append(command)
# # # # # # #                 # 重置当前命令
# # # # # # #                 current_command = []
# # # # # # #                 # 处理剩余部分
# # # # # # #                 remaining_line = line[i+1:]
# # # # # # #                 if remaining_line.strip():
# # # # # # #                     current_command.append(remaining_line)
# # # # # # #                 i = line_length  # 跳到行尾
# # # # # # #             else:
# # # # # # #                 i += 1
                
# # # # # # #         # 如果没有遇到分号，将整行添加到当前命令
# # # # # # #         if i == line_length and not (line.endswith(';') and in_string is None):
# # # # # # #             current_command.append(line)
    
# # # # # # #     # 添加最后一个命令（如果有）
# # # # # # #     if current_command:
# # # # # # #         command = '\n'.join(current_command).strip()
# # # # # # #         if command:
# # # # # # #             commands.append(command)
            
# # # # # # #     return commands

# # # # # # # def execute_sql_commands(host, port, dbname, user, password, sql_file_path, result_dir):
# # # # # # #     """执行SQL命令并分类保存结果，增强了错误处理和日志记录"""
# # # # # # #     # 确保结果目录存在
# # # # # # #     os.makedirs(result_dir, exist_ok=True)
# # # # # # #     logging.info(f"结果将保存到: {result_dir}")
    
# # # # # # #     # 读取SQL文件内容
# # # # # # #     try:
# # # # # # #         with open(sql_file_path, 'r', encoding='utf-8') as f:
# # # # # # #             sql_content = f.read()
# # # # # # #         logging.info(f"成功读取SQL文件: {sql_file_path}")
# # # # # # #     except Exception as e:
# # # # # # #         logging.error(f"读取SQL文件失败: {str(e)}")
# # # # # # #         return
    
# # # # # # #     # 分割SQL命令
# # # # # # #     try:
# # # # # # #         commands = split_sql_commands(sql_content)
# # # # # # #         logging.info(f"共解析到 {len(commands)} 条SQL命令")
# # # # # # #     except Exception as e:
# # # # # # #         logging.error(f"分割SQL命令失败: {str(e)}")
# # # # # # #         return
    
# # # # # # #     # 连接数据库
# # # # # # #     conn = None
# # # # # # #     try:
# # # # # # #         # 确保端口是整数
# # # # # # #         port = int(port) if port else 5432
        
# # # # # # #         conn = psycopg2.connect(
# # # # # # #             host=host,
# # # # # # #             port=port,
# # # # # # #             dbname=dbname,
# # # # # # #             user=user,
# # # # # # #             password=password
# # # # # # #         )
# # # # # # #         cursor = conn.cursor()
# # # # # # #         logging.info("成功连接到数据库")
        
# # # # # # #         # 存储结果
# # # # # # #         success_commands = []
# # # # # # #         failed_commands = []
        
# # # # # # #         # 执行每条命令
# # # # # # #         for i, cmd in enumerate(commands, 1):
# # # # # # #             try:
# # # # # # #                 logging.info(f"开始执行第 {i} 条命令")
# # # # # # #                 # 记录执行时间
# # # # # # #                 start_time = datetime.now()
                
# # # # # # #                 cursor.execute(cmd)
# # # # # # #                 conn.commit()
                
# # # # # # #                 # 计算执行时间
# # # # # # #                 execution_time = (datetime.now() - start_time).total_seconds()
                
# # # # # # #                 success_commands.append({
# # # # # # #                     "index": i,
# # # # # # #                     "sql": cmd,
# # # # # # #                     "message": "执行成功",
# # # # # # #                     "execution_time_seconds": round(execution_time, 4),
# # # # # # #                     "timestamp": datetime.now().isoformat()
# # # # # # #                 })
# # # # # # #                 logging.info(f"第 {i} 条命令执行成功 (耗时: {execution_time:.4f}秒)")
                
# # # # # # #             except Exception as e:
# # # # # # #                 conn.rollback()
# # # # # # #                 error_info = {
# # # # # # #                     "index": i,
# # # # # # #                     "sql": cmd,
# # # # # # #                     "error": str(e),
# # # # # # #                     "error_type": type(e).__name__,
# # # # # # #                     "timestamp": datetime.now().isoformat()
# # # # # # #                 }
                
# # # # # # #                 # 针对特定错误类型添加更多信息
# # # # # # #                 if isinstance(e, errors.UniqueViolation):
# # # # # # #                     error_info["hint"] = "可能存在重复的唯一键值"
# # # # # # #                 elif isinstance(e, errors.ForeignKeyViolation):
# # # # # # #                     error_info["hint"] = "外键约束 violation，可能引用了不存在的数据"
# # # # # # #                 elif isinstance(e, errors.CheckViolation):
# # # # # # #                     error_info["hint"] = "检查约束 violation，数据不符合表定义的检查条件"
# # # # # # #                 elif isinstance(e, errors.ProgrammingError):
# # # # # # #                     error_info["hint"] = "可能存在语法错误或对象不存在"
                
# # # # # # #                 failed_commands.append(error_info)
# # # # # # #                 logging.error(f"第 {i} 条命令执行失败: {str(e)}")
        
# # # # # # #         # 保存结果
# # # # # # #         try:
# # # # # # #             true_path = os.path.join(result_dir, 'true.json')
# # # # # # #             with open(true_path, 'w', encoding='utf-8') as f:
# # # # # # #                 json.dump(success_commands, f, ensure_ascii=False, indent=2)
# # # # # # #             logging.info(f"成功命令已保存到: {true_path}")
            
# # # # # # #             false_path = os.path.join(result_dir, 'false.json')
# # # # # # #             with open(false_path, 'w', encoding='utf-8') as f:
# # # # # # #                 json.dump(failed_commands, f, ensure_ascii=False, indent=2)
# # # # # # #             logging.info(f"失败命令已保存到: {false_path}")
            
# # # # # # #             logging.info(f"执行完成。成功: {len(success_commands)} 条, 失败: {len(failed_commands)} 条")
            
# # # # # # #         except Exception as e:
# # # # # # #             logging.error(f"保存结果文件失败: {str(e)}")
            
# # # # # # #     except Exception as e:
# # # # # # #         logging.error(f"数据库连接或操作失败: {str(e)}")
# # # # # # #     finally:
# # # # # # #         if conn:
# # # # # # #             try:
# # # # # # #                 conn.close()
# # # # # # #                 logging.info("数据库连接已关闭")
# # # # # # #             except Exception as e:
# # # # # # #                 logging.warning(f"关闭数据库连接时出错: {str(e)}")

# # # # # # # if __name__ == "__main__":
# # # # # # #     # 数据库连接配置
# # # # # # #     DB_CONFIG = {
# # # # # # #         "host": "10.231.2.166",
# # # # # # #         "port": 5432,  # 修正为整数类型
# # # # # # #         "dbname": "bird",
# # # # # # #         "user": "postgres",
# # # # # # #         "password": "zhangxiang2025"
# # # # # # #     }
    
# # # # # # #     # 文件路径配置
# # # # # # #     SQL_FILE_PATH = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite.sql"
# # # # # # #     RESULT_DIR = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_pgsql_result"
    
# # # # # # #     # 记录开始时间
# # # # # # #     start_time = datetime.now()
# # # # # # #     logging.info(f"===== 开始执行SQL脚本 =====")
# # # # # # #     logging.info(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
# # # # # # #     # 执行主函数
# # # # # # #     execute_sql_commands(
# # # # # # #         host=DB_CONFIG["host"],
# # # # # # #         port=DB_CONFIG["port"],
# # # # # # #         dbname=DB_CONFIG["dbname"],
# # # # # # #         user=DB_CONFIG["user"],
# # # # # # #         password=DB_CONFIG["password"],
# # # # # # #         sql_file_path=SQL_FILE_PATH,
# # # # # # #         result_dir=RESULT_DIR
# # # # # # #     )
    
# # # # # # #     # 记录结束时间
# # # # # # #     end_time = datetime.now()
# # # # # # #     total_time = (end_time - start_time).total_seconds()
# # # # # # #     logging.info(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
# # # # # # #     logging.info(f"总耗时: {total_time:.4f}秒")
# # # # # # #     logging.info(f"===== SQL脚本执行结束 =====")
    
    
# # # # # # #2.


# # # # # import json
# # # # # import os

# # # # # def extract_matching_sql_dicts():
# # # # #     # 文件路径配置
# # # # #     sqlite_json_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite.json"
# # # # #     true_json_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_pgsql_result\true.json"
# # # # #     false_json_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_pgsql_result\false.json"
# # # # #     result_folder = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_pgsql_result"
# # # # #     do_json_path = os.path.join(result_folder, "do.json")
# # # # #     undo_json_path = os.path.join(result_folder, "undo.json")
    
# # # # #     try:
# # # # #         # 确保结果文件夹存在
# # # # #         os.makedirs(result_folder, exist_ok=True)
        
# # # # #         # 读取sqlite.json数据
# # # # #         with open(sqlite_json_path, 'r', encoding='utf-8') as f:
# # # # #             sqlite_data = json.load(f)
# # # # #             if not isinstance(sqlite_data, list):
# # # # #                 print("错误: sqlite.json中的数据不是列表格式")
# # # # #                 return
        
# # # # #         # 读取true.json并提取sql语句集合
# # # # #         with open(true_json_path, 'r', encoding='utf-8') as f:
# # # # #             true_data = json.load(f)
# # # # #             true_sqls = {item['sql'].strip() for item in true_data if 'sql' in item}
        
# # # # #         # 读取false.json并提取sql语句集合
# # # # #         with open(false_json_path, 'r', encoding='utf-8') as f:
# # # # #             false_data = json.load(f)
# # # # #             false_sqls = {item['sql'].strip() for item in false_data if 'sql' in item}
        
# # # # #         # 筛选匹配的数据
# # # # #         do_data = []  # 与true.json中的sql匹配
# # # # #         undo_data = []  # 与false.json中的sql匹配
        
# # # # #         for item in sqlite_data:
# # # # #             if 'SQL' in item:
# # # # #                 sql_content = item['SQL'].strip()
# # # # #                 if sql_content in true_sqls:
# # # # #                     do_data.append(item)
# # # # #                 if sql_content in false_sqls:
# # # # #                     undo_data.append(item)
        
# # # # #         # 保存结果
# # # # #         with open(do_json_path, 'w', encoding='utf-8') as f:
# # # # #             json.dump(do_data, f, ensure_ascii=False, indent=2)
        
# # # # #         with open(undo_json_path, 'w', encoding='utf-8') as f:
# # # # #             json.dump(undo_data, f, ensure_ascii=False, indent=2)
        
# # # # #         print(f"处理完成:")
# # # # #         print(f"- 与true.json匹配的记录数: {len(do_data)}, 已保存到 {do_json_path}")
# # # # #         print(f"- 与false.json匹配的记录数: {len(undo_data)}, 已保存到 {undo_json_path}")
        
# # # # #     except FileNotFoundError as e:
# # # # #         print(f"错误: 未找到文件 - {e.filename}")
# # # # #     except json.JSONDecodeError as e:
# # # # #         print(f"错误: JSON解析失败 - {e}")
# # # # #     except Exception as e:
# # # # #         print(f"发生意外错误: {str(e)}")

# # # # # if __name__ == "__main__":
# # # # #     extract_matching_sql_dicts()
        
    
    
# # # # # #3.


# # # # # # import json
# # # # # # import os

# # # # # # def remove_trailing_semicolon(sql):
# # # # # #     """去除SQL语句结尾的分号，如果存在的话"""
# # # # # #     # 先去除首尾空白，再检查最后一个字符是否为分号
# # # # # #     stripped_sql = sql.strip()
# # # # # #     if stripped_sql.endswith(';'):
# # # # # #         return stripped_sql[:-1].strip()  # 去除分号后再strip一次，确保没有多余空格
# # # # # #     return sql

# # # # # # def process_json_file(file_path):
# # # # # #     """处理JSON文件，去除所有sql字段结尾的分号"""
# # # # # #     try:
# # # # # #         # 检查文件是否存在
# # # # # #         if not os.path.exists(file_path):
# # # # # #             print(f"错误：文件不存在 - {file_path}")
# # # # # #             return False
        
# # # # # #         # 读取文件内容
# # # # # #         with open(file_path, 'r', encoding='utf-8') as f:
# # # # # #             data = json.load(f)
        
# # # # # #         # 验证数据格式是否为列表
# # # # # #         if not isinstance(data, list):
# # # # # #             print(f"错误：{file_path} 内容不是列表类型")
# # # # # #             return False
        
# # # # # #         # 处理每个条目
# # # # # #         modified_count = 0
# # # # # #         for item in data:
# # # # # #             # 检查是否包含sql字段且为字符串
# # # # # #             if isinstance(item, dict) and 'sql' in item and isinstance(item['sql'], str):
# # # # # #                 original_sql = item['sql']
# # # # # #                 modified_sql = remove_trailing_semicolon(original_sql)
# # # # # #                 if original_sql != modified_sql:
# # # # # #                     item['sql'] = modified_sql
# # # # # #                     modified_count += 1
        
# # # # # #         # 保存修改后的内容
# # # # # #         with open(file_path, 'w', encoding='utf-8') as f:
# # # # # #             json.dump(data, f, ensure_ascii=False, indent=2)
        
# # # # # #         print(f"处理完成：{file_path}，修改了 {modified_count} 条SQL语句")
# # # # # #         return True
    
# # # # # #     except json.JSONDecodeError:
# # # # # #         print(f"错误：{file_path} 不是有效的JSON文件")
# # # # # #         return False
# # # # # #     except Exception as e:
# # # # # #         print(f"处理 {file_path} 时出错：{str(e)}")
# # # # # #         return False

# # # # # # if __name__ == "__main__":
# # # # # #     # 定义要处理的文件路径
# # # # # #     false_json_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_pgsql_result\false.json"
# # # # # #     true_json_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_pgsql_result\true.json"
    
# # # # # #     # 处理两个文件
# # # # # #     process_json_file(false_json_path)
# # # # # #     process_json_file(true_json_path)
    
# # # # # #     print("所有文件处理完毕")
    
    
# # # # #10.


# # # # import json
# # # # import os

# # # # def replace_sql_key_with_sqlite():
# # # #     # 文件路径
# # # #     file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_pgsql_result\undo.json"
    
# # # #     try:
# # # #         # 检查文件是否存在
# # # #         if not os.path.exists(file_path):
# # # #             print(f"错误：文件不存在 - {file_path}")
# # # #             return
        
# # # #         # 读取JSON文件内容
# # # #         with open(file_path, 'r', encoding='utf-8') as f:
# # # #             data = json.load(f)
        
# # # #         # 检查数据是否为列表
# # # #         if not isinstance(data, list):
# # # #             print("错误：JSON文件内容不是列表格式")
# # # #             return
        
# # # #         # 替换每个字典中的"SQL"键为"sqlite"
# # # #         modified_data = []
# # # #         for item in data:
# # # #             if isinstance(item, dict) and "SQL" in item:
# # # #                 # 创建新字典，复制所有键值对
# # # #                 new_item = item.copy()
# # # #                 # 将"SQL"的值赋给"sqlite"键
# # # #                 new_item["sqlite"] = new_item.pop("SQL")
# # # #                 modified_data.append(new_item)
# # # #             else:
# # # #                 # 不包含"SQL"键的项直接添加
# # # #                 modified_data.append(item)
        
# # # #         # 将修改后的数据写回文件
# # # #         with open(file_path, 'w', encoding='utf-8') as f:
# # # #             json.dump(modified_data, f, ensure_ascii=False, indent=2)
        
# # # #         print(f"成功将文件中所有'SQL'键替换为'sqlite'键：{file_path}")
    
# # # #     except json.JSONDecodeError:
# # # #         print(f"错误：文件 {file_path} 不是有效的JSON格式")
# # # #     except Exception as e:
# # # #         print(f"处理文件时发生错误：{str(e)}")

# # # # if __name__ == "__main__":
# # # #     replace_sql_key_with_sqlite()
    
    
    
# # # #11.


# # # import json
# # # import os

# # # def main():
# # #     # 定义文件路径
# # #     pg_json_path = r"C:\copy\code\minidev\MINIDEV\pg\pg.json"
# # #     undo_json_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_pgsql_result\undo.json"
    
# # #     try:
# # #         # 读取pg.json文件
# # #         with open(pg_json_path, 'r', encoding='utf-8') as f:
# # #             pg_data = json.load(f)
        
# # #         # 读取undo.json文件
# # #         with open(undo_json_path, 'r', encoding='utf-8') as f:
# # #             undo_data = json.load(f)
            
# # #     except FileNotFoundError as e:
# # #         print(f"错误：找不到文件 - {e.filename}")
# # #         return
# # #     except json.JSONDecodeError:
# # #         print("错误：文件不是有效的JSON格式")
# # #         return
# # #     except Exception as e:
# # #         print(f"读取文件时发生错误：{str(e)}")
# # #         return
    
# # #     # 创建pg数据中问题到SQL的映射
# # #     question_to_sql = {}
# # #     for item in pg_data:
# # #         if "question" in item and "SQL" in item:
# # #             question_to_sql[item["question"]] = item["SQL"]
    
# # #     # 统计添加的postgres数量
# # #     added_count = 0
    
# # #     # 处理undo数据，添加postgres字段
# # #     for item in undo_data:
# # #         if "question" in item and item["question"] in question_to_sql:
# # #             # 只添加不存在的postgres字段
# # #             if "postgres" not in item:
# # #                 item["postgres"] = question_to_sql[item["question"]]
# # #                 added_count += 1
    
# # #     try:
# # #         # 保存修改后的undo.json
# # #         with open(undo_json_path, 'w', encoding='utf-8') as f:
# # #             json.dump(undo_data, f, ensure_ascii=False, indent=4)
        
# # #         print(f"操作完成，共向undo.json添加了 {added_count} 个postgres字段")
        
# # #     except Exception as e:
# # #         print(f"写入文件时发生错误：{str(e)}")
# # #         return

# # # if __name__ == "__main__":
# # #     main()

    
    
# # #12.



# # import json
# # import os
# # from shutil import copy2

# # def rename_json_key(file_path, old_key, new_key):
# #     """
# #     将JSON文件中指定的旧键名替换为新键名，并创建备份文件
    
# #     参数:
# #         file_path (str): JSON文件的完整路径
# #         old_key (str): 需要替换的旧键名
# #         new_key (str): 替换后的新键名
# #     返回:
# #         bool: 操作是否成功
# #     """
# #     # 验证文件是否存在
# #     if not os.path.exists(file_path):
# #         print(f"错误：文件不存在 - {file_path}")
# #         return False
    
# #     # 验证是否为有效文件
# #     if not os.path.isfile(file_path):
# #         print(f"错误：{file_path} 不是有效文件")
# #         return False
    
# #     # 创建备份文件
# #     backup_path = f"{file_path}.bak"
# #     try:
# #         copy2(file_path, backup_path)
# #         print(f"已创建备份文件：{backup_path}")
# #     except Exception as e:
# #         print(f"警告：创建备份文件失败 - {str(e)}，继续执行但存在风险")
    
# #     # 读取并解析JSON数据
# #     try:
# #         with open(file_path, 'r', encoding='utf-8') as f:
# #             data = json.load(f)
# #     except json.JSONDecodeError as e:
# #         print(f"错误：JSON解析失败 - {str(e)}（文件：{file_path}）")
# #         return False
# #     except Exception as e:
# #         print(f"错误：读取文件失败 - {str(e)}（文件：{file_path}）")
# #         return False
    
# #     # 统一处理列表和字典类型的JSON数据
# #     items = data if isinstance(data, list) else [data]
    
# #     # 替换键名并计数
# #     replace_count = 0
# #     for item in items:
# #         if isinstance(item, dict) and old_key in item:
# #             # 保留值并替换键名
# #             item[new_key] = item.pop(old_key)
# #             replace_count += 1
    
# #     # 保存修改后的内容
# #     try:
# #         with open(file_path, 'w', encoding='utf-8') as f:
# #             json.dump(data, f, ensure_ascii=False, indent=2)
# #         print(f"文件处理完成：{file_path}")
# #         print(f"成功将 {replace_count} 处 '{old_key}' 替换为 '{new_key}'")
# #         return True
# #     except Exception as e:
# #         print(f"错误：保存文件失败 - {str(e)}（文件：{file_path}）")
# #         return False


# # if __name__ == "__main__":
# #     # 配置文件路径和键名
# #     json_file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_pgsql_result\do.json"
# #     old_key = "SQL"
# #     new_key = "sqlite"
    
# #     # 执行替换操作
# #     rename_json_key(json_file_path, old_key, new_key)



# #13.



# import json
# import os
# import re
# from shutil import copy2

# def normalize_text(text):
#     """标准化文本，处理空格、标点和大小写差异，提高匹配准确性"""
#     if not text:
#         return ""
#     # 转换为小写
#     text = text.lower()
#     # 移除标点符号和多余空格
#     text = re.sub(r'[^\w\s]', '', text)  # 保留字母、数字和空格
#     text = re.sub(r'\s+', ' ', text).strip()  # 合并多个空格为一个
#     return text

# def load_json_file(file_path):
#     """加载JSON文件并返回解析后的数据，包含完整的错误处理"""
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

# def supplement_postgres_statements(pg_source_path, target_path):
#     """
#     根据question匹配，将pg.json中的SQL语句补充到目标文件，并重命名键为postgres
#     """
#     # 加载源文件和目标文件数据
#     pg_data = load_json_file(pg_source_path)
#     target_data = load_json_file(target_path)
    
#     if not pg_data or not target_data:
#         print("无法加载源文件或目标文件，程序退出")
#         return
    
#     # 验证数据格式是否为列表
#     if not isinstance(pg_data, list):
#         print("错误：pg源文件数据必须是列表格式")
#         return
#     if not isinstance(target_data, list):
#         print("错误：目标文件数据必须是列表格式")
#         return
    
#     # 构建question到SQL语句的映射（支持多种键名）
#     question_to_sql = {}
#     source_questions = []  # 用于展示源文件示例
    
#     for item in pg_data:
#         if not isinstance(item, dict):
#             continue
        
#         # 提取question（支持多种可能的键名）
#         question_keys = ["question", "Question", "problem", "query"]
#         question_text = None
#         for key in question_keys:
#             if key in item and item[key]:
#                 question_text = str(item[key])
#                 break
        
#         # 提取SQL语句（支持多种可能的键名）
#         sql_keys = ["SQL", "sql", "postgres", "PostgreSQL"]
#         sql_stmt = None
#         for key in sql_keys:
#             if key in item and item[key]:
#                 sql_stmt = str(item[key])
#                 break
        
#         if question_text and sql_stmt:
#             normalized_question = normalize_text(question_text)
#             question_to_sql[normalized_question] = {
#                 "original_question": question_text,
#                 "sql_stmt": sql_stmt
#             }
#             # 记录前3个示例用于展示
#             if len(source_questions) < 3:
#                 source_questions.append(question_text[:50] + "...")
    
#     print(f"已从pg源文件中加载 {len(question_to_sql)} 条有效记录（包含question和SQL）")
#     if source_questions:
#         print(f"源文件question示例：{source_questions}")
    
#     # 创建目标文件备份
#     backup_path = f"{target_path}.bak"
#     try:
#         copy2(target_path, backup_path)
#         print(f"已创建目标文件备份：{backup_path}")
#     except Exception as e:
#         print(f"警告：创建备份文件失败 - {str(e)}，继续执行但存在风险")
    
#     # 遍历目标文件，补充postgres语句
#     updated_count = 0
#     target_questions = []  # 目标文件question示例
#     no_postgres_count = 0  # 缺少postgres的条目数
#     unmatched_questions = []  # 未匹配的question记录
    
#     for idx, item in enumerate(target_data, 1):  # 从1开始计数，方便定位
#         if not isinstance(item, dict):
#             continue
        
#         # 提取目标文件的question
#         target_question = item.get("question", "")
#         current_postgres = item.get("postgres", "")
        
#         # 记录目标文件示例
#         if target_question and len(target_questions) < 3:
#             target_questions.append(target_question[:50] + "...")
        
#         # 统计缺少postgres的条目
#         if not current_postgres:
#             no_postgres_count += 1
        
#         # 尝试匹配并补充
#         if target_question:
#             normalized_target = normalize_text(target_question)
#             if normalized_target in question_to_sql:
#                 # 找到匹配项
#                 source_info = question_to_sql[normalized_target]
#                 item["postgres"] = source_info["sql_stmt"]  # 键名改为postgres
#                 updated_count += 1
#                 print(f"匹配成功（序号{idx}）：\n目标question：{target_question[:50]}...\n源question：{source_info['original_question'][:50]}...")
#             else:
#                 # 记录未匹配的question
#                 unmatched_questions.append({
#                     "序号": idx,
#                     "question": target_question[:200] + ("..." if len(target_question) > 200 else ""),
#                     "normalized": normalized_target[:200] + ("..." if len(normalized_target) > 200 else ""),
#                     "原因": "源文件中无匹配的标准化question"
#                 })
#         else:
#             # 记录无question的条目
#             unmatched_questions.append({
#                 "序号": idx,
#                 "question": "无（目标条目缺少question键）",
#                 "normalized": "",
#                 "原因": "目标文件条目缺少question键"
#             })
    
#     # 输出匹配诊断信息
#     print("\n===== 匹配诊断 =====")
#     print(f"目标文件总条目数：{len(target_data)}")
#     print(f"目标文件中缺少postgres的条目数：{no_postgres_count}")
#     print(f"成功补充postgres语句：{updated_count}条")
#     if target_questions:
#         print(f"目标文件question示例：{target_questions}")
    
#     # 输出未匹配的question信息
#     print(f"\n===== 未匹配的question =====")
#     print(f"未匹配总数：{len(unmatched_questions)}条")
#     # 显示前10条未匹配记录
#     for info in unmatched_questions[:10]:
#         print(f"\n序号：{info['序号']}")
#         print(f"question：{info['question']}")
#         if info["normalized"]:
#             print(f"标准化后：{info['normalized']}")
#         print(f"原因：{info['原因']}")
#     if len(unmatched_questions) > 10:
#         print(f"\n... 省略 {len(unmatched_questions) - 10} 条记录")
    
#     # 保存更新后的目标文件
#     try:
#         with open(target_path, 'w', encoding='utf-8') as f:
#             json.dump(target_data, f, ensure_ascii=False, indent=2)
#         print(f"\n目标文件已更新并保存：{target_path}")
#         print(f"最终补充结果：成功添加 {updated_count} 条postgres语句")
#     except Exception as e:
#         print(f"错误：保存目标文件失败 - {str(e)}")


# if __name__ == "__main__":
#     # 定义文件路径
#     pg_source_file = r"C:\copy\code\minidev\MINIDEV\pg\other\pg.json"
#     target_file = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_pgsql_result\do.json"
    
#     # 执行补充操作
#     supplement_postgres_statements(pg_source_file, target_file)

#统计do.json中的question数目

# import json

# # JSON文件路径 356
# json_file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_pgsql_result\run_result\do.json"

# try:
#     # 打开并加载JSON文件
#     with open(json_file_path, 'r', encoding='utf-8') as file:
#         data = json.load(file)
    
#     # 检查数据是否为列表类型（根据提供的文件样式）
#     if isinstance(data, list):
#         # 统计包含"question"字段的条目数量
#         question_count = 0
#         for item in data:
#             if isinstance(item, dict) and "question" in item:
#                 question_count += 1
        
#         # 输出结果
#         print(f"文件中共有 {question_count} 个question")
#     else:
#         print(f"JSON数据格式不符合预期，类型为: {type(data)}")

# except FileNotFoundError:
#     print(f"文件 {json_file_path} 未找到")
# except json.JSONDecodeError:
#     print(f"文件 {json_file_path} 不是有效的JSON格式")
# except Exception as e:
#     print(f"处理文件时发生错误: {e}")
    
    
#统计undo.json中的question数目

import json

# JSON文件路径 144
json_file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_pgsql_result\run_result\undo.json"

try:
    # 打开并加载JSON文件
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # 检查数据是否为列表类型（根据提供的文件样式）
    if isinstance(data, list):
        # 统计包含"question"字段的条目数量
        question_count = 0
        for item in data:
            if isinstance(item, dict) and "question" in item:
                question_count += 1
        
        # 输出结果
        print(f"文件中共有 {question_count} 个question")
    else:
        print(f"JSON数据格式不符合预期，类型为: {type(data)}")

except FileNotFoundError:
    print(f"文件 {json_file_path} 未找到")
except json.JSONDecodeError:
    print(f"文件 {json_file_path} 不是有效的JSON格式")
except Exception as e:
    print(f"处理文件时发生错误: {e}")