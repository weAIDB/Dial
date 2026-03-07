# utils.py
import os
import re
import json
import textwrap
from .config import RESULT_JSON_PATH, DB_TYPE_TO_RULE_FILE, SUPPORTED_DBS, RULES_ROOT_DIR

def ensure_dir_exists(dir_path):
    """Ensure the output directory exists"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Created output directory: {dir_path}")

def truncate_content(content, max_length=60000):
    """Truncate overly long retrieval result content"""
    if not content:
        return ""
    if len(content) <= max_length:
        return content

    chunks = re.split(r'(=== Relevant Chunk \d+:)|(=== Relevant Syntax Reference \d+:)', content)
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
        return "".join(truncated) + "\n\n[Content has been truncated, key syntax information retained]"
    else:
        return content[:max_length] + "\n\n[Content truncated due to excessive length]"

def clean_nl2_rewrite(text):
    """Clean nl2_rewrite format"""
    if not text: return ""
    text = re.sub(r'\n+', ' ', text.strip())
    text = re.sub(r'\s+', ' ', text)
    return text

def load_db_rule_file(db_type):
    """Load rule file for specified database"""
    if db_type not in DB_TYPE_TO_RULE_FILE:
        raise ValueError(f"Unsupported database type: {db_type}, supported types are: {SUPPORTED_DBS}")
    
    rule_filename = DB_TYPE_TO_RULE_FILE[db_type]

    rule_file_path = os.path.join(RULES_ROOT_DIR, rule_filename)
    
    if not os.path.exists(rule_file_path):
        raise FileNotFoundError(f"Rule file does not exist: {rule_file_path}")
    
    try:
        with open(rule_file_path, 'r', encoding='utf-8') as f:
            rule_content = f.read().strip()
        print(f"✅ Successfully loaded complete {db_type} rule file, file size: {len(rule_content)} characters")
        return rule_content
    except Exception as e:
        raise RuntimeError(f"Failed to load {db_type} rule file: {str(e)}") from e

def get_retrieval_items():
    """Get data items and parse db_id"""
    try:
        if not os.path.exists(RESULT_JSON_PATH):
            raise FileNotFoundError(f"Data file does not exist: {RESULT_JSON_PATH}")

        with open(RESULT_JSON_PATH, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        
        items = []
        if isinstance(input_data, list):
            for idx, entry in enumerate(input_data):
                if "question" not in entry: continue
                
                # [Read db_id]
                db_id = entry.get("db_id", "").strip()
                
                items.append({
                    "index": idx + 1,
                    "question": entry.get("question", "").strip(),
                    "nl2_rewrite": clean_nl2_rewrite(entry.get("nl2_rewrite", "")),
                    "db_id": db_id,  # Core field
                    "question_id": entry.get("question_id"),
                    "difficulty": entry.get("difficulty"),
                    "true_tables_columns": entry.get("true_tables_columns", ""),
                    "retrieval_results": entry.get("retrieval_results", {})
                })
        
        print(f"Successfully loaded {len(items)} data items")
        return items
    except Exception as e:
        raise RuntimeError(f"Failed to load data: {str(e)}") from e
    
def parse_sql_result(sql_content, target_db_type):
    """
    Parse generated SQL results (Enhanced version: supports multiple Markdown formats and plain text fallback)
    """
    if not sql_content:
        return {target_db_type: ""}

    # Clean input
    sql_content = sql_content.strip()

    # 1. Try to match ### DB_TYPE format (Standard format required in Prompt)
    # Compatible: ### SQLite \n ```sql ... ``` or ### SQLite \n SELECT ...
    header_pattern = r'###\s*' + re.escape(target_db_type) + r'\s*(?:```(?:sql|'+ re.escape(target_db_type.lower()) +r')?\s*)?([\s\S]*?)(?:```|###|$)'
    match = re.search(header_pattern, sql_content, re.IGNORECASE)
    
    def clean_sql(raw_sql):
        if not raw_sql: return ""
        # Remove markdown ending
        sql = re.sub(r'```.*$', '', raw_sql, flags=re.MULTILINE)
        # Remove prompt like [MySQL SQL statement]
        sql = re.sub(r'\[.*?SQL statement\]', '', sql)
        # Remove explanatory text (if model adds irrelevant content outside code block)
        # Simple cleaning: remove leading/trailing whitespace
        return sql.strip()

    if match:
        extracted = match.group(1).strip()
        if extracted:
            return {target_db_type: clean_sql(extracted)}

    # 2. Try to match general Markdown code block (```sql ... ```)
    # For cases where model ignores ### header
    fallback_match = re.search(r'```(?:sql|'+ re.escape(target_db_type.lower()) +r')?\s*([\s\S]*?)```', sql_content, re.IGNORECASE)
    if fallback_match:
        return {target_db_type: clean_sql(fallback_match.group(1))}

    # 3. [New] Ultimate fallback: if all text, try to extract via keywords
    # Find first SELECT or WITH until semicolon ends
    # This is a relatively brute-force match to prevent model returning only pure code
    raw_sql_match = re.search(r'\b(SELECT|WITH)\b[\s\S]+?;', sql_content, re.IGNORECASE)
    if raw_sql_match:
        return {target_db_type: clean_sql(raw_sql_match.group(0))}

    # 4. If no semicolon but looks like SQL (starts with SELECT), return all directly
    if sql_content.upper().startswith("SELECT") or sql_content.upper().startswith("WITH"):
         return {target_db_type: clean_sql(sql_content)}

    return {target_db_type: ""}

def get_final_sql(item_result, target_db_type):
    """Get final generated valid SQL statement"""
    invalid_sql_markers = ["Generation failed: No valid SQL obtained", "", None, "Generation failed"]
    
    # 1. Prioritize checking Magic results (as it's the last attempted repair method)
    magic_status = item_result.get("magic_execution_status")
    magic_sql = item_result.get("magic_generated_sql")
    if magic_status == "success" and magic_sql not in invalid_sql_markers:
        return magic_sql

    # 2. Check second (Standard RAG Fix) results
    # Note: If Logic Fix succeeds, it usually overwrites second_generated_sql or has a separate field
    # In original code, Logic Fix writes results back to second_generated_sql (around line 318 in main.py)
    # So just check second here
    if item_result.get("final_execution_status") == "success":
        second_sql = item_result.get("second_generated_sql")
        if second_sql and second_sql not in invalid_sql_markers:
            return second_sql
        
        first_sql = item_result.get("first_generated_sql")
        if first_sql and first_sql not in invalid_sql_markers:
            return first_sql

    # 3. If all failed, return non-empty content in order
    if magic_sql and magic_sql not in invalid_sql_markers:
        return magic_sql
    
    second_sql = item_result.get("second_generated_sql")
    if second_sql and second_sql not in invalid_sql_markers:
        return second_sql
        
    first_sql = item_result.get("first_generated_sql")
    if first_sql and first_sql not in invalid_sql_markers:
        return first_sql
        
    return "Generation failed"

def select_target_db():
    """Select target database via command line"""
    print("\n=== Please select the database type for SQL generation ===")
    for i, db_type in enumerate(SUPPORTED_DBS, 1):
        print(f"{i}. {db_type}")
    
    while True:
        user_input = input("\nPlease enter a number (1-5) to select the database: ").strip()
        if user_input.isdigit():
            selected_idx = int(user_input) - 1
            if 0 <= selected_idx < len(SUPPORTED_DBS):
                target_db = SUPPORTED_DBS[selected_idx]
                # Check if connection is configured
                if target_db in ["MySQL", "PostgreSQL", "SQLite"]:
                     if target_db not in os.getenv("DB_CONNECT_CONFIGS", {}):
                         # Simple logic check here, actually in config
                         pass
                print(f"\n✅ Target database selected: {target_db}")
                return target_db
            else:
                print(f"❌ Invalid input! Please enter a number between 1 and {len(SUPPORTED_DBS)}")
        else:
            print("❌ Invalid input! Please enter a number")