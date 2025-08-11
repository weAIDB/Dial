# # # # # # # # # # #归类
# # # # # # # # # # #归类

# # # # # # # # # # import json
# # # # # # # # # # import os

# # # # # # # # # # def load_json_file(file_path):
# # # # # # # # # #     """加载JSON文件并验证有效性"""
# # # # # # # # # #     if not os.path.exists(file_path):
# # # # # # # # # #         print(f"错误：文件不存在 - {file_path}")
# # # # # # # # # #         return None
# # # # # # # # # #     if not os.path.isfile(file_path):
# # # # # # # # # #         print(f"错误：不是有效文件 - {file_path}")
# # # # # # # # # #         return None

# # # # # # # # # #     try:
# # # # # # # # # #         with open(file_path, 'r', encoding='utf-8') as f:
# # # # # # # # # #             return json.load(f)
# # # # # # # # # #     except json.JSONDecodeError as e:
# # # # # # # # # #         print(f"错误：JSON解析失败 - {str(e)}（文件：{file_path}）")
# # # # # # # # # #         return None
# # # # # # # # # #     except Exception as e:
# # # # # # # # # #         print(f"错误：加载文件失败 - {str(e)}（文件：{file_path}）")
# # # # # # # # # #         return None

# # # # # # # # # # def save_json_file(data, file_path, backup=True):
# # # # # # # # # #     """保存JSON文件并创建备份"""
# # # # # # # # # #     try:
# # # # # # # # # #         # 创建备份文件
# # # # # # # # # #         if backup and os.path.exists(file_path):
# # # # # # # # # #             backup_path = f"{file_path}.bak"
# # # # # # # # # #             with open(file_path, 'r', encoding='utf-8') as f_in, \
# # # # # # # # # #                  open(backup_path, 'w', encoding='utf-8') as f_out:
# # # # # # # # # #                 f_out.write(f_in.read())
# # # # # # # # # #             print(f"已创建备份文件：{backup_path}")
        
# # # # # # # # # #         # 保存处理后的数据
# # # # # # # # # #         with open(file_path, 'w', encoding='utf-8') as f:
# # # # # # # # # #             json.dump(data, f, ensure_ascii=False, indent=2)
# # # # # # # # # #         print(f"文件已保存至：{file_path}")
# # # # # # # # # #         return True
# # # # # # # # # #     except Exception as e:
# # # # # # # # # #         print(f"错误：保存文件失败 - {str(e)}")
# # # # # # # # # #         return False

# # # # # # # # # # def create_category_mapping():
# # # # # # # # # #     """创建原始差异类型到16个大类的映射关系"""
# # # # # # # # # #     return {
# # # # # # # # # #         # 1. 数据去重（DISTINCT 相关）
# # # # # # # # # #         "DISTINCT语法": "数据去重（DISTINCT 相关）",
        
# # # # # # # # # #         # 2. 分组聚合（GROUP BY 子句）
# # # # # # # # # #         "GROUP BY子句": "分组聚合（GROUP BY 子句）",
# # # # # # # # # #         "GROUP BY子句格式": "分组聚合（GROUP BY 子句）",
        
# # # # # # # # # #         # 3. 分组后的筛选（HAVING 子句）
# # # # # # # # # #         "HAVING子句": "分组后的筛选（HAVING 子句）",
        
# # # # # # # # # #         # 4. 聚合函数与引用
# # # # # # # # # #         "聚合函数引用": "聚合函数与引用",
# # # # # # # # # #         "聚合查询结构": "聚合函数与引用",
        
# # # # # # # # # #         # 5. 表连接（JOIN）相关
# # # # # # # # # #         "JOIN子句格式": "表连接（JOIN）相关",
# # # # # # # # # #         "JOIN条件中的列引用": "表连接（JOIN）相关",
# # # # # # # # # #         "JOIN条件引用": "表连接（JOIN）相关",
# # # # # # # # # #         "JOIN条件格式": "表连接（JOIN）相关",
# # # # # # # # # #         "JOIN条件语法": "表连接（JOIN）相关",
# # # # # # # # # #         "JOIN语法": "表连接（JOIN）相关",
# # # # # # # # # #         "连接条件引用": "表连接（JOIN）相关",
        
# # # # # # # # # #         # 6. 模式匹配（LIKE）相关
# # # # # # # # # #         "LIKE子句的字符串匹配": "模式匹配（LIKE）相关",
# # # # # # # # # #         "LIKE条件语法": "模式匹配（LIKE）相关",
# # # # # # # # # #         "LIKE模式匹配": "模式匹配（LIKE）相关",
        
# # # # # # # # # #         # 7. 分页（LIMIT）语法
# # # # # # # # # #         "LIMIT语法": "分页（LIMIT）语法",
        
# # # # # # # # # #         # 8. 空值（NULL）处理
# # # # # # # # # #         "NULLS排序处理": "空值（NULL）处理",
# # # # # # # # # #         "NULL值排序": "空值（NULL）处理",
# # # # # # # # # #         "NULL值排序处理": "空值（NULL）处理",
# # # # # # # # # #         "NULL值排序语法": "空值（NULL）处理",
# # # # # # # # # #         "NULL处理语法": "空值（NULL）处理",
# # # # # # # # # #         "NULL排序": "空值（NULL）处理",
# # # # # # # # # #         "NULL排序处理": "空值（NULL）处理",
# # # # # # # # # #         "NULL排序语法": "空值（NULL）处理",
# # # # # # # # # #         "NULL检查语法": "空值（NULL）处理",
# # # # # # # # # #         "空值检查语法": "空值（NULL）处理",
# # # # # # # # # #         "ORDER BY子句NULL处理": "空值（NULL）处理",
# # # # # # # # # #         "排序空值处理": "空值（NULL）处理",
# # # # # # # # # #         "排序选项": "空值（NULL）处理",
        
# # # # # # # # # #         # 9. 排序（ORDER BY）基础语法
# # # # # # # # # #         "ORDER BY子句": "排序（ORDER BY）基础语法",
# # # # # # # # # #         "ORDER BY引用": "排序（ORDER BY）基础语法",
# # # # # # # # # #         "排序与筛选方式": "排序（ORDER BY）基础语法",
        
# # # # # # # # # #         # 10. 筛选条件（WHERE）相关
# # # # # # # # # #         "WHERE子句引用": "筛选条件相关",
# # # # # # # # # #         "WHERE条件中的列引用": "筛选条件相关",
# # # # # # # # # #         "WHERE条件列引用": "筛选条件相关",
# # # # # # # # # #         "WHERE条件引用": "筛选条件相关",
# # # # # # # # # #         "WHERE条件语法": "筛选条件相关",
# # # # # # # # # #         "条件值引用": "筛选条件相关",
# # # # # # # # # #         "条件列引用": "筛选条件相关",
# # # # # # # # # #         "条件表达式": "筛选条件相关",
# # # # # # # # # #         "条件表达式中的列引用": "筛选条件相关",
# # # # # # # # # #         "条件表达式引用": "筛选条件相关",
# # # # # # # # # #         "条件表达式语法": "筛选条件相关",
# # # # # # # # # #         "筛选条件（WHERE）相关":"筛选条件相关",
# # # # # # # # # #         # 11. 列与表引用规则
# # # # # # # # # #         "列别名引用": "列与表引用规则",
# # # # # # # # # #         "列别名引用方式": "列与表引用规则",
# # # # # # # # # #         "列名引用": "列与表引用规则",
# # # # # # # # # #         "列名引用符号": "列与表引用规则",
# # # # # # # # # #         "列名引用语法": "列与表引用规则",
# # # # # # # # # #         "列引用": "列与表引用规则",
# # # # # # # # # #         "列引用格式": "列与表引用规则",
# # # # # # # # # #         "列引用符号": "列与表引用规则",
# # # # # # # # # #         "列引用语法": "列与表引用规则",
# # # # # # # # # #         "特殊列名引用语法": "列与表引用规则",
# # # # # # # # # #         "表别名引用": "列与表引用规则",
# # # # # # # # # #         "表别名引用方式": "列与表引用规则",
# # # # # # # # # #         "表别名引用语法": "列与表引用规则",
# # # # # # # # # #         "表名/列名引用语法": "列与表引用规则",
# # # # # # # # # #         "表名和列名引用": "列与表引用规则",
# # # # # # # # # #         "表名引用": "列与表引用规则",
# # # # # # # # # #         "表名引用方式": "列与表引用规则",
# # # # # # # # # #         "表名引用符号": "列与表引用规则",
# # # # # # # # # #         "表名引用语法": "列与表引用规则",
# # # # # # # # # #         "表引用": "列与表引用规则",
# # # # # # # # # #         "表引用语法": "列与表引用规则",
# # # # # # # # # #         "子查询列引用": "列与表引用规则",
# # # # # # # # # #         "子查询别名命名": "列与表引用规则",
# # # # # # # # # #         "子查询别名引用": "列与表引用规则",
# # # # # # # # # #         "派生表别名语法": "列与表引用规则",
        
# # # # # # # # # #         # 12. 字符串处理
# # # # # # # # # #         "字符串与数字比较": "字符串处理",
# # # # # # # # # #         "字符串分割函数": "字符串处理",
# # # # # # # # # #         "字符串常量": "字符串处理",
# # # # # # # # # #         "字符串常量语法": "字符串处理",
# # # # # # # # # #         "字符串截取函数": "字符串处理",
# # # # # # # # # #         "字符串比较": "字符串处理",
# # # # # # # # # #         "字符串转日期": "字符串处理",
# # # # # # # # # #         "年份格式字符串": "字符串处理",
# # # # # # # # # #         "引号风格": "字符串处理",
        
# # # # # # # # # #         # 13. 数值处理
# # # # # # # # # #         "数值比较": "数值处理",
# # # # # # # # # #         "数值类型处理": "数值处理",
# # # # # # # # # #         "浮点数类型": "数值处理",
# # # # # # # # # #         "浮点数类型转换": "数值处理",
# # # # # # # # # #         "除零处理": "数值处理",
# # # # # # # # # #         "除零错误处理": "数值处理",
        
# # # # # # # # # #         # 14. 日期时间处理
# # # # # # # # # #         "当前日期函数": "日期时间处理",
# # # # # # # # # #         "当前时间戳函数": "日期时间处理",
# # # # # # # # # #         "日期处理": "日期时间处理",
# # # # # # # # # #         "日期处理函数": "日期时间处理",
# # # # # # # # # #         "日期提取函数": "日期时间处理",
# # # # # # # # # #         "日期时间处理": "日期时间处理",
# # # # # # # # # #         "日期格式化函数": "日期时间处理",
# # # # # # # # # #         "日期格式化模式": "日期时间处理",
# # # # # # # # # #         "日期格式匹配": "日期时间处理",
# # # # # # # # # #         "日期格式处理": "日期时间处理",
# # # # # # # # # #         "日期比较": "日期时间处理",
# # # # # # # # # #         "日期类型转换": "日期时间处理",
# # # # # # # # # #         "日期计算": "日期时间处理",
# # # # # # # # # #         "日期计算语法": "日期时间处理",
# # # # # # # # # #         "时间处理函数": "日期时间处理",
# # # # # # # # # #         "时间戳类型转换": "日期时间处理",
# # # # # # # # # #         "时间类型转换": "日期时间处理",
# # # # # # # # # #         "时间间隔处理": "日期时间处理",
# # # # # # # # # #         "年龄计算函数": "日期时间处理",
# # # # # # # # # #         "年龄计算方式": "日期时间处理",
# # # # # # # # # #         "年龄计算语法": "日期时间处理",
        
# # # # # # # # # #         # 15. 类型转换
# # # # # # # # # #         "数据类型转换": "类型转换",
# # # # # # # # # #         "类型转换": "类型转换",
# # # # # # # # # #         "类型转换函数": "类型转换",
# # # # # # # # # #         "类型转换语法": "类型转换",
        
# # # # # # # # # #         # 16. 分析失败
# # # # # # # # # #         "分析失败": "分析失败"
# # # # # # # # # #     }

# # # # # # # # # # def rewrite_differences(data, category_mapping):
# # # # # # # # # #     """将JSON中的difference字段重写为对应的大类"""
# # # # # # # # # #     if not data or not isinstance(data, list):
# # # # # # # # # #         return data

# # # # # # # # # #     rewritten_data = []
# # # # # # # # # #     for item in data:
# # # # # # # # # #         # 处理每条数据中的syntax_differences
# # # # # # # # # #         if "syntax_differences" in item and isinstance(item["syntax_differences"], list):
# # # # # # # # # #             new_syntax_diffs = []
# # # # # # # # # #             for diff in item["syntax_differences"]:
# # # # # # # # # #                 if "difference" in diff:
# # # # # # # # # #                     # 替换为大类名称
# # # # # # # # # #                     original_diff = diff["difference"]
# # # # # # # # # #                     new_diff = category_mapping.get(original_diff, original_diff)
# # # # # # # # # #                     updated_diff = diff.copy()
# # # # # # # # # #                     updated_diff["difference"] = new_diff
# # # # # # # # # #                     new_syntax_diffs.append(updated_diff)
# # # # # # # # # #                 else:
# # # # # # # # # #                     new_syntax_diffs.append(diff)
# # # # # # # # # #             item["syntax_differences"] = new_syntax_diffs

# # # # # # # # # #         # 同步更新causing_part字段
# # # # # # # # # #         if "causing_part" in item:
# # # # # # # # # #             causing_part = item["causing_part"]
# # # # # # # # # #             for original, target in category_mapping.items():
# # # # # # # # # #                 if original in causing_part:
# # # # # # # # # #                     causing_part = causing_part.replace(original, target)
# # # # # # # # # #             item["causing_part"] = causing_part

# # # # # # # # # #         rewritten_data.append(item)
    
# # # # # # # # # #     return rewritten_data

# # # # # # # # # # def main():
# # # # # # # # # #     # 目标文件路径
# # # # # # # # # #     file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\conclude\sqlite_mysql_difference.json"
    
# # # # # # # # # #     # 加载文件数据
# # # # # # # # # #     data = load_json_file(file_path)
# # # # # # # # # #     if not data:
# # # # # # # # # #         return
    
# # # # # # # # # #     # 创建类别映射表
# # # # # # # # # #     category_mapping = create_category_mapping()
    
# # # # # # # # # #     # 重写差异类型
# # # # # # # # # #     updated_data = rewrite_differences(data, category_mapping)
    
# # # # # # # # # #     # 保存结果
# # # # # # # # # #     save_json_file(updated_data, file_path)

# # # # # # # # # # if __name__ == "__main__":
# # # # # # # # # #     main()


# # # # # # # # # #再次分析


# # # # # # # # # import json
# # # # # # # # # import requests
# # # # # # # # # import os
# # # # # # # # # import shutil
# # # # # # # # # from time import sleep
# # # # # # # # # import socket  # 用于网络调试

# # # # # # # # # # 配置参数
# # # # # # # # # TARGET_FILE = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\conclude\sqlite_mysql_difference.json"
# # # # # # # # # API_KEY = "sk-578f63b08e74438692e3ebdb42b49934"  # 注意：实际使用中不要暴露密钥
# # # # # # # # # API_URL = "https://api.deepseek.com/chat/completions"
# # # # # # # # # MODEL_NAME = "deepseek-chat"  # 使用DeepSeek Chat 2.0模型
# # # # # # # # # BACKUP_SUFFIX = ".backup"

# # # # # # # # # # 网络配置（根据实际环境修改）
# # # # # # # # # USE_PROXY = False  # 如果需要代理，设为True
# # # # # # # # # PROXY = {
# # # # # # # # #     "http": "http://your-proxy:port",
# # # # # # # # #     "https": "https://your-proxy:port"
# # # # # # # # # }
# # # # # # # # # VERIFY_SSL = True  # 若SSL验证失败，可临时设为False（不推荐生产环境）


# # # # # # # # # def test_api_connectivity():
# # # # # # # # #     """测试API端点的网络连通性"""
# # # # # # # # #     print("\n=== 测试API连通性 ===")
# # # # # # # # #     try:
# # # # # # # # #         # 测试DNS解析
# # # # # # # # #         ip_address = socket.gethostbyname("api.deepseek.com")
# # # # # # # # #         print(f"DNS解析成功: api.deepseek.com -> {ip_address}")
        
# # # # # # # # #         # 测试TCP连接
# # # # # # # # #         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
# # # # # # # # #             s.settimeout(10)
# # # # # # # # #             result = s.connect_ex((ip_address, 443))
# # # # # # # # #             if result == 0:
# # # # # # # # #                 print("TCP连接成功（443端口可达）")
# # # # # # # # #             else:
# # # # # # # # #                 print(f"TCP连接失败，错误码: {result}（可能被防火墙阻止）")
# # # # # # # # #     except Exception as e:
# # # # # # # # #         print(f"网络连通性测试失败: {str(e)}")


# # # # # # # # # def create_backup(file_path):
# # # # # # # # #     """创建文件备份，防止数据丢失"""
# # # # # # # # #     backup_path = f"{file_path}{BACKUP_SUFFIX}"
# # # # # # # # #     try:
# # # # # # # # #         shutil.copy2(file_path, backup_path)
# # # # # # # # #         print(f"已创建备份文件: {backup_path}")
# # # # # # # # #         return True
# # # # # # # # #     except Exception as e:
# # # # # # # # #         print(f"创建备份失败: {str(e)}")
# # # # # # # # #         return False


# # # # # # # # # def load_json_data(file_path):
# # # # # # # # #     """加载并验证JSON数据"""
# # # # # # # # #     if not os.path.exists(file_path):
# # # # # # # # #         print(f"错误: 文件不存在 - {file_path}")
# # # # # # # # #         return None
    
# # # # # # # # #     try:
# # # # # # # # #         with open(file_path, 'r', encoding='utf-8') as f:
# # # # # # # # #             return json.load(f)
# # # # # # # # #     except json.JSONDecodeError as e:
# # # # # # # # #         print(f"错误: JSON解析失败 - {str(e)}")
# # # # # # # # #         return None
# # # # # # # # #     except Exception as e:
# # # # # # # # #         print(f"错误: 加载文件失败 - {str(e)}")
# # # # # # # # #         return None


# # # # # # # # # def is_failed_analysis(item):
# # # # # # # # #     """判断条目是否为分析失败状态"""
# # # # # # # # #     required_fields = ["question", "mysql_sql", "sqlite_sql", "syntax_differences"]
# # # # # # # # #     for field in required_fields:
# # # # # # # # #         if field not in item:
# # # # # # # # #             return True
    
# # # # # # # # #     if not isinstance(item["syntax_differences"], list):
# # # # # # # # #         return True
    
# # # # # # # # #     for diff in item["syntax_differences"]:
# # # # # # # # #         if isinstance(diff, dict) and diff.get("difference", "").lower() == "分析失败":
# # # # # # # # #             return True
    
# # # # # # # # #     return False


# # # # # # # # # def query_model(question, sqlite_sql, mysql_sql, max_retries=3):
# # # # # # # # #     """调用大模型分析SQL语法差异（增加网络调试和代理支持）"""
# # # # # # # # #     if not API_KEY:
# # # # # # # # #         print("错误: 请配置有效的API_KEY")
# # # # # # # # #         return None
    
# # # # # # # # #     prompt = f"""
# # # # # # # # #     任务：详细分析SQLite和MySQL语句之间的语法差异，按照指定格式输出结果。
    
# # # # # # # # #     自然语言问题：{question}
# # # # # # # # #     SQLite语句：{sqlite_sql}
# # # # # # # # #     MySQL语句：{mysql_sql}
    
# # # # # # # # #     分析要求：
# # # # # # # # #     1. 找出两条SQL语句之间所有语法差异
# # # # # # # # #     2. 对每个差异，需明确：
# # # # # # # # #        - 差异类型（difference）
# # # # # # # # #        - 差异详情（detail）
# # # # # # # # #        - 导致差异的问题子串（question_causing_substring）
# # # # # # # # #        - MySQL中的差异代码片段（mysql_differing_substring）
# # # # # # # # #        - SQLite中的差异代码片段（sqlite_differing_substring）
# # # # # # # # #     3. 仅返回JSON数组，每个元素为一个差异对象，无任何额外文本
# # # # # # # # #     4. 如果没有差异或无法分析，返回空数组
    
# # # # # # # # #     输出示例：
# # # # # # # # #     [
# # # # # # # # #         {{
# # # # # # # # #             "difference": "条件表达式语法",
# # # # # # # # #             "detail": "MySQL使用CASE WHEN语句，SQLite使用IIF函数",
# # # # # # # # #             "question_causing_substring": "ratio of customers who pay in EUR against customers who pay in CZK",
# # # # # # # # #             "mysql_differing_substring": "CASE WHEN `Currency` = 'EUR' THEN 1 ELSE 0 END",
# # # # # # # # #             "sqlite_differing_substring": "IIF(Currency = 'EUR', 1, 0)"
# # # # # # # # #         }}
# # # # # # # # #     ]
# # # # # # # # #     """
    
# # # # # # # # #     headers = {
# # # # # # # # #         "Content-Type": "application/json",
# # # # # # # # #         "Authorization": f"Bearer {API_KEY}"
# # # # # # # # #     }
    
# # # # # # # # #     payload = {
# # # # # # # # #         "model": MODEL_NAME,
# # # # # # # # #         "messages": [{"role": "user", "content": prompt}],
# # # # # # # # #         "max_tokens": 1000,
# # # # # # # # #         "temperature": 0.2
# # # # # # # # #     }
    
# # # # # # # # #     # 配置代理（如果需要）
# # # # # # # # #     proxies = PROXY if USE_PROXY else None
    
# # # # # # # # #     for retry in range(max_retries):
# # # # # # # # #         try:
# # # # # # # # #             print(f"\n第{retry+1}次尝试连接API...")
# # # # # # # # #             response = requests.post(
# # # # # # # # #                 API_URL,
# # # # # # # # #                 headers=headers,
# # # # # # # # #                 json=payload,
# # # # # # # # #                 timeout=30,
# # # # # # # # #                 proxies=proxies,
# # # # # # # # #                 verify=VERIFY_SSL  # 控制SSL验证
# # # # # # # # #             )
            
# # # # # # # # #             # 打印HTTP状态码（辅助调试）
# # # # # # # # #             print(f"API响应状态码: {response.status_code}")
            
# # # # # # # # #             if response.status_code == 401:
# # # # # # # # #                 print("错误: API密钥无效或已过期")
# # # # # # # # #                 return None
# # # # # # # # #             if response.status_code == 429:
# # # # # # # # #                 wait_time = 2 ** retry
# # # # # # # # #                 print(f"请求频率超限，等待{wait_time}秒后重试...")
# # # # # # # # #                 sleep(wait_time)
# # # # # # # # #                 continue
# # # # # # # # #             if response.status_code != 200:
# # # # # # # # #                 print(f"API请求失败: {response.text[:500]}")
# # # # # # # # #                 return None
            
# # # # # # # # #             model_output = response.json()["choices"][0]["message"]["content"].strip()
# # # # # # # # #             model_output = model_output.replace("```json", "").replace("```", "").strip()
            
# # # # # # # # #             try:
# # # # # # # # #                 result = json.loads(model_output)
# # # # # # # # #                 return result if isinstance(result, list) else None
# # # # # # # # #             except json.JSONDecodeError as e:
# # # # # # # # #                 print(f"模型输出解析失败: {str(e)}, 原始输出: {model_output[:200]}")
# # # # # # # # #                 return None
                
# # # # # # # # #         except requests.exceptions.ProxyError:
# # # # # # # # #             print("错误: 代理配置错误或不可用")
# # # # # # # # #             if not USE_PROXY:
# # # # # # # # #                 print("提示: 若处于企业网络，可能需要配置代理（修改USE_PROXY和PROXY参数）")
# # # # # # # # #         except requests.exceptions.SSLError:
# # # # # # # # #             print("错误: SSL证书验证失败")
# # # # # # # # #             print("提示: 可尝试将VERIFY_SSL设为False（仅测试用，不安全）")
# # # # # # # # #         except requests.exceptions.ConnectionError:
# # # # # # # # #             print("错误: 网络连接失败（无法到达API服务器）")
# # # # # # # # #             print("提示: 可能被防火墙阻止，或API端点错误")
# # # # # # # # #         except requests.exceptions.Timeout:
# # # # # # # # #             print("错误: 请求超时")
# # # # # # # # #         except Exception as e:
# # # # # # # # #             print(f"请求异常: {str(e)}")
            
# # # # # # # # #         if retry < max_retries - 1:
# # # # # # # # #             sleep(2)  # 重试间隔
    
# # # # # # # # #     print(f"已达到最大重试次数({max_retries}次)，分析失败")
# # # # # # # # #     return None


# # # # # # # # # def process_analysis_failures(data):
# # # # # # # # #     """处理所有分析失败的条目"""
# # # # # # # # #     if not data:
# # # # # # # # #         return None, 0, 0
    
# # # # # # # # #     is_dict_format = isinstance(data, dict)
# # # # # # # # #     processed_data = {} if is_dict_format else []
# # # # # # # # #     total_analyzed = 0
# # # # # # # # #     successfully_updated = 0
    
# # # # # # # # #     if is_dict_format:
# # # # # # # # #         for category, items in data.items():
# # # # # # # # #             processed_items = []
# # # # # # # # #             for item in items:
# # # # # # # # #                 if not isinstance(item, dict):
# # # # # # # # #                     processed_items.append(item)
# # # # # # # # #                     continue
                
# # # # # # # # #                 if is_failed_analysis(item):
# # # # # # # # #                     total_analyzed += 1
# # # # # # # # #                     print(f"\n重新分析问题: {item['question'][:60]}...")
                    
# # # # # # # # #                     new_differences = query_model(
# # # # # # # # #                         item["question"],
# # # # # # # # #                         item["sqlite_sql"],
# # # # # # # # #                         item["mysql_sql"]
# # # # # # # # #                     )
                    
# # # # # # # # #                     if new_differences and len(new_differences) > 0:
# # # # # # # # #                         item["syntax_differences"] = new_differences
# # # # # # # # #                         if "causing_part" in item:
# # # # # # # # #                             item["causing_part"] = new_differences[0].get("question_causing_substring", "")
# # # # # # # # #                         processed_items.append(item)
# # # # # # # # #                         successfully_updated += 1
# # # # # # # # #                         print("分析成功，已更新结果")
# # # # # # # # #                     else:
# # # # # # # # #                         print("重新分析失败，将删除该条目")
# # # # # # # # #                 else:
# # # # # # # # #                     processed_items.append(item)
            
# # # # # # # # #             processed_data[category] = processed_items
# # # # # # # # #     else:
# # # # # # # # #         for item in data:
# # # # # # # # #             if not isinstance(item, dict):
# # # # # # # # #                 processed_data.append(item)
# # # # # # # # #                 continue
            
# # # # # # # # #             if is_failed_analysis(item):
# # # # # # # # #                 total_analyzed += 1
# # # # # # # # #                 print(f"\n重新分析问题: {item['question'][:60]}...")
                
# # # # # # # # #                 new_differences = query_model(
# # # # # # # # #                     item["question"],
# # # # # # # # #                     item["sqlite_sql"],
# # # # # # # # #                     item["mysql_sql"]
# # # # # # # # #                 )
                
# # # # # # # # #                 if new_differences and len(new_differences) > 0:
# # # # # # # # #                     item["syntax_differences"] = new_differences
# # # # # # # # #                     if "causing_part" in item:
# # # # # # # # #                         item["causing_part"] = new_differences[0].get("question_causing_substring", "")
# # # # # # # # #                     processed_data.append(item)
# # # # # # # # #                     successfully_updated += 1
# # # # # # # # #                     print("分析成功，已更新结果")
# # # # # # # # #                 else:
# # # # # # # # #                     print("重新分析失败，将删除该条目")
# # # # # # # # #             else:
# # # # # # # # #                 processed_data.append(item)
    
# # # # # # # # #     return processed_data, total_analyzed, successfully_updated


# # # # # # # # # def save_processed_data(data, file_path):
# # # # # # # # #     """保存处理后的数据到文件"""
# # # # # # # # #     try:
# # # # # # # # #         with open(file_path, 'w', encoding='utf-8') as f:
# # # # # # # # #             json.dump(data, f, ensure_ascii=False, indent=4)
# # # # # # # # #         print(f"\n处理完成，结果已保存到: {file_path}")
# # # # # # # # #         return True
# # # # # # # # #     except Exception as e:
# # # # # # # # #         print(f"保存文件失败: {str(e)}")
# # # # # # # # #         return False


# # # # # # # # # def main():
# # # # # # # # #     # 先测试API连通性
# # # # # # # # #     test_api_connectivity()
    
# # # # # # # # #     # 创建备份
# # # # # # # # #     if not create_backup(TARGET_FILE):
# # # # # # # # #         print("无法创建备份，程序退出")
# # # # # # # # #         return
    
# # # # # # # # #     # 加载数据
# # # # # # # # #     data = load_json_data(TARGET_FILE)
# # # # # # # # #     if data is None:
# # # # # # # # #         print("无法加载数据，程序退出")
# # # # # # # # #         return
    
# # # # # # # # #     # 处理分析失败的条目
# # # # # # # # #     processed_data, total_analyzed, successfully_updated = process_analysis_failures(data)
    
# # # # # # # # #     # 保存结果
# # # # # # # # #     if processed_data is not None:
# # # # # # # # #         save_processed_data(processed_data, TARGET_FILE)
    
# # # # # # # # #     # 输出统计
# # # # # # # # #     print("\n=== 处理统计 ===")
# # # # # # # # #     print(f"总共分析失败的条目: {total_analyzed}")
# # # # # # # # #     print(f"重新分析成功并更新的条目: {successfully_updated}")
# # # # # # # # #     print(f"仍然失败并被删除的条目: {total_analyzed - successfully_updated}")


# # # # # # # # # if __name__ == "__main__":
# # # # # # # # #     main()

# # # ##统计difference类型总数

# # # import json
# # # import os

# # # def count_difference_types(file_path):
# # #         # 检查文件是否存在
# # #         if not os.path.exists(file_path):
# # #             print(f"错误：文件 '{file_path}' 不存在")
# # #             return
        
# # #         try:
# # #             # 读取JSON文件
# # #             with open(file_path, 'r', encoding='utf-8') as f:
# # #                 data = json.load(f)
            
# # #             # 存储不重复的difference类型
# # #             difference_types = set()
            
# # #             # 遍历JSON数据中的每个条目
# # #             for item in data:
# # #                 # 检查是否包含syntax_differences字段
# # #                 if 'syntax_differences' in item:
# # #                     # 遍历每个差异
# # #                     for diff in item['syntax_differences']:
# # #                         if 'difference' in diff:
# # #                             difference_types.add(diff['difference'])
            
# # #             # 输出结果
# # #             print(f"共发现 {len(difference_types)} 种不同的difference类型：")
# # #             for i, diff_type in enumerate(sorted(difference_types), 1):
# # #                 print(f"{i}. {diff_type}")
                
# # #         except json.JSONDecodeError:
# # #             print(f"错误：文件 '{file_path}' 不是有效的JSON格式")
# # #         except Exception as e:
# # #             print(f"处理文件时发生错误：{str(e)}")

# # # if __name__ == "__main__":
# # #         # 指定JSON文件路径
# # #         json_file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\conclude\sqlite_mysql_difference.json"
# # #         count_difference_types(json_file_path)
    
    
# # # # # # # ##去除标识符类


# # # import json
# # # import os

# # # # 定义文件路径
# # # file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\conclude\sqlite_mysql_difference.json"

# # # # 需要移除的difference列表
# # # target_differences = [
# # #     "反引号标识符引用",
# # #     "引用标识符",
# # #     "标识符引用",
# # #     "标识符引用方式",
# # #     "标识符引用符号",
# # #     "反引号使用"
# # # ]

# # # try:
# # #     # 读取JSON文件
# # #     with open(file_path, 'r', encoding='utf-8') as f:
# # #         data = json.load(f)
    
# # #     # 处理每个条目，过滤掉指定的difference
# # #     if isinstance(data, list):
# # #         for item in data:
# # #             if "syntax_differences" in item and isinstance(item["syntax_differences"], list):
# # #                 # 过滤掉需要移除的difference条目
# # #                 item["syntax_differences"] = [
# # #                     diff for diff in item["syntax_differences"]
# # #                     if diff.get("difference") not in target_differences
# # #                 ]
    
# # #     # 写回处理后的内容
# # #     with open(file_path, 'w', encoding='utf-8') as f:
# # #         json.dump(data, f, ensure_ascii=False, indent=4)
    
# # #     print(f"处理完成，已移除所有指定的difference条目。文件路径：{file_path}")

# # # except FileNotFoundError:
# # #     print(f"错误：文件未找到 - {file_path}")
# # # except json.JSONDecodeError:
# # #     print(f"错误：文件不是有效的JSON格式 - {file_path}")
# # # except Exception as e:
# # #     print(f"处理过程中发生错误：{str(e)}")


# # # # # # ##更新causing_part字段

# # # import json
# # # import os

# # # # 定义文件路径
# # # file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\conclude\sqlite_mysql_difference.json"

# # # try:
# # #     # 读取JSON文件
# # #     with open(file_path, 'r', encoding='utf-8') as f:
# # #         data = json.load(f)
    
# # #     # 处理每个条目，更新causing_part字段
# # #     if isinstance(data, list):
# # #         for item in data:
# # #             # 检查是否包含syntax_differences字段且为列表
# # #             if "syntax_differences" in item and isinstance(item["syntax_differences"], list):
# # #                 # 提取所有difference值
# # #                 differences = [diff.get("difference") for diff in item["syntax_differences"] if diff.get("difference")]
                
# # #                 # 组合成新的causing_part（使用中文逗号分隔）
# # #                 if differences:
# # #                     item["causing_part"] = "、".join(differences)
# # #                 else:
# # #                     # 如果没有差异，设置为空字符串或适当提示
# # #                     item["causing_part"] = ""
    
# # #     # 写回处理后的内容，保持缩进格式
# # #     with open(file_path, 'w', encoding='utf-8') as f:
# # #         json.dump(data, f, ensure_ascii=False, indent=4)
    
# # #     print(f"处理完成，已更新所有causing_part字段。文件路径：{file_path}")

# # # except FileNotFoundError:
# # #     print(f"错误：文件未找到 - {file_path}")
# # # except json.JSONDecodeError:
# # #     print(f"错误：文件不是有效的JSON格式 - {file_path}")
# # # except Exception as e:
# # #     print(f"处理过程中发生错误：{str(e)}")
    
    
# # # # # ##去除syntax_differences为空的条目

# # # import json

# # # # 定义文件路径
# # # file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\conclude\sqlite_mysql_difference.json"

# # # try:
# # #     # 读取JSON文件内容
# # #     with open(file_path, 'r', encoding='utf-8') as f:
# # #         data = json.load(f)
    
# # #     # 检查数据是否为列表类型（符合预期格式）
# # #     if not isinstance(data, list):
# # #         raise ValueError("JSON文件内容不是预期的列表格式")
    
# # #     # 过滤掉syntax_differences为空列表的条目
# # #     # 保留条件：syntax_differences存在且为非空列表
# # #     filtered_data = []
# # #     removed_count = 0
# # #     for item in data:
# # #         # 检查条目是否包含syntax_differences字段且为列表
# # #         if "syntax_differences" in item and isinstance(item["syntax_differences"], list):
# # #             if len(item["syntax_differences"]) > 0:
# # #                 filtered_data.append(item)
# # #             else:
# # #                 removed_count += 1
# # #         else:
# # #             # 对于没有syntax_differences字段的条目，也视为需要删除（根据需求调整）
# # #             removed_count += 1
    
# # #     # 将过滤后的结果写回文件
# # #     with open(file_path, 'w', encoding='utf-8') as f:
# # #         json.dump(filtered_data, f, ensure_ascii=False, indent=4)
    
# # #     print(f"处理完成！共删除 {removed_count} 个syntax_differences为空的条目")
# # #     print(f"剩余有效条目数量：{len(filtered_data)}")

# # # except FileNotFoundError:
# # #     print(f"错误：找不到文件 - {file_path}")
# # # except json.JSONDecodeError:
# # #     print(f"错误：文件不是有效的JSON格式")
# # # except Exception as e:
# # #     print(f"处理过程中发生错误：{str(e)}")

# # ##将difference字段重写为大类

# # # import json
# # # import os

# # # def load_json_file(file_path):
# # #     """加载JSON文件并验证有效性"""
# # #     if not os.path.exists(file_path):
# # #         print(f"错误：文件不存在 - {file_path}")
# # #         return None
# # #     if not os.path.isfile(file_path):
# # #         print(f"错误：不是有效文件 - {file_path}")
# # #         return None

# # #     try:
# # #         with open(file_path, 'r', encoding='utf-8') as f:
# # #             return json.load(f)
# # #     except json.JSONDecodeError as e:
# # #         print(f"错误：JSON解析失败 - {str(e)}（文件：{file_path}）")
# # #         return None
# # #     except Exception as e:
# # #         print(f"错误：加载文件失败 - {str(e)}（文件：{file_path}）")
# # #         return None

# # # def save_json_file(data, file_path, backup=True):
# # #     """保存JSON文件并创建备份"""
# # #     try:
# # #         if backup and os.path.exists(file_path):
# # #             backup_path = f"{file_path}.bak"
# # #             with open(file_path, 'r', encoding='utf-8') as f_in, \
# # #                  open(backup_path, 'w', encoding='utf-8') as f_out:
# # #                 f_out.write(f_in.read())
# # #             print(f"已创建备份文件：{backup_path}")
        
# # #         with open(file_path, 'w', encoding='utf-8') as f:
# # #             json.dump(data, f, ensure_ascii=False, indent=2)
# # #         print(f"文件已保存至：{file_path}")
# # #         return True
# # #     except Exception as e:
# # #         print(f"错误：保存文件失败 - {str(e)}")
# # #         return False

# # # def create_category_mapping():
# # #     """创建原始差异类型（小类）到大类的映射，确保键与数据中的小类完全匹配（修复空格问题）"""
# # #     return {
# # #         # 1. 数据去重（DISTINCT 相关）
# # #         "DISTINCT关键字": "数据去重（DISTINCT 相关）",  # 移除空格，匹配"DISTINCT关键字"
        
# # #         # 2. 分组聚合（GROUP BY 子句）
# # #         "GROUP BY子句": "分组聚合（GROUP BY 子句）",      # 移除空格，匹配"GROUP BY子句"
# # #         "GROUP BY子句格式": "分组聚合（GROUP BY 子句）",  # 移除空格，匹配"GROUP BY子句格式"
        
# # #         # 3. 聚合函数与引用
# # #         "条件聚合函数语法": "聚合函数与引用",
# # #         "聚合查询与排序方式": "聚合函数与引用",
        
# # #         # 4. 表连接（JOIN）相关
# # #         "JOIN条件关键字大小写": "表连接（JOIN）相关",    # 移除空格，匹配"JOIN条件关键字大小写"
# # #         "JOIN条件列引用": "表连接（JOIN）相关",          # 移除空格，匹配"JOIN条件列引用"
# # #         "JOIN条件引用": "表连接（JOIN）相关",            # 移除空格，匹配"JOIN条件引用"
# # #         "JOIN条件引用符号": "表连接（JOIN）相关",        # 移除空格，匹配"JOIN条件引用符号"
# # #         "JOIN条件格式": "表连接（JOIN）相关",            # 移除空格，匹配"JOIN条件格式"
# # #         "JOIN语法": "表连接（JOIN）相关",                # 移除空格，匹配"JOIN语法"
# # #         "表连接语法": "表连接（JOIN）相关",
# # #         "连接条件引用": "表连接（JOIN）相关",
# # #         "连接条件引用符号": "表连接（JOIN）相关",
        
# # #         # 5. 模式匹配（LIKE）相关
# # #         "LIKE子句中的日期格式": "模式匹配（LIKE）相关",  # 移除空格，匹配"LIKE子句中的日期格式"
# # #         "NOT LIKE语法位置": "模式匹配（LIKE）相关",      # 移除空格，匹配"NOT LIKE语法位置"
        
# # #         # 6. 分页（LIMIT）语法
# # #         "LIMIT/OFFSET语法": "分页（LIMIT）语法",        # 移除空格，匹配"LIMIT/OFFSET语法"
# # #         "LIMIT和OFFSET语法": "分页（LIMIT）语法",        # 移除空格，匹配"LIMIT和OFFSET语法"
        
# # #         # 7. 空值（NULL）处理
# # #         "NULL值判断语法": "空值（NULL）处理",            # 移除空格，匹配"NULL值判断语法"
# # #         "NULL值检查语法": "空值（NULL）处理",            # 移除空格，匹配"NULL值检查语法"
# # #         "空值检查语法": "空值（NULL）处理",
        
# # #         # 8. 排序（ORDER BY）基础语法
# # #         "ORDER BY子句格式": "排序（ORDER BY）基础语法",  # 移除空格，匹配"ORDER BY子句格式"
# # #         "ORDER BY引用": "排序（ORDER BY）基础语法",      # 移除空格，匹配"ORDER BY引用"
# # #         "排序条件引用符号": "排序（ORDER BY）基础语法",
        
# # #         # 9. 筛选条件相关
# # #         "WHERE子句列引用": "筛选条件相关",              # 移除空格，匹配"WHERE子句列引用"
# # #         "WHERE子句引用": "筛选条件相关",                # 移除空格，匹配"WHERE子句引用"
# # #         "WHERE条件列引用": "筛选条件相关",              # 移除空格，匹配"WHERE条件列引用"
# # #         "WHERE条件引用": "筛选条件相关",                # 移除空格，匹配"WHERE条件引用"
# # #         "WHERE条件引用符号": "筛选条件相关",            # 移除空格，匹配"WHERE条件引用符号"
# # #         "排除条件实现方式": "筛选条件相关",
# # #         "条件值引用": "筛选条件相关",
# # #         "条件列引用": "筛选条件相关",
# # #         "条件列引用符号": "筛选条件相关",
# # #         "条件字段引用": "筛选条件相关",
# # #         "条件表达式": "筛选条件相关",
# # #         "条件表达式中的列引用符号": "筛选条件相关",
# # #         "条件表达式格式": "筛选条件相关",
# # #         "条件表达式语法": "筛选条件相关",
        
# # #         # 10. 列与表引用规则
# # #         "列引用符号": "列与表引用规则",
# # #         "结果列命名": "列与表引用规则",
# # #         "表/列引用语法": "列与表引用规则",              # 修正为"表/列引用语法"，匹配警告中的"表/列引用语法"
# # #         "列别名关键字": "列与表引用规则",
# # #         "列别名引用": "列与表引用规则",
# # #         "列别名语法": "列与表引用规则",
# # #         "列名引用": "列与表引用规则",
# # #         "列名引用符号": "列与表引用规则",
# # #         "列名引用语法": "列与表引用规则",
# # #         "列引用": "列与表引用规则",
# # #         "列引用引号": "列与表引用规则",
# # #         "列引用方式": "列与表引用规则",
# # #         "列引用格式": "列与表引用规则",
# # #         "列引用语法": "列与表引用规则",
# # #         "子查询中的列名引用符号": "列与表引用规则",
# # #         "子查询中的表名引用符号": "列与表引用规则",
# # #         "子查询列名引用": "列与表引用规则",
# # #         "子查询别名": "列与表引用规则",
# # #         "子查询别名引用": "列与表引用规则",
# # #         "子查询表名引用": "列与表引用规则",
# # #         "字段名引用符号": "列与表引用规则",
# # #         "字段引用符号": "列与表引用规则",
# # #         "日期列引用符号": "列与表引用规则",
# # #         "日期字段引用": "列与表引用规则",
# # #         "结果列引用符号": "列与表引用规则",
# # #         "表列引用": "列与表引用规则",
# # #         "表别名引用": "列与表引用规则",
# # #         "表名和列名引用": "列与表引用规则",
# # #         "表名引用": "列与表引用规则",
# # #         "表名引用方式": "列与表引用规则",
# # #         "表名引用符号": "列与表引用规则",
# # #         "表名引用语法": "列与表引用规则",
# # #         "表引用": "列与表引用规则",
# # #         "表引用符号": "列与表引用规则",
# # #         "表引用语法": "列与表引用规则",
        
# # #         # 11. 字符串处理
# # #         "字符串引用符号": "字符串处理",
# # #         "字符串截取函数": "字符串处理",
# # #         "字符串比较": "字符串处理",
# # #         "引号使用": "字符串处理",
# # #         "引号风格": "字符串处理",
# # #         "格式化风格": "字符串处理",
        
# # #         # 12. 数值处理
# # #         "浮点数类型转换": "数值处理",
# # #         "关键字大小写": "数值处理",
        
# # #         # 13. 日期时间处理
# # #         "年份提取语法": "日期时间处理",
# # #         "当前时间戳函数": "日期时间处理",
# # #         "日期函数语法": "日期时间处理",
# # #         "日期字段处理": "日期时间处理",
# # #         "日期排序函数": "日期时间处理",
# # #         "日期条件格式": "日期时间处理",
# # #         "日期格式化函数": "日期时间处理",
# # #         "日期类型转换": "日期时间处理",
# # #         "日期计算语法": "日期时间处理",
        
# # #         # 14. 类型转换
# # #         "数据类型转换": "类型转换",
# # #         "类型转换": "类型转换",
# # #         "类型转换函数": "类型转换",
# # #         "类型转换语法": "类型转换"
# # #     }

# # # def rewrite_differences(data, category_mapping):
# # #     """优化替换逻辑：添加未映射项日志，确保小类全量匹配"""
# # #     if not data or not isinstance(data, list):
# # #         return data

# # #     rewritten_data = []
# # #     # 用于记录未被映射的小类（排查问题核心）
# # #     unmapped_categories = set()

# # #     for item in data:
# # #         if "syntax_differences" in item and isinstance(item["syntax_differences"], list):
# # #             new_syntax_diffs = []
# # #             for diff in item["syntax_differences"]:
# # #                 if "difference" in diff:
# # #                     original_diff = diff["difference"].strip()  # 去除首尾空格，避免匹配误差
# # #                     # 检查是否在映射中
# # #                     if original_diff in category_mapping:
# # #                         new_diff = category_mapping[original_diff]
# # #                     else:
# # #                         # 记录未映射的小类，方便后续补充映射表
# # #                         unmapped_categories.add(original_diff)
# # #                         new_diff = original_diff  # 保留原值但记录问题
                    
# # #                     updated_diff = diff.copy()
# # #                     updated_diff["difference"] = new_diff
# # #                     new_syntax_diffs.append(updated_diff)
# # #                 else:
# # #                     new_syntax_diffs.append(diff)
# # #             item["syntax_differences"] = new_syntax_diffs

# # #         # 处理causing_part字段（保持原逻辑但依赖映射表完整性）
# # #         if "causing_part" in item and isinstance(item["causing_part"], str):
# # #             causing_part = item["causing_part"]
# # #             for original in sorted(category_mapping.keys(), key=len, reverse=True):
# # #                 if original in causing_part:
# # #                     causing_part = causing_part.replace(original, category_mapping[original])
# # #             item["causing_part"] = causing_part

# # #         rewritten_data.append(item)
    
# # #     # 输出未映射的小类（关键：帮助用户发现遗漏的映射）
# # #     if unmapped_categories:
# # #         print("\n警告：以下小类未在映射表中找到对应大类，已保留原值：")
# # #         for idx, cat in enumerate(unmapped_categories, 1):
# # #             print(f"  {idx}. {cat}")
# # #     else:
# # #         print("\n所有小类均已成功映射到对应的大类！")

# # #     return rewritten_data

# # # def main():
# # #     file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\conclude\sqlite_mysql_difference.json"
    
# # #     data = load_json_file(file_path)
# # #     if not data:
# # #         return
    
# # #     category_mapping = create_category_mapping()
# # #     updated_data = rewrite_differences(data, category_mapping)
# # #     save_json_file(updated_data, file_path)

# # # if __name__ == "__main__":
# # #     main()
    

# # # # ##将筛选条件（WHERE）相关的差异类型更改为筛选条件相关

# # # # import json
# # # # import os

# # # # def load_json_file(file_path):
# # # #     """加载JSON文件并验证有效性"""
# # # #     if not os.path.exists(file_path):
# # # #         print(f"错误：文件不存在 - {file_path}")
# # # #         return None
# # # #     if not os.path.isfile(file_path):
# # # #         print(f"错误：不是有效文件 - {file_path}")
# # # #         return None

# # # #     try:
# # # #         with open(file_path, 'r', encoding='utf-8') as f:
# # # #             return json.load(f)
# # # #     except json.JSONDecodeError as e:
# # # #         print(f"错误：JSON解析失败 - {str(e)}（文件：{file_path}）")
# # # #         return None
# # # #     except Exception as e:
# # # #         print(f"错误：加载文件失败 - {str(e)}（文件：{file_path}）")
# # # #         return None

# # # # def save_json_file(data, file_path, backup=True):
# # # #     """保存JSON文件并创建备份"""
# # # #     try:
# # # #         # 创建备份文件
# # # #         if backup and os.path.exists(file_path):
# # # #             backup_path = f"{file_path}.bak"
# # # #             with open(file_path, 'r', encoding='utf-8') as f_in, \
# # # #                  open(backup_path, 'w', encoding='utf-8') as f_out:
# # # #                 f_out.write(f_in.read())
# # # #             print(f"已创建备份文件：{backup_path}")
        
# # # #         # 保存处理后的数据
# # # #         with open(file_path, 'w', encoding='utf-8') as f:
# # # #             json.dump(data, f, ensure_ascii=False, indent=2)
# # # #         print(f"文件已保存至：{file_path}")
# # # #         return True
# # # #     except Exception as e:
# # # #         print(f"错误：保存文件失败 - {str(e)}")
# # # #         return False

# # # # def remove_where_in_filter_conditions(data):
# # # #     """将所有"筛选条件（WHERE）相关"替换为"筛选条件相关" """
# # # #     if not data or not isinstance(data, list):
# # # #         return data

# # # #     modified_data = []
# # # #     for item in data:
# # # #         # 处理syntax_differences中的difference字段
# # # #         if "syntax_differences" in item and isinstance(item["syntax_differences"], list):
# # # #             modified_differences = []
# # # #             for diff in item["syntax_differences"]:
# # # #                 if "difference" in diff and diff["difference"] == "筛选条件（WHERE）相关":
# # # #                     # 创建新的字典，避免修改原始数据
# # # #                     updated_diff = diff.copy()
# # # #                     updated_diff["difference"] = "筛选条件相关"
# # # #                     modified_differences.append(updated_diff)
# # # #                 else:
# # # #                     modified_differences.append(diff)
# # # #             item["syntax_differences"] = modified_differences
        
# # # #         # 处理causing_part字段
# # # #         if "causing_part" in item and isinstance(item["causing_part"], str):
# # # #             # 替换所有出现的"筛选条件（WHERE）相关"
# # # #             item["causing_part"] = item["causing_part"].replace(
# # # #                 "筛选条件（WHERE）相关", "筛选条件相关"
# # # #             )
        
# # # #         modified_data.append(item)
    
# # # #     return modified_data

# # # # def main():
# # # #     # 目标文件路径
# # # #     file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\conclude\sqlite_mysql_difference.json"
    
# # # #     # 加载文件数据
# # # #     data = load_json_file(file_path)
# # # #     if not data:
# # # #         return
    
# # # #     # 修改筛选条件相关的WHERE标识
# # # #     modified_data = remove_where_in_filter_conditions(data)
    
# # # #     # 保存结果
# # # #     save_json_file(modified_data, file_path)

# # # # if __name__ == "__main__":
# # # #     main()
    
    
# # # ##将问题归类


# # # import json
# # # import os

# # # def group_by_difference(input_file, output_file):
# # #     """
# # #     将JSON文件中的数据按"syntax_differences"数组中的"difference"字段分类，并保存到新的JSON文件
    
# # #     参数:
# # #         input_file: 输入JSON文件路径
# # #         output_file: 输出JSON文件路径
# # #     """
# # #     try:
# # #         # 读取输入文件
# # #         with open(input_file, 'r', encoding='utf-8') as f:
# # #             data = json.load(f)
        
# # #         # 确保输入数据是列表类型
# # #         if not isinstance(data, list):
# # #             raise ValueError("输入JSON文件的根元素必须是列表")
        
# # #         # 按"difference"分组
# # #         grouped = {}
# # #         skipped_items = 0  # 记录跳过的项目数量
# # #         total_processed = 0  # 记录处理的差异数量
        
# # #         for item in data:
# # #             # 检查顶层必要字段 - 适配SQLite和MySQL的字段名
# # #             top_level_fields = ["question", "mysql_sql", "sqlite_sql"]
# # #             missing_top_fields = [field for field in top_level_fields if field not in item]
            
# # #             if missing_top_fields:
# # #                 skipped_items += 1
# # #                 print(f"警告: 跳过缺少顶层字段的数据项，缺少字段: {', '.join(missing_top_fields)}")
# # #                 continue
            
# # #             # 检查是否有syntax_differences字段且是列表
# # #             if "syntax_differences" not in item or not isinstance(item["syntax_differences"], list):
# # #                 skipped_items += 1
# # #                 print("警告: 跳过缺少有效的syntax_differences数组的数据项")
# # #                 continue
            
# # #             # 处理每个syntax_difference
# # #             for diff in item["syntax_differences"]:
# # #                 # 检查差异项中的必要字段 - 适配SQLite和MySQL的字段名
# # #                 diff_fields = ["difference", "question_causing_substring", 
# # #                              "mysql_differing_substring", "sqlite_differing_substring"]
# # #                 missing_diff_fields = [field for field in diff_fields if field not in diff]
                
# # #                 if missing_diff_fields:
# # #                     skipped_items += 1
# # #                     print(f"警告: 跳过缺少字段的差异项，缺少字段: {', '.join(missing_diff_fields)}")
# # #                     continue
                
# # #                 # 准备要保存的条目，包含顶层信息和当前差异信息
# # #                 entry = {
# # #                     "question": item["question"],
# # #                     "mysql_sql": item["mysql_sql"],
# # #                     "sqlite_sql": item["sqlite_sql"],
# # #                     "question_causing_substring": diff["question_causing_substring"],
# # #                     "mysql_differing_substring": diff["mysql_differing_substring"],
# # #                     "sqlite_differing_substring": diff["sqlite_differing_substring"],
# # #                     "difference": diff["difference"],
# # #                     "detail": diff.get("detail", "")  # 可选字段
# # #                 }
                
# # #                 difference = diff["difference"]
# # #                 # 确保difference是字符串类型
# # #                 if not isinstance(difference, str):
# # #                     difference = str(difference)
                
# # #                 # 按difference分组，允许重复项
# # #                 if difference not in grouped:
# # #                     grouped[difference] = []
# # #                 grouped[difference].append(entry)
# # #                 total_processed += 1
        
# # #         # 确保输出目录存在
# # #         output_dir = os.path.dirname(output_file)
# # #         if not os.path.exists(output_dir):
# # #             os.makedirs(output_dir)
        
# # #         # 保存结果到输出文件
# # #         with open(output_file, 'w', encoding='utf-8') as f:
# # #             json.dump(grouped, f, ensure_ascii=False, indent=4)
        
# # #         print(f"成功将数据按'difference'分类，结果已保存到: {output_file}")
# # #         print(f"共分为 {len(grouped)} 个不同的'difference'类别")
# # #         print(f"共处理了 {total_processed} 个差异项")
# # #         print(f"处理过程中跳过了 {skipped_items} 个有问题的数据项/差异项")
        
# # #     except FileNotFoundError:
# # #         print(f"错误: 找不到输入文件 {input_file}")
# # #     except json.JSONDecodeError:
# # #         print(f"错误: 输入文件 {input_file} 不是有效的JSON格式")
# # #     except Exception as e:
# # #         print(f"处理过程中发生错误: {str(e)}")

# # # if __name__ == "__main__":
# # #     # 输入文件路径 - SQLite与MySQL差异文件
# # #     input_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\conclude\sqlite_mysql_difference.json"
# # #     # 输出文件路径 - 分类后的结果文件
# # #     output_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\conclude\sqlite_mysql_conclusion.json"
    
# # #     # 执行分组操作
# # #     group_by_difference(input_path, output_path)
    
    
# # ##计算方言部分的长度比

# # import json
# # import os
# # import shutil

# # def calculate_substring_percentage(json_data):
# #     """计算每个问题中question_causing_substring占整个question的百分比并添加到对应位置（带%）"""
# #     # 遍历每个顶层分类（如"筛选条件相关"）
# #     for category, questions_list in json_data.items():
# #         # 检查每个分类对应的是否为问题列表
# #         if isinstance(questions_list, list):
# #             # 遍历列表中的每个问题条目
# #             for question_item in questions_list:
# #                 # 确保包含必要的字段
# #                 if "question" in question_item and "question_causing_substring" in question_item:
# #                     full_question = question_item["question"]
# #                     dialect_substring = question_item["question_causing_substring"]
                    
# #                     # 计算百分比（避免除以零错误）
# #                     if len(full_question) > 0:
# #                         percentage = (len(dialect_substring) / len(full_question)) * 100
# #                         # 保留两位小数并添加百分号
# #                         question_item["substring_percentage"] = f"{round(percentage, 2)}%"
# #                     else:
# #                         question_item["substring_percentage"] = "0.00%"
# #     return json_data

# # def main():
# #     # 目标文件路径（SQLite与MySQL的结论文件）
# #     file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\conclude\sqlite_mysql_conclusion.json"
    
# #     # 检查文件是否存在
# #     if not os.path.exists(file_path):
# #         print(f"错误：文件不存在 - {file_path}")
# #         return
    
# #     try:
# #         # 创建文件备份（添加.backup后缀）
# #         backup_path = f"{file_path}.backup"
# #         shutil.copy2(file_path, backup_path)
# #         print(f"已创建文件备份: {backup_path}")
        
# #         # 读取JSON文件内容
# #         with open(file_path, 'r', encoding='utf-8') as f:
# #             json_data = json.load(f)
        
# #         # 计算并添加百分比字段
# #         updated_data = calculate_substring_percentage(json_data)
        
# #         # 保存更新后的JSON文件
# #         with open(file_path, 'w', encoding='utf-8') as f:
# #             json.dump(updated_data, f, ensure_ascii=False, indent=4)
        
# #         print("处理完成，已添加substring_percentage字段（方言部分占比）")
        
# #     except json.JSONDecodeError:
# #         print("错误：文件不是有效的JSON格式")
# #     except Exception as e:
# #         print(f"处理过程中发生错误: {str(e)}")

# # if __name__ == "__main__":
# #     main()


# ##计算平均值


# import json
# import os

# def calculate_average_percentages(input_file, output_file):
#     # 读取输入JSON文件
#     try:
#         with open(input_file, 'r', encoding='utf-8') as f:
#             data = json.load(f)
#     except FileNotFoundError:
#         print(f"错误：找不到文件 {input_file}")
#         return
#     except json.JSONDecodeError:
#         print(f"错误：文件 {input_file} 不是有效的JSON格式")
#         return
#     except Exception as e:
#         print(f"读取文件时发生错误：{str(e)}")
#         return
    
#     result = {}
    
#     # 遍历每个类别
#     for category, questions in data.items():
#         percentages = []
        
#         # 提取每个问题的substring_percentage
#         for question in questions:
#             if "substring_percentage" in question:
#                 # 移除百分号并转换为浮点数
#                 percentage_str = question["substring_percentage"].replace('%', '')
#                 try:
#                     percentage = float(percentage_str)
#                     percentages.append(percentage)
#                 except ValueError:
#                     print(f"警告：类别 '{category}' 中的问题 '{question.get('question', '')}' 包含无效的百分比值：{question['substring_percentage']}")
        
#         # 计算平均值
#         if percentages:
#             average = sum(percentages) / len(percentages)
#             # 保留两位小数并添加百分号
#             result[category] = f"{average:.2f}%"
#         else:
#             result[category] = "0.00%"
#             print(f"警告：类别 '{category}' 中没有有效的百分比数据")
    
#     # 确保输出目录存在
#     output_dir = os.path.dirname(output_file)
#     if not os.path.exists(output_dir):
#         os.makedirs(output_dir)
    
#     # 写入结果到输出JSON文件
#     try:
#         with open(output_file, 'w', encoding='utf-8') as f:
#             json.dump(result, f, ensure_ascii=False, indent=4)
#         print(f"成功生成输出文件：{output_file}")
#     except Exception as e:
#         print(f"写入文件时发生错误：{str(e)}")

# if __name__ == "__main__":
#     # SQLite与MySQL结论文件路径
#     input_json_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\conclude\sqlite_mysql_conclusion.json"
#     # 输出的平均值文件路径
#     output_json_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\conclude\radio.json"
    
#     calculate_average_percentages(input_json_path, output_json_path)
    
    
##画图


import json
import os
import matplotlib.pyplot as plt
import numpy as np

# 文件路径（radio.json的位置）
file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\conclude\radio.json"
# 输出文件夹路径（与radio.json同目录）
output_dir = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\conclude"

# 确保输出文件夹存在
os.makedirs(output_dir, exist_ok=True)

# 设置中文字体，确保中文正常显示
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

try:
    # 读取JSON数据（radio.json为键值对结构）
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 检查数据有效性
    if not data or not isinstance(data, dict):
        print("警告：未找到有效数据或数据格式错误")
        exit()
    
    # 解析数据：转换为[{类别名, 百分比}, ...]格式，并转换百分比为浮点数
    parsed_data = []
    for category, percentage_str in data.items():
        # 去除百分号并转换为浮点数
        try:
            percentage = float(percentage_str.strip('%'))
            parsed_data.append({
                'category': category,
                'percentage': percentage
            })
        except ValueError:
            print(f"警告：类别 '{category}' 的百分比值 '{percentage_str}' 无效，已跳过")
    
    if not parsed_data:
        print("警告：没有有效数据可用于绘图")
        exit()
    
    # 按百分比从大到小排序（增强可读性）
    parsed_data.sort(key=lambda x: x['percentage'], reverse=True)
    
    # 提取排序后的类别名和百分比
    categories = [item['category'] for item in parsed_data]
    percentages = [item['percentage'] for item in parsed_data]
    
    # 动态调整画布宽度（根据类别数量）
    fig_width = max(12, len(categories) * 0.9)  # 类别越多，画布越宽
    fig, ax = plt.subplots(figsize=(fig_width, 8))
    
    # 绘制柱状图（使用渐变色）
    x_pos = np.arange(len(categories))
    bars = ax.bar(
        x_pos,
        percentages,
        color=plt.cm.plasma(np.linspace(0, 0.9, len(categories))),  # 渐变色方案
        edgecolor='gray',
        alpha=0.85
    )
    
    # 在柱子上方添加百分比标签（保留两位小数）
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,  # 柱子中心x坐标
            height + 1,  # 标签位置（柱子顶部上方）
            f'{percentages[i]:.2f}%',  # 显示百分比
            ha='center',
            va='bottom',
            fontsize=9,
            color='#2c3e50'
        )
    
    # 设置图表标题和坐标轴标签
    ax.set_title('各类型处理差异的平均匹配度百分比', fontsize=16, pad=20, fontweight='bold')
    ax.set_xlabel('处理类型', fontsize=12, labelpad=10)
    ax.set_ylabel('平均匹配度（%）', fontsize=12, labelpad=10)
    
    # 设置x轴刻度和标签（旋转避免文字重叠）
    ax.set_xticks(x_pos)
    ax.set_xticklabels(categories, rotation=45, ha='right', fontsize=10, rotation_mode='anchor')
    
    # 设置y轴范围（从0开始，留10%余量）
    max_percent = max(percentages)
    ax.set_ylim(0, max_percent * 1.1 if max_percent != 0 else 100)
    
    # 美化图表：添加网格线、隐藏顶部和右侧边框
    ax.yaxis.grid(True, linestyle='--', alpha=0.6)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # 调整布局，避免标签被截断
    plt.tight_layout()
    
    # 保存图表到conclude文件夹
    save_path = os.path.join(output_dir, '各类型处理差异平均匹配度柱状图.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"图表已成功保存至：{save_path}")
    
    # 显示图表
    plt.show()

except FileNotFoundError:
    print(f"错误：文件不存在 - {file_path}")
except json.JSONDecodeError:
    print(f"错误：文件不是有效的JSON格式 - {file_path}")
except Exception as e:
    print(f"发生错误：{str(e)}")