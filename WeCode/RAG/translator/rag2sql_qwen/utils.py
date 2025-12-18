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
    """获取多库检索结果项（从JSON文件读取）"""
    try:
        if not os.path.exists(RESULT_JSON_PATH):
            raise FileNotFoundError(f"多库检索结果文件不存在: {RESULT_JSON_PATH}")
        
        with open(RESULT_JSON_PATH, 'r', encoding='utf-8') as f:
            output_data = json.load(f)
        
        retrieval_items = []
        if isinstance(output_data, list):
            for idx, item in enumerate(output_data):
                if isinstance(item, dict) and "retrieval_results" in item and "question" in item:
                    # 过滤无效检索结果
                    all_empty = all(
                        not content or content == "No relevant content retrieved"
                        for content in item.get("retrieval_results", {}).values()
                    )
                    if all_empty and item.get("retrieval_result") != "Error":
                        # print(f"⚠️ 第{idx+1}条数据无有效检索结果，跳过")
                        # 暂时不跳过，因为可能需要基于 rewrite 生成
                        pass
                    
                    retrieval_items.append({
                        "index": idx + 1,
                        "question": item.get("question", "").strip(),
                        "nl2_rewrite": clean_nl2_rewrite(item.get("nl2_rewrite", "")),
                        "retrieval_results": item.get("retrieval_results", {}),
                        "question_id": item.get("question_id", None),
                        "difficulty": item.get("difficulty", None)
                    })
        
        if not retrieval_items:
            raise RuntimeError("多库检索结果文件中未找到有效的检索结果项")
            
        print(f"成功加载 {len(retrieval_items)} 个有效检索结果项")
        return retrieval_items
            
    except Exception as e:
        raise RuntimeError(f"获取检索结果项失败: {str(e)}") from e

def parse_sql_result(sql_content, target_db_type):
    """解析生成的SQL结果"""
    if not sql_content:
        return {target_db_type: ""}

    # 定义针对不同数据库的正则，增加了对 Markdown ```sql 代码块的兼容
    db_patterns = {
        "MySQL": r'### MySQL\s*(?:```(?:sql|mysql)?\s*)?([\s\S]*?)(?:```|### |$)',
        "PostgreSQL": r'### PostgreSQL\s*(?:```(?:sql|postgresql)?\s*)?([\s\S]*?)(?:```|### |$)',
        "SQLite": r'### SQLite\s*(?:```(?:sql|sqlite)?\s*)?([\s\S]*?)(?:```|### |$)',
        "Oracle": r'### Oracle\s*(?:```(?:sql|oracle)?\s*)?([\s\S]*?)(?:```|### |$)',
        "SQL Server": r'### SQL Server\s*(?:```(?:sql|mssql)?\s*)?([\s\S]*?)(?:```|### |$)'
    }
    
    if target_db_type not in db_patterns:
        # Fallback regex if specific type not found
        pattern = r'### ' + re.escape(target_db_type) + r'\s*([\s\S]*?)(?=### |$)'
    else:
        pattern = db_patterns[target_db_type]
    
    match = re.search(pattern, sql_content, re.IGNORECASE)
    
    def clean_sql(raw_sql):
        if not raw_sql: return ""
        # 去除 markdown 结尾
        sql = re.sub(r'```.*$', '', raw_sql, flags=re.MULTILINE)
        # 去除 [MySQL SQL语句] 这种提示符
        sql = re.sub(r'\[.*?SQL语句\]', '', sql)
        # 压缩多余换行
        sql = re.sub(r'\n+', ' ', sql).strip()
        return sql
    
    if match:
        return {target_db_type: clean_sql(match.group(1))}
    
    # 如果没匹配到，尝试直接找代码块
    fallback_match = re.search(r'```sql\s*([\s\S]*?)```', sql_content, re.IGNORECASE)
    if fallback_match:
        return {target_db_type: clean_sql(fallback_match.group(1))}
        
    return {target_db_type: ""}

def get_final_sql(item_result, target_db_type):
    """获取最终生成的有效SQL语句"""
    invalid_sql_markers = ["生成失败：未获取到有效SQL", "", None]
    
    # 优先返回成功的SQL
    if item_result.get("final_execution_status") == "success":
        # 如果第二次成功，返回第二次
        second_status = item_result.get("second_execution_status")
        second_sql = item_result.get("second_generated_sql")
        if second_status == "success" and second_sql not in invalid_sql_markers:
            return second_sql
        
        # 如果第一次成功，返回第一次
        first_status = item_result.get("first_execution_status")
        first_sql = item_result.get("first_generated_sql")
        if first_status == "success" and first_sql not in invalid_sql_markers:
            return first_sql

    # 如果都失败，返回最后一次生成的非空内容
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