# magic_adapter.py
import re
import textwrap
from api_client import call_modelscope_api_single
from db_operations import test_sql_execution
from rag_retrieval import save_magic_guideline

class MagicAdapter:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def clean_sql(self, text: str) -> str:
        """从 LLM 输出中提取 SQL"""
        # 优先匹配 markdown sql
        match = re.search(r"```sql\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        # 其次匹配 markdown (无sql标记)
        match_generic = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match_generic:
            return match_generic.group(1).strip()
        
        return text.strip().replace("```", "").replace("sql", "")

    def propose_syntax_fix(self, question, dialect, incorrect_sql, error_msg, nl2_rewrite):
        """
        Magic Step A: 生成语法修正规则
        [Correction] 增加了 nl2_rewrite 作为 Schema 上下文，对应原 agent 中的 schema 参数
        """
        prompt = f"""
You are a {dialect} SQL Expert.
The following SQL failed to execute.

**Context**:
- Question: {question}
- Schema & Requirements: 
{nl2_rewrite}

- Incorrect SQL: {incorrect_sql}
- Error Message: {error_msg}

**Task**:
Analyze the error. Identify the specific syntax or function misuse.
Provide a specific "Syntax Correction Rule" to fix this. 
Do NOT write the full SQL yet. Just explain the rule in natural language.

**Output**:
A concise rule description.
"""
        try:
            return call_modelscope_api_single(prompt, dialect)
        except Exception as e:
            print(f"Magic Syntax Rule Gen Error: {e}")
            return "Ensure standard SQL syntax is used."

    def fix_sql_with_rule(self, question, dialect, incorrect_sql, rule, nl2_rewrite):
        """
        Magic Step B: 根据规则修复 SQL
        [Correction] 增加了 nl2_rewrite 作为 Schema 上下文
        """
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
        """Magic Step D: 生成结构化指南 (保持原样，逻辑一致)"""
        prompt = f"""
Analyze the following SQL correction case and extract a syntax rule.
Case:
- Dialect: {case.get('dialect')}
- Question: {case.get('question')}
- Mistake: {case.get('incorrect_sql')}
- Error: {case.get('error_msg')}
- Fix: {case.get('corrected_sql')}

Format Output EXACTLY as follows (start/end with @homy@):

@homy@
<Category ID & Name>

<Sub-category>:
   1. Common Scenarios:
      <Description>
   2. Function Description:
      <Description>

    -- {case.get('dialect')}
       - Correct: {case.get('corrected_sql')}
       - Incorrect: {case.get('incorrect_sql')}
       - Reason: <Reason>
@homy@

Output ONLY the text.
"""
        response = call_modelscope_api_single(prompt, case.get('dialect'))
        # 简单的清洗逻辑
        if "@homy@" in response:
            return response.replace("```text", "").replace("```", "").strip()
        # 如果模型没输出 @homy@，尝试直接返回内容（容错）
        return response.strip()

    # 修改 run_magic_fix 方法签名，增加 logger 参数
    def run_magic_fix(self, question, nl2_rewrite, incorrect_sql, error_msg, dialect, logger=None):
        """
        执行 Magic 修复流程
        """
        print(f"\n🔮 [Magic Module] 启动! 正在尝试修复 {dialect} SQL...")
        
        # 1. 提出语法修正建议
        syntax_rule = self.propose_syntax_fix(question, dialect, incorrect_sql, error_msg, nl2_rewrite)
        print(f"🔮 [Magic] 生成修正规则: {syntax_rule[:100]}...")

        # 2. 根据规则修复 SQL
        fixed_sql = self.fix_sql_with_rule(question, dialect, incorrect_sql, syntax_rule, nl2_rewrite)
        print(f"🔮 [Magic] 修复后的 SQL: {fixed_sql[:100]}...")

        # [新增] 记录日志
        if logger:
            logger.log_magic_fix(syntax_rule, fixed_sql)

        # 3. 验证执行 (后续代码保持不变...)
        exec_result = test_sql_execution(fixed_sql, dialect, self.db_connection)

        if exec_result["status"] == "success":
            print(f"🔮 [Magic] 修复成功! SQL 可执行。")
            
            # 4. 生成并保存指南
            case_info = {
                "dialect": dialect,
                "question": question,
                "incorrect_sql": incorrect_sql,
                "error_msg": error_msg,
                "corrected_sql": fixed_sql,
                "syntax_rule": syntax_rule
            }
            try:
                guideline_text = self.generate_structured_guideline(case_info)
                if guideline_text:
                    print(f"🔮 [Magic] 生成指南，正在进行分类存储...")
                    # 传入 nl2_rewrite 用于计算相似度
                    save_magic_guideline(guideline_text, nl2_rewrite, dialect)
            except Exception as e:
                print(f"⚠️ [Magic] 指南保存失败: {e}")
            
            return "success", fixed_sql
        else:
            print(f"🔮 [Magic] 修复后执行依旧失败: {exec_result['error'][:100]}...")
            return "failed", fixed_sql