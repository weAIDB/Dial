# utils.py
import os
import re
import json
import textwrap
from config import RESULT_JSON_PATH, DB_TYPE_TO_RULE_FILE, SUPPORTED_DBS, RULES_ROOT_DIR

def ensure_dir_exists(dir_path):
    """确保输出目录存在"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"创建输出目录: {dir_path}")

def truncate_content(content, max_length=60000):
    """截断过长的检索结果内容"""
    if not content:
        return ""
    if len(content) <= max_length:
        return content
    
    # 尝试按 Chunk 分割截断
    chunks = re.split(r'(=== Relevant Chunk \d+:)|(=== 相关语法参考 \d+:)', content)
    if len(chunks) > 1:
        truncated = []
        current_length = 0
        for chunk in chunks:
            if not chunk: continue
            if current_length + len(chunk) > max_length:
                remaining = max_length - current_length
                truncated.append(chunk[:remaining])
                break
            truncated.append(chunk)
            current_length += len(chunk)
        return "".join(truncated) + "\n\n[内容已截断，保留关键语法信息]"
    else:
        return content[:max_length] + "\n\n[内容过长已截断]"

def clean_nl2_rewrite(text):
    """清理nl2_rewrite格式"""
    if not text: return ""
    text = re.sub(r'\n+', ' ', text.strip())
    text = re.sub(r'\s+', ' ', text)
    return text

def load_db_rule_file(db_type):
    """加载指定数据库的规则文件"""
    if db_type not in DB_TYPE_TO_RULE_FILE:
        raise ValueError(f"不支持的数据库类型: {db_type}，支持的类型为：{SUPPORTED_DBS}")
    
    rule_filename = DB_TYPE_TO_RULE_FILE[db_type]
    # 直接使用从 config 导入的 RULES_ROOT_DIR
    rule_file_path = os.path.join(RULES_ROOT_DIR, rule_filename)
    
    if not os.path.exists(rule_file_path):
        raise FileNotFoundError(f"规则文件不存在: {rule_file_path}")
    
    try:
        with open(rule_file_path, 'r', encoding='utf-8') as f:
            rule_content = f.read().strip()
        print(f"✅ 成功加载{db_type}完整规则文件，文件大小：{len(rule_content)} 字符")
        return rule_content
    except Exception as e:
        raise RuntimeError(f"加载{db_type}规则文件失败: {str(e)}") from e

def get_retrieval_items():
    """获取数据项，解析 db_id"""
    try:
        if not os.path.exists(RESULT_JSON_PATH):
            raise FileNotFoundError(f"数据文件不存在: {RESULT_JSON_PATH}")

        with open(RESULT_JSON_PATH, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        
        items = []
        if isinstance(input_data, list):
            for idx, entry in enumerate(input_data):
                if "question" not in entry: continue
                
                # [读取 db_id]
                db_id = entry.get("db_id", "").strip()
                
                items.append({
                    "index": idx + 1,
                    "question": entry.get("question", "").strip(),
                    "nl2_rewrite": clean_nl2_rewrite(entry.get("nl2_rewrite", "")),
                    "db_id": db_id,  # 核心字段
                    "question_id": entry.get("question_id"),
                    "difficulty": entry.get("difficulty"),
                    "true_tables_columns": entry.get("true_tables_columns", ""),
                    "retrieval_results": entry.get("retrieval_results", {})
                })
        
        print(f"成功加载 {len(items)} 条数据")
        return items
    except Exception as e:
        raise RuntimeError(f"加载数据失败: {str(e)}") from e
    
def parse_sql_result(sql_content, target_db_type):
    """
    解析生成的SQL结果（增强版：支持多种Markdown格式及纯文本后备）
    """
    if not sql_content:
        return {target_db_type: ""}

    # 清理输入
    sql_content = sql_content.strip()

    # 1. 尝试匹配 ### DB_TYPE 格式 (Prompt中要求的标准格式)
    # 兼容: ### SQLite \n ```sql ... ``` 或 ### SQLite \n SELECT ...
    header_pattern = r'###\s*' + re.escape(target_db_type) + r'\s*(?:```(?:sql|'+ re.escape(target_db_type.lower()) +r')?\s*)?([\s\S]*?)(?:```|###|$)'
    match = re.search(header_pattern, sql_content, re.IGNORECASE)
    
    def clean_sql(raw_sql):
        if not raw_sql: return ""
        # 去除 markdown 结尾
        sql = re.sub(r'```.*$', '', raw_sql, flags=re.MULTILINE)
        # 去除 [MySQL SQL语句] 这种提示符
        sql = re.sub(r'\[.*?SQL语句\]', '', sql)
        # 去除解释性文字 (如果模型在代码块外废话)
        # 简单清洗：去除首尾空白
        return sql.strip()

    if match:
        extracted = match.group(1).strip()
        if extracted:
            return {target_db_type: clean_sql(extracted)}

    # 2. 尝试匹配通用的 Markdown 代码块 (```sql ... ```)
    # 针对模型忽略了 ### 头的情况
    fallback_match = re.search(r'```(?:sql|'+ re.escape(target_db_type.lower()) +r')?\s*([\s\S]*?)```', sql_content, re.IGNORECASE)
    if fallback_match:
        return {target_db_type: clean_sql(fallback_match.group(1))}

    # 3. [新增] 终极后备：如果全是文本，尝试通过关键字提取
    # 查找第一个 SELECT 或 WITH，直到分号结束
    # 这是一个比较暴力的匹配，防止模型只返回了纯代码
    raw_sql_match = re.search(r'\b(SELECT|WITH)\b[\s\S]+?;', sql_content, re.IGNORECASE)
    if raw_sql_match:
        return {target_db_type: clean_sql(raw_sql_match.group(0))}

    # 4. 如果连分号都没有，但看起来像SQL（以SELECT开头），直接返回全部
    if sql_content.upper().startswith("SELECT") or sql_content.upper().startswith("WITH"):
         return {target_db_type: clean_sql(sql_content)}

    return {target_db_type: ""}

def get_final_sql(item_result, target_db_type):
    """获取最终生成的有效SQL语句"""
    invalid_sql_markers = ["生成失败：未获取到有效SQL", "", None, "生成失败"]
    
    # 1. 优先检查 Magic 结果 (因为它是最后尝试的修复手段)
    magic_status = item_result.get("magic_execution_status")
    magic_sql = item_result.get("magic_generated_sql")
    if magic_status == "success" and magic_sql not in invalid_sql_markers:
        return magic_sql

    # 2. 检查第二次 (Standard RAG Fix) 结果
    # 注意：如果逻辑修正(Logic Fix)成功，它通常覆盖在 second_generated_sql 或者有单独字段
    # 原代码中逻辑修正在 main.py 里将结果写回了 second_generated_sql (第318行左右)
    # 所以这里检查 second 即可
    if item_result.get("final_execution_status") == "success":
        second_sql = item_result.get("second_generated_sql")
        if second_sql and second_sql not in invalid_sql_markers:
            return second_sql
        
        first_sql = item_result.get("first_generated_sql")
        if first_sql and first_sql not in invalid_sql_markers:
            return first_sql

    # 3. 如果都失败，按顺序返回非空内容
    if magic_sql and magic_sql not in invalid_sql_markers:
        return magic_sql
    
    second_sql = item_result.get("second_generated_sql")
    if second_sql and second_sql not in invalid_sql_markers:
        return second_sql
        
    first_sql = item_result.get("first_generated_sql")
    if first_sql and first_sql not in invalid_sql_markers:
        return first_sql
        
    return "生成失败"

def select_target_db():
    """命令行选择目标数据库"""
    print("\n=== 请选择要生成SQL的数据库类型 ===")
    for i, db_type in enumerate(SUPPORTED_DBS, 1):
        print(f"{i}. {db_type}")
    
    while True:
        user_input = input("\n请输入数字（1-5）选择数据库：").strip()
        if user_input.isdigit():
            selected_idx = int(user_input) - 1
            if 0 <= selected_idx < len(SUPPORTED_DBS):
                target_db = SUPPORTED_DBS[selected_idx]
                # 检查是否配置了连接
                if target_db in ["MySQL", "PostgreSQL", "SQLite"]:
                     if target_db not in os.getenv("DB_CONNECT_CONFIGS", {}):
                         # 这里简单的逻辑检查，实际上config里有
                         pass
                print(f"\n✅ 已选择目标数据库：{target_db}")
                return target_db
            else:
                print(f"❌ 输入无效！请输入1-{len(SUPPORTED_DBS)}之间的数字")
        else:
            print("❌ 输入无效！请输入数字")