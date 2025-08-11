# #归类
# #归类

# import json
# import os

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

# def create_category_mapping():
#     """创建原始差异类型到16个大类的映射关系"""
#     return {
#         # 1. 数据去重（DISTINCT 相关）
#         "DISTINCT语法": "数据去重（DISTINCT 相关）",
        
#         # 2. 分组聚合（GROUP BY 子句）
#         "GROUP BY子句": "分组聚合（GROUP BY 子句）",
#         "GROUP BY子句格式": "分组聚合（GROUP BY 子句）",
        
#         # 3. 分组后的筛选（HAVING 子句）
#         "HAVING子句": "分组后的筛选（HAVING 子句）",
        
#         # 4. 聚合函数与引用
#         "聚合函数引用": "聚合函数与引用",
#         "聚合查询结构": "聚合函数与引用",
        
#         # 5. 表连接（JOIN）相关
#         "JOIN子句格式": "表连接（JOIN）相关",
#         "JOIN条件中的列引用": "表连接（JOIN）相关",
#         "JOIN条件引用": "表连接（JOIN）相关",
#         "JOIN条件格式": "表连接（JOIN）相关",
#         "JOIN条件语法": "表连接（JOIN）相关",
#         "JOIN语法": "表连接（JOIN）相关",
#         "连接条件引用": "表连接（JOIN）相关",
        
#         # 6. 模式匹配（LIKE）相关
#         "LIKE子句的字符串匹配": "模式匹配（LIKE）相关",
#         "LIKE条件语法": "模式匹配（LIKE）相关",
#         "LIKE模式匹配": "模式匹配（LIKE）相关",
        
#         # 7. 分页（LIMIT）语法
#         "LIMIT语法": "分页（LIMIT）语法",
        
#         # 8. 空值（NULL）处理
#         "NULLS排序处理": "空值（NULL）处理",
#         "NULL值排序": "空值（NULL）处理",
#         "NULL值排序处理": "空值（NULL）处理",
#         "NULL值排序语法": "空值（NULL）处理",
#         "NULL处理语法": "空值（NULL）处理",
#         "NULL排序": "空值（NULL）处理",
#         "NULL排序处理": "空值（NULL）处理",
#         "NULL排序语法": "空值（NULL）处理",
#         "NULL检查语法": "空值（NULL）处理",
#         "空值检查语法": "空值（NULL）处理",
#         "ORDER BY子句NULL处理": "空值（NULL）处理",
#         "排序空值处理": "空值（NULL）处理",
#         "排序选项": "空值（NULL）处理",
        
#         # 9. 排序（ORDER BY）基础语法
#         "ORDER BY子句": "排序（ORDER BY）基础语法",
#         "ORDER BY引用": "排序（ORDER BY）基础语法",
#         "排序与筛选方式": "排序（ORDER BY）基础语法",
        
#         # 10. 筛选条件（WHERE）相关
#         "WHERE子句引用": "筛选条件相关",
#         "WHERE条件中的列引用": "筛选条件相关",
#         "WHERE条件列引用": "筛选条件相关",
#         "WHERE条件引用": "筛选条件相关",
#         "WHERE条件语法": "筛选条件相关",
#         "条件值引用": "筛选条件相关",
#         "条件列引用": "筛选条件相关",
#         "条件表达式": "筛选条件相关",
#         "条件表达式中的列引用": "筛选条件相关",
#         "条件表达式引用": "筛选条件相关",
#         "条件表达式语法": "筛选条件相关",
#         "筛选条件（WHERE）相关":"筛选条件相关",
#         # 11. 列与表引用规则
#         "列别名引用": "列与表引用规则",
#         "列别名引用方式": "列与表引用规则",
#         "列名引用": "列与表引用规则",
#         "列名引用符号": "列与表引用规则",
#         "列名引用语法": "列与表引用规则",
#         "列引用": "列与表引用规则",
#         "列引用格式": "列与表引用规则",
#         "列引用符号": "列与表引用规则",
#         "列引用语法": "列与表引用规则",
#         "特殊列名引用语法": "列与表引用规则",
#         "表别名引用": "列与表引用规则",
#         "表别名引用方式": "列与表引用规则",
#         "表别名引用语法": "列与表引用规则",
#         "表名/列名引用语法": "列与表引用规则",
#         "表名和列名引用": "列与表引用规则",
#         "表名引用": "列与表引用规则",
#         "表名引用方式": "列与表引用规则",
#         "表名引用符号": "列与表引用规则",
#         "表名引用语法": "列与表引用规则",
#         "表引用": "列与表引用规则",
#         "表引用语法": "列与表引用规则",
#         "子查询列引用": "列与表引用规则",
#         "子查询别名命名": "列与表引用规则",
#         "子查询别名引用": "列与表引用规则",
#         "派生表别名语法": "列与表引用规则",
        
#         # 12. 字符串处理
#         "字符串与数字比较": "字符串处理",
#         "字符串分割函数": "字符串处理",
#         "字符串常量": "字符串处理",
#         "字符串常量语法": "字符串处理",
#         "字符串截取函数": "字符串处理",
#         "字符串比较": "字符串处理",
#         "字符串转日期": "字符串处理",
#         "年份格式字符串": "字符串处理",
#         "引号风格": "字符串处理",
        
#         # 13. 数值处理
#         "数值比较": "数值处理",
#         "数值类型处理": "数值处理",
#         "浮点数类型": "数值处理",
#         "浮点数类型转换": "数值处理",
#         "除零处理": "数值处理",
#         "除零错误处理": "数值处理",
        
#         # 14. 日期时间处理
#         "当前日期函数": "日期时间处理",
#         "当前时间戳函数": "日期时间处理",
#         "日期处理": "日期时间处理",
#         "日期处理函数": "日期时间处理",
#         "日期提取函数": "日期时间处理",
#         "日期时间处理": "日期时间处理",
#         "日期格式化函数": "日期时间处理",
#         "日期格式化模式": "日期时间处理",
#         "日期格式匹配": "日期时间处理",
#         "日期格式处理": "日期时间处理",
#         "日期比较": "日期时间处理",
#         "日期类型转换": "日期时间处理",
#         "日期计算": "日期时间处理",
#         "日期计算语法": "日期时间处理",
#         "时间处理函数": "日期时间处理",
#         "时间戳类型转换": "日期时间处理",
#         "时间类型转换": "日期时间处理",
#         "时间间隔处理": "日期时间处理",
#         "年龄计算函数": "日期时间处理",
#         "年龄计算方式": "日期时间处理",
#         "年龄计算语法": "日期时间处理",
        
#         # 15. 类型转换
#         "数据类型转换": "类型转换",
#         "类型转换": "类型转换",
#         "类型转换函数": "类型转换",
#         "类型转换语法": "类型转换",
        
#         # 16. 分析失败
#         "分析失败": "分析失败"
#     }

# def rewrite_differences(data, category_mapping):
#     """将JSON中的difference字段重写为对应的大类"""
#     if not data or not isinstance(data, list):
#         return data

#     rewritten_data = []
#     for item in data:
#         # 处理每条数据中的syntax_differences
#         if "syntax_differences" in item and isinstance(item["syntax_differences"], list):
#             new_syntax_diffs = []
#             for diff in item["syntax_differences"]:
#                 if "difference" in diff:
#                     # 替换为大类名称
#                     original_diff = diff["difference"]
#                     new_diff = category_mapping.get(original_diff, original_diff)
#                     updated_diff = diff.copy()
#                     updated_diff["difference"] = new_diff
#                     new_syntax_diffs.append(updated_diff)
#                 else:
#                     new_syntax_diffs.append(diff)
#             item["syntax_differences"] = new_syntax_diffs

#         # 同步更新causing_part字段
#         if "causing_part" in item:
#             causing_part = item["causing_part"]
#             for original, target in category_mapping.items():
#                 if original in causing_part:
#                     causing_part = causing_part.replace(original, target)
#             item["causing_part"] = causing_part

#         rewritten_data.append(item)
    
#     return rewritten_data

# def main():
#     # 目标文件路径
#     file_path = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\conclude\sqlite_mysql_difference.json"
    
#     # 加载文件数据
#     data = load_json_file(file_path)
#     if not data:
#         return
    
#     # 创建类别映射表
#     category_mapping = create_category_mapping()
    
#     # 重写差异类型
#     updated_data = rewrite_differences(data, category_mapping)
    
#     # 保存结果
#     save_json_file(updated_data, file_path)

# if __name__ == "__main__":
#     main()


#再次分析


import json
import requests
import os
import shutil
from time import sleep
import socket  # 用于网络调试

# 配置参数
TARGET_FILE = r"C:\copy\code\minidev\MINIDEV\sqlite\sqlite_mysql_result\conclude\sqlite_mysql_difference.json"
API_KEY = "sk-578f63b08e74438692e3ebdb42b49934"  # 注意：实际使用中不要暴露密钥
API_URL = "https://api.deepseek.com/chat/completions"
MODEL_NAME = "deepseek-chat"  # 使用DeepSeek Chat 2.0模型
BACKUP_SUFFIX = ".backup"

# 网络配置（根据实际环境修改）
USE_PROXY = False  # 如果需要代理，设为True
PROXY = {
    "http": "http://your-proxy:port",
    "https": "https://your-proxy:port"
}
VERIFY_SSL = True  # 若SSL验证失败，可临时设为False（不推荐生产环境）


def test_api_connectivity():
    """测试API端点的网络连通性"""
    print("\n=== 测试API连通性 ===")
    try:
        # 测试DNS解析
        ip_address = socket.gethostbyname("api.deepseek.com")
        print(f"DNS解析成功: api.deepseek.com -> {ip_address}")
        
        # 测试TCP连接
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            result = s.connect_ex((ip_address, 443))
            if result == 0:
                print("TCP连接成功（443端口可达）")
            else:
                print(f"TCP连接失败，错误码: {result}（可能被防火墙阻止）")
    except Exception as e:
        print(f"网络连通性测试失败: {str(e)}")


def create_backup(file_path):
    """创建文件备份，防止数据丢失"""
    backup_path = f"{file_path}{BACKUP_SUFFIX}"
    try:
        shutil.copy2(file_path, backup_path)
        print(f"已创建备份文件: {backup_path}")
        return True
    except Exception as e:
        print(f"创建备份失败: {str(e)}")
        return False


def load_json_data(file_path):
    """加载并验证JSON数据"""
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 - {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误: JSON解析失败 - {str(e)}")
        return None
    except Exception as e:
        print(f"错误: 加载文件失败 - {str(e)}")
        return None


def is_failed_analysis(item):
    """判断条目是否为分析失败状态"""
    required_fields = ["question", "mysql_sql", "sqlite_sql", "syntax_differences"]
    for field in required_fields:
        if field not in item:
            return True
    
    if not isinstance(item["syntax_differences"], list):
        return True
    
    for diff in item["syntax_differences"]:
        if isinstance(diff, dict) and diff.get("difference", "").lower() == "分析失败":
            return True
    
    return False


def query_model(question, sqlite_sql, mysql_sql, max_retries=3):
    """调用大模型分析SQL语法差异（增加网络调试和代理支持）"""
    if not API_KEY:
        print("错误: 请配置有效的API_KEY")
        return None
    
    prompt = f"""
    任务：详细分析SQLite和MySQL语句之间的语法差异，按照指定格式输出结果。
    
    自然语言问题：{question}
    SQLite语句：{sqlite_sql}
    MySQL语句：{mysql_sql}
    
    分析要求：
    1. 找出两条SQL语句之间所有语法差异
    2. 对每个差异，需明确：
       - 差异类型（difference）
       - 差异详情（detail）
       - 导致差异的问题子串（question_causing_substring）
       - MySQL中的差异代码片段（mysql_differing_substring）
       - SQLite中的差异代码片段（sqlite_differing_substring）
    3. 仅返回JSON数组，每个元素为一个差异对象，无任何额外文本
    4. 如果没有差异或无法分析，返回空数组
    
    输出示例：
    [
        {{
            "difference": "条件表达式语法",
            "detail": "MySQL使用CASE WHEN语句，SQLite使用IIF函数",
            "question_causing_substring": "ratio of customers who pay in EUR against customers who pay in CZK",
            "mysql_differing_substring": "CASE WHEN `Currency` = 'EUR' THEN 1 ELSE 0 END",
            "sqlite_differing_substring": "IIF(Currency = 'EUR', 1, 0)"
        }}
    ]
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "temperature": 0.2
    }
    
    # 配置代理（如果需要）
    proxies = PROXY if USE_PROXY else None
    
    for retry in range(max_retries):
        try:
            print(f"\n第{retry+1}次尝试连接API...")
            response = requests.post(
                API_URL,
                headers=headers,
                json=payload,
                timeout=30,
                proxies=proxies,
                verify=VERIFY_SSL  # 控制SSL验证
            )
            
            # 打印HTTP状态码（辅助调试）
            print(f"API响应状态码: {response.status_code}")
            
            if response.status_code == 401:
                print("错误: API密钥无效或已过期")
                return None
            if response.status_code == 429:
                wait_time = 2 ** retry
                print(f"请求频率超限，等待{wait_time}秒后重试...")
                sleep(wait_time)
                continue
            if response.status_code != 200:
                print(f"API请求失败: {response.text[:500]}")
                return None
            
            model_output = response.json()["choices"][0]["message"]["content"].strip()
            model_output = model_output.replace("```json", "").replace("```", "").strip()
            
            try:
                result = json.loads(model_output)
                return result if isinstance(result, list) else None
            except json.JSONDecodeError as e:
                print(f"模型输出解析失败: {str(e)}, 原始输出: {model_output[:200]}")
                return None
                
        except requests.exceptions.ProxyError:
            print("错误: 代理配置错误或不可用")
            if not USE_PROXY:
                print("提示: 若处于企业网络，可能需要配置代理（修改USE_PROXY和PROXY参数）")
        except requests.exceptions.SSLError:
            print("错误: SSL证书验证失败")
            print("提示: 可尝试将VERIFY_SSL设为False（仅测试用，不安全）")
        except requests.exceptions.ConnectionError:
            print("错误: 网络连接失败（无法到达API服务器）")
            print("提示: 可能被防火墙阻止，或API端点错误")
        except requests.exceptions.Timeout:
            print("错误: 请求超时")
        except Exception as e:
            print(f"请求异常: {str(e)}")
            
        if retry < max_retries - 1:
            sleep(2)  # 重试间隔
    
    print(f"已达到最大重试次数({max_retries}次)，分析失败")
    return None


def process_analysis_failures(data):
    """处理所有分析失败的条目"""
    if not data:
        return None, 0, 0
    
    is_dict_format = isinstance(data, dict)
    processed_data = {} if is_dict_format else []
    total_analyzed = 0
    successfully_updated = 0
    
    if is_dict_format:
        for category, items in data.items():
            processed_items = []
            for item in items:
                if not isinstance(item, dict):
                    processed_items.append(item)
                    continue
                
                if is_failed_analysis(item):
                    total_analyzed += 1
                    print(f"\n重新分析问题: {item['question'][:60]}...")
                    
                    new_differences = query_model(
                        item["question"],
                        item["sqlite_sql"],
                        item["mysql_sql"]
                    )
                    
                    if new_differences and len(new_differences) > 0:
                        item["syntax_differences"] = new_differences
                        if "causing_part" in item:
                            item["causing_part"] = new_differences[0].get("question_causing_substring", "")
                        processed_items.append(item)
                        successfully_updated += 1
                        print("分析成功，已更新结果")
                    else:
                        print("重新分析失败，将删除该条目")
                else:
                    processed_items.append(item)
            
            processed_data[category] = processed_items
    else:
        for item in data:
            if not isinstance(item, dict):
                processed_data.append(item)
                continue
            
            if is_failed_analysis(item):
                total_analyzed += 1
                print(f"\n重新分析问题: {item['question'][:60]}...")
                
                new_differences = query_model(
                    item["question"],
                    item["sqlite_sql"],
                    item["mysql_sql"]
                )
                
                if new_differences and len(new_differences) > 0:
                    item["syntax_differences"] = new_differences
                    if "causing_part" in item:
                        item["causing_part"] = new_differences[0].get("question_causing_substring", "")
                    processed_data.append(item)
                    successfully_updated += 1
                    print("分析成功，已更新结果")
                else:
                    print("重新分析失败，将删除该条目")
            else:
                processed_data.append(item)
    
    return processed_data, total_analyzed, successfully_updated


def save_processed_data(data, file_path):
    """保存处理后的数据到文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"\n处理完成，结果已保存到: {file_path}")
        return True
    except Exception as e:
        print(f"保存文件失败: {str(e)}")
        return False


def main():
    # 先测试API连通性
    test_api_connectivity()
    
    # 创建备份
    if not create_backup(TARGET_FILE):
        print("无法创建备份，程序退出")
        return
    
    # 加载数据
    data = load_json_data(TARGET_FILE)
    if data is None:
        print("无法加载数据，程序退出")
        return
    
    # 处理分析失败的条目
    processed_data, total_analyzed, successfully_updated = process_analysis_failures(data)
    
    # 保存结果
    if processed_data is not None:
        save_processed_data(processed_data, TARGET_FILE)
    
    # 输出统计
    print("\n=== 处理统计 ===")
    print(f"总共分析失败的条目: {total_analyzed}")
    print(f"重新分析成功并更新的条目: {successfully_updated}")
    print(f"仍然失败并被删除的条目: {total_analyzed - successfully_updated}")


if __name__ == "__main__":
    main()