# # # # # # # # import json
# # # # # # # # import os

# # # # # # # # # 定义文件路径
# # # # # # # # file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\conclude\postgres_mysql_difference.json"

# # # # # # # # # 定义连接符和后缀（根据示例中的格式调整）
# # # # # # # # connector = "、"  # 用于连接多个difference的分隔符
# # # # # # # # suffix = ""   # 末尾固定后缀

# # # # # # # # try:
# # # # # # # #     # 读取JSON文件
# # # # # # # #     with open(file_path, 'r', encoding='utf-8') as file:
# # # # # # # #         data = json.load(file)
    
# # # # # # # #     # 检查数据是否为列表
# # # # # # # #     if not isinstance(data, list):
# # # # # # # #         raise ValueError("JSON文件的根元素不是一个列表")
    
# # # # # # # #     # 处理每个条目
# # # # # # # #     for item in data:
# # # # # # # #         # 检查是否包含必要的字段
# # # # # # # #         if "syntax_differences" in item and isinstance(item["syntax_differences"], list):
# # # # # # # #             # 提取所有difference的值
# # # # # # # #             differences = [
# # # # # # # #                 diff["difference"] 
# # # # # # # #                 for diff in item["syntax_differences"] 
# # # # # # # #                 if "difference" in diff  # 确保diff中包含difference字段
# # # # # # # #             ]
            
# # # # # # # #             # 生成新的causing_part内容
# # # # # # # #             if differences:
# # # # # # # #                 # 用连接符拼接所有difference，再添加后缀
# # # # # # # #                 new_causing_part = f"{connector.join(differences)}{suffix}"
# # # # # # # #                 # 更新causing_part
# # # # # # # #                 item["causing_part"] = new_causing_part
    
# # # # # # # #     # 创建备份文件
# # # # # # # #     backup_path = f"{file_path}.backup"
# # # # # # # #     if not os.path.exists(backup_path):
# # # # # # # #         with open(backup_path, 'w', encoding='utf-8') as backup_file:
# # # # # # # #             json.dump(data, backup_file, ensure_ascii=False, indent=2)
# # # # # # # #         print(f"已创建备份文件: {backup_path}")
    
# # # # # # # #     # 保存修改后的内容
# # # # # # # #     with open(file_path, 'w', encoding='utf-8') as file:
# # # # # # # #         json.dump(data, file, ensure_ascii=False, indent=2)
    
# # # # # # # #     print(f"处理完成，已更新文件: {file_path}")

# # # # # # # # except FileNotFoundError:
# # # # # # # #     print(f"错误: 找不到文件 {file_path}")
# # # # # # # # except json.JSONDecodeError:
# # # # # # # #     print(f"错误: 文件 {file_path} 不是有效的JSON格式")
# # # # # # # # except Exception as e:
# # # # # # # #     print(f"处理过程中发生错误: {str(e)}")


#归类

import json
import os

def load_json_file(file_path):
    """加载JSON文件并验证有效性"""
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

def save_json_file(data, file_path, backup=True):
    """保存JSON文件并创建备份"""
    try:
        # 创建备份文件
        if backup and os.path.exists(file_path):
            backup_path = f"{file_path}.bak"
            with open(file_path, 'r', encoding='utf-8') as f_in, \
                 open(backup_path, 'w', encoding='utf-8') as f_out:
                f_out.write(f_in.read())
            print(f"已创建备份文件：{backup_path}")
        
        # 保存处理后的数据
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"文件已保存至：{file_path}")
        return True
    except Exception as e:
        print(f"错误：保存文件失败 - {str(e)}")
        return False

def create_category_mapping():
    """创建原始差异类型到16个大类的映射关系"""
    return {
        # 1. 数据去重（DISTINCT 相关）
        "DISTINCT语法": "数据去重（DISTINCT 相关）",
        
        # 2. 分组聚合（GROUP BY 子句）
        "GROUP BY子句": "分组聚合（GROUP BY 子句）",
        "GROUP BY子句格式": "分组聚合（GROUP BY 子句）",
        
        # 3. 分组后的筛选（HAVING 子句）
        "HAVING子句": "分组后的筛选（HAVING 子句）",
        
        # 4. 聚合函数与引用
        "聚合函数引用": "聚合函数与引用",
        "聚合查询结构": "聚合函数与引用",
        
        # 5. 表连接（JOIN）相关
        "JOIN子句格式": "表连接（JOIN）相关",
        "JOIN条件中的列引用": "表连接（JOIN）相关",
        "JOIN条件引用": "表连接（JOIN）相关",
        "JOIN条件格式": "表连接（JOIN）相关",
        "JOIN条件语法": "表连接（JOIN）相关",
        "JOIN语法": "表连接（JOIN）相关",
        "连接条件引用": "表连接（JOIN）相关",
        
        # 6. 模式匹配（LIKE）相关
        "LIKE子句的字符串匹配": "模式匹配（LIKE）相关",
        "LIKE条件语法": "模式匹配（LIKE）相关",
        "LIKE模式匹配": "模式匹配（LIKE）相关",
        
        # 7. 分页（LIMIT）语法
        "LIMIT语法": "分页（LIMIT）语法",
        
        # 8. 空值（NULL）处理
        "NULLS排序处理": "空值（NULL）处理",
        "NULL值排序": "空值（NULL）处理",
        "NULL值排序处理": "空值（NULL）处理",
        "NULL值排序语法": "空值（NULL）处理",
        "NULL处理语法": "空值（NULL）处理",
        "NULL排序": "空值（NULL）处理",
        "NULL排序处理": "空值（NULL）处理",
        "NULL排序语法": "空值（NULL）处理",
        "NULL检查语法": "空值（NULL）处理",
        "空值检查语法": "空值（NULL）处理",
        "ORDER BY子句NULL处理": "空值（NULL）处理",
        "排序空值处理": "空值（NULL）处理",
        "排序选项": "空值（NULL）处理",
        
        # 9. 排序（ORDER BY）基础语法
        "ORDER BY子句": "排序（ORDER BY）基础语法",
        "ORDER BY引用": "排序（ORDER BY）基础语法",
        "排序与筛选方式": "排序（ORDER BY）基础语法",
        
        # 10. 筛选条件（WHERE）相关
        "WHERE子句引用": "筛选条件相关",
        "WHERE条件中的列引用": "筛选条件相关",
        "WHERE条件列引用": "筛选条件相关",
        "WHERE条件引用": "筛选条件相关",
        "WHERE条件语法": "筛选条件相关",
        "条件值引用": "筛选条件相关",
        "条件列引用": "筛选条件相关",
        "条件表达式": "筛选条件相关",
        "条件表达式中的列引用": "筛选条件相关",
        "条件表达式引用": "筛选条件相关",
        "条件表达式语法": "筛选条件相关",
        "筛选条件（WHERE）相关":"筛选条件相关",
        # 11. 列与表引用规则
        "列别名引用": "列与表引用规则",
        "列别名引用方式": "列与表引用规则",
        "列名引用": "列与表引用规则",
        "列名引用符号": "列与表引用规则",
        "列名引用语法": "列与表引用规则",
        "列引用": "列与表引用规则",
        "列引用格式": "列与表引用规则",
        "列引用符号": "列与表引用规则",
        "列引用语法": "列与表引用规则",
        "特殊列名引用语法": "列与表引用规则",
        "表别名引用": "列与表引用规则",
        "表别名引用方式": "列与表引用规则",
        "表别名引用语法": "列与表引用规则",
        "表名/列名引用语法": "列与表引用规则",
        "表名和列名引用": "列与表引用规则",
        "表名引用": "列与表引用规则",
        "表名引用方式": "列与表引用规则",
        "表名引用符号": "列与表引用规则",
        "表名引用语法": "列与表引用规则",
        "表引用": "列与表引用规则",
        "表引用语法": "列与表引用规则",
        "子查询列引用": "列与表引用规则",
        "子查询别名命名": "列与表引用规则",
        "子查询别名引用": "列与表引用规则",
        "派生表别名语法": "列与表引用规则",
        
        # 12. 字符串处理
        "字符串与数字比较": "字符串处理",
        "字符串分割函数": "字符串处理",
        "字符串常量": "字符串处理",
        "字符串常量语法": "字符串处理",
        "字符串截取函数": "字符串处理",
        "字符串比较": "字符串处理",
        "字符串转日期": "字符串处理",
        "年份格式字符串": "字符串处理",
        "引号风格": "字符串处理",
        
        # 13. 数值处理
        "数值比较": "数值处理",
        "数值类型处理": "数值处理",
        "浮点数类型": "数值处理",
        "浮点数类型转换": "数值处理",
        "除零处理": "数值处理",
        "除零错误处理": "数值处理",
        
        # 14. 日期时间处理
        "当前日期函数": "日期时间处理",
        "当前时间戳函数": "日期时间处理",
        "日期处理": "日期时间处理",
        "日期处理函数": "日期时间处理",
        "日期提取函数": "日期时间处理",
        "日期时间处理": "日期时间处理",
        "日期格式化函数": "日期时间处理",
        "日期格式化模式": "日期时间处理",
        "日期格式匹配": "日期时间处理",
        "日期格式处理": "日期时间处理",
        "日期比较": "日期时间处理",
        "日期类型转换": "日期时间处理",
        "日期计算": "日期时间处理",
        "日期计算语法": "日期时间处理",
        "时间处理函数": "日期时间处理",
        "时间戳类型转换": "日期时间处理",
        "时间类型转换": "日期时间处理",
        "时间间隔处理": "日期时间处理",
        "年龄计算函数": "日期时间处理",
        "年龄计算方式": "日期时间处理",
        "年龄计算语法": "日期时间处理",
        
        # 15. 类型转换
        "数据类型转换": "类型转换",
        "类型转换": "类型转换",
        "类型转换函数": "类型转换",
        "类型转换语法": "类型转换",
        
        # 16. 分析失败
        "分析失败": "分析失败"
    }

def rewrite_differences(data, category_mapping):
    """将JSON中的difference字段重写为对应的大类"""
    if not data or not isinstance(data, list):
        return data

    rewritten_data = []
    for item in data:
        # 处理每条数据中的syntax_differences
        if "syntax_differences" in item and isinstance(item["syntax_differences"], list):
            new_syntax_diffs = []
            for diff in item["syntax_differences"]:
                if "difference" in diff:
                    # 替换为大类名称
                    original_diff = diff["difference"]
                    new_diff = category_mapping.get(original_diff, original_diff)
                    updated_diff = diff.copy()
                    updated_diff["difference"] = new_diff
                    new_syntax_diffs.append(updated_diff)
                else:
                    new_syntax_diffs.append(diff)
            item["syntax_differences"] = new_syntax_diffs

        # 同步更新causing_part字段
        if "causing_part" in item:
            causing_part = item["causing_part"]
            for original, target in category_mapping.items():
                if original in causing_part:
                    causing_part = causing_part.replace(original, target)
            item["causing_part"] = causing_part

        rewritten_data.append(item)
    
    return rewritten_data

def main():
    # 目标文件路径
    file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\conclude\postgres_mysql_difference.json"
    
    # 加载文件数据
    data = load_json_file(file_path)
    if not data:
        return
    
    # 创建类别映射表
    category_mapping = create_category_mapping()
    
    # 重写差异类型
    updated_data = rewrite_differences(data, category_mapping)
    
    # 保存结果
    save_json_file(updated_data, file_path)

if __name__ == "__main__":
    main()


    
# # # # # # #将问题归类


# # # # # import json
# # # # # import os

# # # # # def group_by_difference(input_file, output_file):
# # # # #     """
# # # # #     将JSON文件中的数据按"syntax_differences"数组中的"difference"字段分类，并保存到新的JSON文件
    
# # # # #     参数:
# # # # #         input_file: 输入JSON文件路径
# # # # #         output_file: 输出JSON文件路径
# # # # #     """
# # # # #     try:
# # # # #         # 读取输入文件
# # # # #         with open(input_file, 'r', encoding='utf-8') as f:
# # # # #             data = json.load(f)
        
# # # # #         # 确保输入数据是列表类型
# # # # #         if not isinstance(data, list):
# # # # #             raise ValueError("输入JSON文件的根元素必须是列表")
        
# # # # #         # 按"difference"分组
# # # # #         grouped = {}
# # # # #         skipped_items = 0  # 记录跳过的项目数量
# # # # #         total_processed = 0  # 记录处理的差异数量
        
# # # # #         for item in data:
# # # # #             # 检查顶层必要字段
# # # # #             top_level_fields = ["question", "postgres_sql", "mysql_sql"]
# # # # #             missing_top_fields = [field for field in top_level_fields if field not in item]
            
# # # # #             if missing_top_fields:
# # # # #                 skipped_items += 1
# # # # #                 print(f"警告: 跳过缺少顶层字段的数据项，缺少字段: {', '.join(missing_top_fields)}")
# # # # #                 continue
            
# # # # #             # 检查是否有syntax_differences字段且是列表
# # # # #             if "syntax_differences" not in item or not isinstance(item["syntax_differences"], list):
# # # # #                 skipped_items += 1
# # # # #                 print("警告: 跳过缺少有效的syntax_differences数组的数据项")
# # # # #                 continue
            
# # # # #             # 处理每个syntax_difference
# # # # #             for diff in item["syntax_differences"]:
# # # # #                 # 检查差异项中的必要字段
# # # # #                 diff_fields = ["difference", "question_causing_substring", 
# # # # #                              "postgres_differing_substring", "mysql_differing_substring"]
# # # # #                 missing_diff_fields = [field for field in diff_fields if field not in diff]
                
# # # # #                 if missing_diff_fields:
# # # # #                     skipped_items += 1
# # # # #                     print(f"警告: 跳过缺少字段的差异项，缺少字段: {', '.join(missing_diff_fields)}")
# # # # #                     continue
                
# # # # #                 # 准备要保存的条目，包含顶层信息和当前差异信息
# # # # #                 entry = {
# # # # #                     "question": item["question"],
# # # # #                     "postgres_sql": item["postgres_sql"],
# # # # #                     "mysql_sql": item["mysql_sql"],
# # # # #                     "question_causing_substring": diff["question_causing_substring"],
# # # # #                     "postgres_differing_substring": diff["postgres_differing_substring"],
# # # # #                     "mysql_differing_substring": diff["mysql_differing_substring"],
# # # # #                     "difference": diff["difference"],
# # # # #                     "detail": diff.get("detail", "")  # 可选字段
# # # # #                 }
                
# # # # #                 difference = diff["difference"]
# # # # #                 # 确保difference是字符串类型
# # # # #                 if not isinstance(difference, str):
# # # # #                     difference = str(difference)
                
# # # # #                 # 按difference分组，允许重复项
# # # # #                 if difference not in grouped:
# # # # #                     grouped[difference] = []
# # # # #                 grouped[difference].append(entry)
# # # # #                 total_processed += 1
        
# # # # #         # 确保输出目录存在
# # # # #         output_dir = os.path.dirname(output_file)
# # # # #         if not os.path.exists(output_dir):
# # # # #             os.makedirs(output_dir)
        
# # # # #         # 保存结果到输出文件
# # # # #         with open(output_file, 'w', encoding='utf-8') as f:
# # # # #             json.dump(grouped, f, ensure_ascii=False, indent=4)
        
# # # # #         print(f"成功将数据按'difference'分类，结果已保存到: {output_file}")
# # # # #         print(f"共分为 {len(grouped)} 个不同的'difference'类别")
# # # # #         print(f"共处理了 {total_processed} 个差异项")
# # # # #         print(f"处理过程中跳过了 {skipped_items} 个有问题的数据项/差异项")
        
# # # # #     except FileNotFoundError:
# # # # #         print(f"错误: 找不到输入文件 {input_file}")
# # # # #     except json.JSONDecodeError:
# # # # #         print(f"错误: 输入文件 {input_file} 不是有效的JSON格式")
# # # # #     except Exception as e:
# # # # #         print(f"处理过程中发生错误: {str(e)}")

# # # # # if __name__ == "__main__":
# # # # #     # 输入文件路径
# # # # #     input_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\conclude\postgres_mysql_difference.json"
# # # # #     # 输出文件路径
# # # # #     output_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\conclude\pg_mysql_conclusion.json"
    
# # # # #     # 执行分组操作
# # # # #     group_by_difference(input_path, output_path)

# #计算方言部分占自然语言问题的百分比

# import json
# import os
# import shutil

# def calculate_substring_percentage(json_data):
#     """计算每个问题中question_causing_substring占整个question的百分比并添加到对应位置（带%）"""
#     # 遍历每个顶层大字典（如"空值(NULL)处理"）
#     for category, questions_list in json_data.items():
#         # 检查是否是列表类型（根据提供的格式，每个顶层键对应一个列表）
#         if isinstance(questions_list, list):
#             # 遍历列表中的每个问题
#             for question in questions_list:
#                 # 确保必要字段存在
#                 if "question" in question and "question_causing_substring" in question:
#                     full_question = question["question"]
#                     substring = question["question_causing_substring"]
                    
#                     # 计算百分比，避免除以零
#                     if len(full_question) > 0:
#                         percentage = (len(substring) / len(full_question)) * 100
#                         # 保留两位小数并添加百分号
#                         question["substring_percentage"] = f"{round(percentage, 2)}%"
#                     else:
#                         question["substring_percentage"] = "0.00%"
#     return json_data

# def main():
#     # 文件路径
#     file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\conclude\pg_mysql_conclusion.json"
    
#     # 检查文件是否存在
#     if not os.path.exists(file_path):
#         print(f"错误：文件不存在 - {file_path}")
#         return
    
#     try:
#         # 创建文件备份
#         backup_path = f"{file_path}.backup"
#         shutil.copy2(file_path, backup_path)
#         print(f"已创建文件备份: {backup_path}")
        
#         # 读取JSON文件
#         with open(file_path, 'r', encoding='utf-8') as f:
#             json_data = json.load(f)
        
#         # 计算并更新百分比
#         updated_data = calculate_substring_percentage(json_data)
        
#         # 保存更新后的JSON文件
#         with open(file_path, 'w', encoding='utf-8') as f:
#             # 确保中文正常显示且格式美观
#             json.dump(updated_data, f, ensure_ascii=False, indent=4)
        
#         print("处理完成，已更新文件并添加带百分号的substring_percentage字段")
        
#     except json.JSONDecodeError:
#         print("错误：文件不是有效的JSON格式")
#     except Exception as e:
#         print(f"处理过程中发生错误: {str(e)}")

# if __name__ == "__main__":
#     main()
    
    
# #计算平均值


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
#     # 输入文件路径
#     input_json_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\conclude\pg_mysql_conclusion.json"
#     # 输出文件路径
#     output_json_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\conclude\radio.json"
    
#     calculate_average_percentages(input_json_path, output_json_path)
    
    
#画图


import json
import os
import matplotlib.pyplot as plt
import numpy as np

# 文件路径（radio.json的位置）
file_path = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\conclude\radio.json"
# 输出文件夹路径（与radio.json同目录）
output_dir = r"C:\copy\code\minidev\MINIDEV\pg\pg_mysql_result\conclude"

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