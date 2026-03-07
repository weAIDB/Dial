# error_analysis.py
import os
from openai import OpenAI
from .config import API_BASE_URL, MODEL_NAME, API_KEY


def analyze_sql_error(question: str, wrong_sql: str, error_msg: str, db_type: str, nl2_rewrite: str, true_tables_columns: str) -> str:
    """
    Use Qwen3-max combined with Schema and logical intent to analyze SQL errors.
    The goal is to generate a description containing 'root cause' and 'retrieval keywords' to hit specific solutions in the RAG knowledge base.
    """
    if not wrong_sql or not error_msg:
        return error_msg

    client = OpenAI(
        api_key=API_KEY,
        base_url=API_BASE_URL,
    )

    # Build a prompt with deeper reasoning capabilities
    prompt = f"""
You are a kernel-level {db_type} database expert.
Your task now is to diagnose a failed SQL execution and generate a precise **error analysis summary** for retrieving solutions in a knowledge base.

【Context Information】
1. **User Question**: {question}
2. **Logical Deduction (NL2SQL)**: {nl2_rewrite}
3. **True Schema (Tables.Columns)**: {true_tables_columns}
   *(Note: If the Schema only has column names without types, please infer possible data type mismatches based on the error message. For example, ORA-01861 usually implies a string column was mistakenly treated as a date column)*
4. **Wrong SQL**: {wrong_sql}
5. **Original Error**: {error_msg}

【Analysis Requirements】
Please think step by step:
1. **Compare SQL with Schema**: Check if fields in WHERE/JOIN conditions (like date, timestamp) conflict with common syntax usage.
2. **Interpret Error**: Interpret the error message based on {db_type} characteristics.
   - For example: If it is `ORA-01861` and the SQL uses `DATE 'yyyy-mm-dd'`, this often means the column in the database is actually of **VARCHAR2** type, and implicit conversion failed.
   - For example: If it is `invalid identifier`, check if a non-existent column was referenced or if aliases were used incorrectly.
3. **Generate Retrieval Keywords**: Extract keywords that can hit the knowledge base (e.g., "Implicit Conversion", "Data Type Mismatch", "Reserved Keyword").

【Output Format】
Directly return a plain text block in the following format (do not include other verbose text):
Error Essence: [One sentence summary, e.g., VARCHAR field was mistakenly compared as DATE type]
Technical Reason: [Detailed explanation, e.g., Field X might be in string format in the table, but SQL used a DATE literal, leading to implicit conversion failure]
Suggested Retrieval Keywords: [Key terms, separated by spaces]
"""

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {'role': 'system', 'content': 'You are a DB expert specialized in diagnosing SQL execution errors.'},
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.1, # Keep temperature low for stable output
            top_p=0.7
        )
        analysis_result = completion.choices[0].message.content.strip()
        print(f"   🧠 [Error Analysis] Deep diagnosis completed: {analysis_result[:100]}...")
        return analysis_result
    except Exception as e:
        print(f"   ⚠️ [Error Analysis] Analysis failed: {e}")
        return error_msg