# sql_error_analyzer.py
import re
import json
import time
from typing import Dict, Optional
from openai import OpenAI
from .config import API_BASE_URL, MODEL_NAME, API_KEY


class SQLErrorAnalyzer:
    """
    Intelligent SQL Execution Error Analyzer (General Enhanced Version)
    Combines 'Expert Rule Base' and 'LLM Deep Reasoning' to provide precise RAG retrieval keywords.
    """
    def __init__(self, target_db_type: str):
        self.target_db_type = target_db_type.lower()
        self.client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
        
        # === Expert Knowledge Base: Error Code -> Guidance Hints ===
        # Targets common stubborn errors in different databases to give LLM a clear reasoning direction.
        self.ERROR_HINT_MAP = {
            # Oracle
            "ORA-01861": "Hint: Literal does not match format string. Check: Are DATE/TIMESTAMP literals being compared to VARCHAR2 columns (implicit conversion failure)? Columns with undefined types in Schema might be strings.",
            "ORA-00904": "Hint: Invalid identifier. Check: 1. Does the column name exist? 2. Are aliases used (SELECT aliases cannot be used directly in WHERE)? 3. Does double-quoting cause case sensitivity?",
            "ORA-00979": "Hint: Not a GROUP BY expression. Rule: All non-aggregated columns in the SELECT list must appear in the GROUP BY clause.",
            "ORA-00933": "Hint: SQL command not properly ended. Check: Is ORDER BY in the correct position? Are ANSI JOIN and comma JOIN mixed?",
            
            # MySQL
            "1054": "Hint: Unknown column. Check column spelling. Note: In some MySQL versions, the WHERE clause cannot recognize aliases from the SELECT clause.",
            "1064": "Hint: Syntax error. Check reserved keywords (e.g., RANK, LEAD), or usage of window functions not supported in the current version.",
            "1055": "Hint: GROUP BY aggregation error (only_full_group_by). Selected columns must be in GROUP BY or use ANY_VALUE().",
            
            # Generic
            "generic_type": "Hint: Data type mismatch. Check if strings and numbers/dates are being compared without explicit conversion."
        }

    def analyze_error(
        self,
        sql: str,
        error_msg: str,
        true_tc_str: Optional[str] = None,
        nl2_rewrite: Optional[str] = None,
        question: Optional[str] = None
    ) -> Dict:
        """Execute intelligent analysis"""
        start_time = time.time()
        
        # 1. Extract error features
        error_code = self._extract_error_code(error_msg)
        specific_hint = self.ERROR_HINT_MAP.get(error_code, "")
        
        # 2. If no specific Hint, but contains words like "type" or "convert", give generic hint
        if not specific_hint and ("type" in error_msg.lower() or "convers" in error_msg.lower()):
            specific_hint = self.ERROR_HINT_MAP["generic_type"]

        # 3. LLM Deep Reasoning
        analysis_data = self._call_llm_analysis(
            sql, error_msg, true_tc_str, nl2_rewrite, question, specific_hint
        )
        
        # 4. Result encapsulation
        result = {
            "error_code": error_code,
            "error_type": f"{self.target_db_type}_{error_code}" if error_code else "unknown",
            "inferred_reason": analysis_data.get("reason", error_msg),
            "suggested_keywords": analysis_data.get("keywords", []),
            "raw_error": error_msg,
            "latency": round(time.time() - start_time, 2)
        }
        return result

    def _extract_error_code(self, error_msg: str) -> Optional[str]:
        """Extract standard error code"""
        error_msg = error_msg.upper()
        if "ORA-" in error_msg:
            match = re.search(r'ORA-\d+', error_msg)
            return match.group(0) if match else None
        if "ERROR" in error_msg and ("MYSQL" in self.target_db_type.upper() or "MARIADB" in self.target_db_type.upper()):
            match = re.search(r'ERROR\s+(\d+)', error_msg)
            return match.group(1) if match else None
        return None

    def _call_llm_analysis(self, sql, error_msg, schema, logic, question, hint) -> Dict:
        """Build Prompt and call LLM"""
        
        schema_info = f"Schema (Column Names Only): {schema}" if schema else "Schema: Unknown"
        if schema:
            schema_info += "\n   (Note: If the error suggests type issues, please infer if certain columns are actually VARCHAR or other types, regardless of the name)"

        prompt = f"""
You are a {self.target_db_type} database kernel expert. Please diagnose the following SQL failure.

【Context】
User Question: {question}
Logical Intent: {logic}
{schema_info}
Error SQL: {sql}
Original Error: {error_msg}

{f"【Expert Hint】: {hint}" if hint else ""}

【Tasks】
1. **Root Cause**: Based on Schema and SQL syntax, analyze the deep-seated cause of the error (e.g., implicit conversion, dialect incompatibility, logical error).
2. **Retrieval Keywords**: Extract 3-5 keywords used to retrieve official documentation or knowledge bases.
   - Must include specific database terminology (e.g., "Implicit Conversion", "Window Function", "CTE").

【Output Format】
Return JSON only, no Markdown:
{{
    "reason": "Short one-sentence reason (<100 characters)",
    "keywords": ["keyword1", "keyword2", "keyword3"]
}}
"""
        try:
            resp = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            content = resp.choices[0].message.content.strip()
            # Clean potential Markdown markers
            if content.startswith("```"): 
                content = content.replace("```json", "").replace("```", "")
            return json.loads(content)
        except Exception as e:
            print(f"   ⚠️ [Analyzer] LLM Analysis Exception: {e}")
            return {"reason": error_msg, "keywords": []}

def get_error_analyzer(target_db_type: str) -> SQLErrorAnalyzer:
    return SQLErrorAnalyzer(target_db_type)