import re
from api_client import call_modelscope_api_single
from db_operations import test_sql_execution
from rag_retrieval import save_magic_guideline
# 导入 schema 纠错工具（确保路径正确）
from schema_corrector import correct_sql_schema


class MagicAdapter:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def clean_sql(self, text: str) -> str:
        """从 LLM 输出中提取 SQL"""
        match = re.search(r"```sql\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        match_generic = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match_generic:
            return match_generic.group(1).strip()
        return text.strip().replace("```", "").replace("sql", "")

    def propose_syntax_fix(self, question, dialect, incorrect_sql, error_msg, nl2_rewrite, iteration=1):
        """Magic Step A: 生成语法修正建议（带迭代上下文）"""
        iteration_hint = f"\nThis is your iteration {iteration} attempt. Previous fix still failed." if iteration > 1 else ""

        prompt = f"""
You are a {dialect} SQL Expert.
The following SQL failed to execute.{iteration_hint}

**Context**:
- Question: {question}
- Schema & Requirements: 
{nl2_rewrite}

- Incorrect SQL: {incorrect_sql}
- Error Message: {error_msg}

**Task**:
Analyze the error. Identify specific syntax or dialect-specific misuse (e.g., reserved keywords, date formats, or join types).
Provide a "Syntax Correction Rule" to fix this.
Do NOT write the full SQL. Just explain the logic.
"""
        try:
            return call_modelscope_api_single(prompt, dialect)
        except Exception:
            return "Ensure standard SQL syntax and check for reserved keywords."

    def fix_sql_with_rule(self, question, dialect, incorrect_sql, rule, nl2_rewrite):
        """Magic Step B: 根据规则修复 SQL"""
        prompt = f"""
You are a {dialect} SQL Expert.

**Schema & Requirements**:
{nl2_rewrite}

**Task**:
Fix the following SQL based on the provided Syntax Rule.

- Question: {question}
- Incorrect SQL: {incorrect_sql}
- **Mandatory Syntax Rule**: {rule}

Output ONLY the corrected SQL wrapped in ```sql ... ```.
Ensure the SQL ends with a semicolon.
"""
        response = call_modelscope_api_single(prompt, dialect)
        return self.clean_sql(response)

    def generate_structured_guideline(self, case):
        """Magic Step D: 生成结构化指南"""
        prompt = f"""
Analyze the correction case and extract a generic rule for future use.
Format: @homy@ <Category> <Sub-category> 1. Scenarios 2. Function -- {case.get('dialect')} - Correct/Incorrect/Reason @homy@
Case Info:
- Error: {case.get('error_msg')}
- Correct SQL: {case.get('corrected_sql')}
"""
        response = call_modelscope_api_single(prompt, case.get('dialect'))
        return response.strip() if "@homy@" in response else ""

    def run_magic_fix(self, question, nl2_rewrite, incorrect_sql, error_msg, dialect, true_tc_str=None, logger=None,
                      max_retries=2):
        """
        [增强版] 迭代式 Magic 修复流程
        """
        current_sql = incorrect_sql
        current_error = error_msg

        for attempt in range(1, max_retries + 1):
            print(f"\n🔮 [Magic Module] 第 {attempt} 次修复尝试...")

            # 1. 提出修正建议
            syntax_rule = self.propose_syntax_fix(question, dialect, current_sql, current_error, nl2_rewrite,
                                                  iteration=attempt)
            print(f"🔮 [Magic] 诊断建议: {syntax_rule[:100]}...")

            # 2. 生成修复 SQL
            fixed_sql = self.fix_sql_with_rule(question, dialect, current_sql, syntax_rule, nl2_rewrite)

            # [核心] 集成 Schema 纠错
            if true_tc_str:
                fixed_sql = correct_sql_schema(fixed_sql, true_tc_str)

            # [记录日志]
            if logger:
                logger.log_magic_fix(f"Attempt {attempt}: {syntax_rule}", fixed_sql)

            # 3. 验证执行
            # 简单清洗末尾符号防止报错
            sql_for_run = fixed_sql.strip().rstrip(';').rstrip('/')
            exec_result = test_sql_execution(sql_for_run, dialect, self.db_connection)

            if exec_result["status"] == "success":
                print(f"✨ [Magic] 第 {attempt} 次修复成功!")

                # 4. 成功后生成指南
                case_info = {
                    "dialect": dialect, "question": question,
                    "incorrect_sql": incorrect_sql, "error_msg": error_msg,
                    "corrected_sql": fixed_sql, "syntax_rule": syntax_rule
                }
                guideline = self.generate_structured_guideline(case_info)
                if guideline:
                    save_magic_guideline(guideline, nl2_rewrite, dialect)

                return "success", fixed_sql
            else:
                print(f"❌ [Magic] 第 {attempt} 次修复失败: {exec_result['error'][:100]}")
                # 更新当前状态进入下一轮迭代
                current_sql = fixed_sql
                current_error = exec_result["error"]

        return "failed", current_sql