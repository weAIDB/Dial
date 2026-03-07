# qwen3-max semantic_checker.py
import json
import os
import re
from .config import SEMANTIC_FAIL_LOG_PATH
from .api_client import call_modelscope_analysis
from .prompt_builder import build_semantic_check_prompt

def parse_json_response(content):
    """Attempt to parse JSON returned by the LLM"""
    try:
        # Clean potential markdown code block markers
        cleaned = re.sub(r'```json\s*', '', content, flags=re.IGNORECASE)
        cleaned = re.sub(r'```', '', cleaned).strip()
        return json.loads(cleaned)
    except Exception:
        return None

def verify_sql_logic(question, nl2_rewrite, sql, db_type):
    """
    Verify SQL logic consistency.
    Returns: (is_pass: bool, reason: str)
    """
    prompt = build_semantic_check_prompt(question, nl2_rewrite, sql, db_type)
    analysis_result = call_modelscope_analysis(prompt)
    
    if not analysis_result:
        print("⚠️ Semantic verification API no response, skipping validation by default")
        return True, ""
        
    result_json = parse_json_response(analysis_result)
    
    if result_json:
        status = result_json.get("status", "PASS").upper()
        reason = result_json.get("reason", "")
        if status == "FAIL":
            return False, reason
        else:
            return True, ""
    else:
        # Conservative strategy if JSON parsing fails: 
        # Assume pass unless "FAIL" keyword is explicitly found in the raw text.
        if "FAIL" in analysis_result.upper():
             return False, analysis_result
        return True, ""

def save_semantic_failure(item_index, question, nl2_rewrite, wrong_sql, reason, fixed_sql=None):
    """Save reasons for unimplemented requirements to a log file"""
    log_entry = {
        "index": item_index,
        "timestamp": os.path.getmtime(SEMANTIC_FAIL_LOG_PATH) if os.path.exists(SEMANTIC_FAIL_LOG_PATH) else 0,
        "question": question,
        "nl2_rewrite": nl2_rewrite,
        "unimplemented_reason": reason,
        "original_executable_sql": wrong_sql,
        "fixed_sql": fixed_sql
    }
    
    # Append to list mode
    data = []
    if os.path.exists(SEMANTIC_FAIL_LOG_PATH):
        try:
            with open(SEMANTIC_FAIL_LOG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = []
            
    data.append(log_entry)
    
    with open(SEMANTIC_FAIL_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"📝 Semantic inconsistency logged: {reason[:50]}...")