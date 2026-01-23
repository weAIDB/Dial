# process_logger.py
import os
import datetime

class ProcessLogger:
    def __init__(self, output_dir):
        # [核心路径配置] 确保日志输出到指定目录下的 process_logs 子文件夹
        # 传入的 output_dir 应该是: C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\方言匹配\输出结果
        self.log_dir = os.path.join(output_dir, "process_logs")
        
        # 自动创建目录
        if not os.path.exists(self.log_dir):
            try:
                os.makedirs(self.log_dir)
            except Exception as e:
                print(f"⚠️ 创建日志目录失败: {e}")
        
        # 以时间戳命名日志文件
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.log_dir, f"run_log_{timestamp}.md")
        
        print(f"📝 日志文件路径: {self.log_file}")
        
        # 初始化文件头
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"# NL2SQL Execution Process Log\n")
            f.write(f"**Start Time:** {timestamp}\n")
            f.write(f"**Output Dir:** `{self.log_dir}`\n\n")
            f.write("---\n")

    def _write(self, content):
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(content + "\n")

    def start_question(self, index, question_id, db_id, question, nl2_rewrite):
        content = f"\n# 🟢 Question Process [Index: {index} | ID: {question_id}]\n"
        content += f"**Database:** `{db_id}`\n\n"
        content += f"**Original Question:**\n> {question}\n\n"
        content += f"**NL2SQL Rewrite (Schema Context):**\n> {nl2_rewrite}\n"
        content += "\n---"
        self._write(content)

    def log_phase(self, phase_name):
        self._write(f"\n## 🔹 Phase: {phase_name}")

    def log_llm_response(self, response_content):
        self._write(f"\n### 🤖 LLM Raw Response")
        if len(response_content) > 500000:
            response_content = response_content[:500000] + "\n...[Output Truncated]..."
        self._write(f"```text\n{response_content}\n```")

    def log_prompt(self, prompt_type, prompt_content):
        self._write(f"\n### 📝 Prompt Constructed ({prompt_type})")
        display_content = prompt_content[:300000] + "\n...[truncated]..." if len(prompt_content) > 300000 else prompt_content
        self._write(f"```markdown\n{display_content}\n```")

    # =========================================================================
    # [Requirement 1] 记录每一次检索到的知识库片段 (Functional & Rule-based)
    # =========================================================================
    def log_knowledge_retrieval(self, retrieval_results, target_db_type):
        """
        记录第一轮检索到的所有知识片段，包括 functional_dialect 和 rule_based_dialect
        """
        self._write(f"\n### 📖 Round 1: Knowledge Base Retrieval")
        
        if not retrieval_results:
            self._write("> *No knowledge retrieved.*")
            return

        # 1. 记录目标数据库的知识片段
        target_content = retrieval_results.get(target_db_type)
        if target_content:
            self._write(f"\n#### 🎯 Target Dialect Knowledge ({target_db_type})")
            # 简单的标记提示，帮助区分内容来源（假设内容中有关键词）
            if "Functional" in target_content or "Function" in target_content:
                 self._write("*(Detected: Functional Dialect Information)*")
            if "Rule" in target_content or "Syntax" in target_content:
                 self._write("*(Detected: Rule-based Dialect Information)*")
                 
            self._write(f"```text\n{target_content.strip()}\n```")
        else:
             self._write(f"\n#### 🎯 Target Dialect ({target_db_type}): No specific knowledge retrieved.")
        
        # 2. 记录其他数据库的参考片段（可能包含通用的 Functional logic）
        found_other = False
        for db, content in retrieval_results.items():
            if db != target_db_type and content:
                if not found_other:
                    self._write(f"\n#### 📎 Other Dialect References")
                    found_other = True
                self._write(f"**{db}:**")
                self._write(f"```text\n{content.strip()[:800]} ... (truncated)\n```")

    # =========================================================================
    # [Requirement 2] 记录第二轮反馈生成的语法片段和修改
    # =========================================================================
    def log_syntax_refinement(self, error_msg, retrieved_guidance, new_sql):
        """
        记录第二轮：基于报错的RAG检索（语法片段）与生成的修正SQL
        """
        self._write(f"\n### 🔧 Round 2: Syntax Correction (Feedback Loop)")
        
        # 1. 记录发生的错误
        self._write(f"\n**1. Detected Execution Error:**")
        self._write(f"> ❌ `{error_msg}`")
        
        # 2. 记录二次检索出的语法片段 (Rule-based correction)
        self._write(f"\n**2. Retrieved Syntax Guidance (Secondary RAG):**")
        if retrieved_guidance:
            self._write(f"```text\n{retrieved_guidance.strip()}\n```")
        else:
            self._write("> *No specific syntax guidance retrieved.*")
        
        # 3. 记录生成的 SQL
        self._write(f"\n**3. Refined SQL:**")
        self._write(f"```sql\n{new_sql}\n```")

    # =========================================================================
    # [Magic Module] 记录 Magic 模块生成的语法规则
    # =========================================================================
    def log_magic_fix(self, syntax_rule, fixed_sql):
        self._write(f"\n### 🔮 Magic Module Intervention")
        self._write(f"\n**1. AI-Generated Syntax Rule:**")
        self._write(f"> 🧠 {syntax_rule}")
        self._write(f"\n**2. Magic Fixed SQL:**")
        self._write(f"```sql\n{fixed_sql}\n```")

    # =========================================================================
    # [Requirement 3] 记录第三轮反馈（逻辑修正）生成的片段和修改
    # =========================================================================
    def log_logic_refinement(self, fail_reason, logic_fix_sql):
        """
        记录第三轮：基于语义校验的逻辑修正
        """
        self._write(f"\n### 🧠 Round 3: Logic & Semantic Correction")
        
        # 1. 记录校验失败原因
        self._write(f"\n**1. Semantic Verification Failure:**")
        self._write(f"> ⚠️ {fail_reason}")
        
        # 2. 记录生成的逻辑修正SQL
        self._write(f"\n**2. Logic Refined SQL:**")
        self._write(f"```sql\n{logic_fix_sql}\n```")

    def log_sql_execution(self, sql, status, error_msg=None):
        self._write(f"\n### ⚙️ SQL Execution Check")
        self._write(f"- **SQL:** `{sql}`")
        if status == "success":
            self._write(f"- **Status:** ✅ SUCCESS")
        else:
            self._write(f"- **Status:** ❌ FAILED")
            self._write(f"- **Error:** `{error_msg}`")

    def log_semantic_check(self, is_pass, reason):
        self._write(f"\n### 🛡️ Semantic Verification Result")
        if is_pass:
            self._write(f"- **Result:** ✅ PASS")
        else:
            self._write(f"- **Result:** ⚠️ FAIL")
            self._write(f"- **Reason:** {reason}")

    def end_question(self, final_status):
        self._write(f"\n**🏁 Final Status:** {final_status}")
        self._write("\n---\n")