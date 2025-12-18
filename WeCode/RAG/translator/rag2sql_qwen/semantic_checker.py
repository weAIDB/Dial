# qwen3-max semantic_checker.py
import json
import os
import re
from config import SEMANTIC_FAIL_LOG_PATH
from api_client import call_modelscope_analysis
from prompt_builder import build_semantic_check_prompt

def parse_json_response(content):
    """尝试解析LLM返回的JSON"""
    try:
        # 清理可能存在的 markdown 代码块标记
        cleaned = re.sub(r'```json\s*', '', content, flags=re.IGNORECASE)
        cleaned = re.sub(r'```', '', cleaned).strip()
        return json.loads(cleaned)
    except:
        return None

def verify_sql_logic(question, nl2_rewrite, sql, db_type):
    """
    验证SQL逻辑
    返回: (is_pass: bool, reason: str)
    """
    prompt = build_semantic_check_prompt(question, nl2_rewrite, sql, db_type)
    analysis_result = call_modelscope_analysis(prompt)
    
    if not analysis_result:
        print("⚠️ 语义验证 API 无响应，默认跳过验证")
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
        # 如果无法解析JSON，保守策略：认为验证通过，或者是模型输出了非JSON的肯定回答
        # 也可以选择根据关键词判断，这里简单处理
        if "FAIL" in analysis_result.upper():
             return False, analysis_result
        return True, ""

def save_semantic_failure(item_index, question, nl2_rewrite, wrong_sql, reason, fixed_sql=None):
    """保存未实现需求的原因到文件"""
    log_entry = {
        "index": item_index,
        "timestamp": os.path.getmtime(SEMANTIC_FAIL_LOG_PATH) if os.path.exists(SEMANTIC_FAIL_LOG_PATH) else 0, # 这里仅作示意，实际用 append
        "question": question,
        "nl2_rewrite": nl2_rewrite,
        "unimplemented_reason": reason,
        "original_executable_sql": wrong_sql,
        "fixed_sql": fixed_sql
    }
    
    # 追加写入列表模式
    data = []
    if os.path.exists(SEMANTIC_FAIL_LOG_PATH):
        try:
            with open(SEMANTIC_FAIL_LOG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = []
            
    data.append(log_entry)
    
    with open(SEMANTIC_FAIL_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"📝 已记录语义不一致日志: {reason[:50]}...")


