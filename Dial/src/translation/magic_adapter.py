# magic_adapter.py
import re
import json
import traceback
from .api_client import call_modelscope_api_single
from .db_operations import test_sql_execution
from .rag_retrieval import save_magic_guideline
from .schema_corrector import correct_sql_schema

class MagicAdapter:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def clean_sql(self, text: str) -> str:
        """Extract SQL from LLM output"""
        match = re.search(r"```sql\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match: return match.group(1).strip()
        match_generic = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match_generic: return match_generic.group(1).strip()
        return text.strip().replace("```", "").replace("sql", "")

    def _determine_knowledge_type(self, nl2_rewrite, error_msg, dialect):
        """
        [Step C] Determine if it is Functional (function usage) or Rule (syntax rule).
        Used to decide which repository to store in, and which @dialect2sql@ format to use.
        """
        prompt = f"""
        Analyze the following SQL generation scenario and classify the knowledge type required.
        
        **Requirement**: {nl2_rewrite}
        **Error**: {error_msg}
        **Dialect**: {dialect}
        
        **Task**: Classify into ONE category:
        1. "FUNCTIONAL": The issue is about how to use a specific function (e.g., SUBSTR, TO_DATE, REGEXP, JSON_EXTRACT) to achieve a data transformation described in the NL requirement.
        2. "RULE": The issue is about general SQL structure, JOIN logic, GROUP BY constraints, NULL handling, or dialect-specific clause limitations (e.g. LIMIT vs ROWNUM).
        
        Return ONLY the word "FUNCTIONAL" or "RULE".
        """
        try:
            response = call_modelscope_api_single(prompt, dialect).strip().upper()
            if "FUNCTIONAL" in response:
                return "FUNCTIONAL"
            return "RULE"
        except:
            return "RULE"

    def generate_structured_guideline(self, case_info, k_type):
        """
        [Step D] Generate specific format @dialect2sql@ guidelines based on type
        """
        dialect = case_info['dialect']
        
        if k_type == "FUNCTIONAL":
            # === Functional Library Format ===
            # Emphasize Scenarios and Function Description for NL similarity matching
            prompt = f"""
            Generate a knowledge entry for the **Functional Library**.
            
            **Context**:
            - Requirement: {case_info['nl2_rewrite']}
            - Correct SQL: {case_info['corrected_sql']}
            - Function Used: Identify the key function (e.g. SUBSTR, TO_DATE).
            
            **Output Format (Strictly wrap with @dialect2sql@)**:
            @dialect2sql@
            [Function Name] [Short Description]:
            1. Common Scenarios for Using This Syntax in Natural Language Queries:
               (List 3-5 abstract scenarios based on the requirement, e.g., "Partial extraction from date strings", "Handling strings with abnormal length")
            
            2. Relevant Function Description:
               (Describe how this function works in {dialect}, params, return types. e.g., "Supports extracting substring from start index...")
            
            -- {dialect}:
                Methods:
                (Detailed syntax explanation)
                Examples:
                (Provide 2 examples, including the one below)
                {case_info['corrected_sql']}
            @dialect2sql@
            """
        else:
            # === Rule Library Format ===
            # Emphasize Error Analysis and Correction Method for Error similarity matching
            prompt = f"""
            Generate a knowledge entry for the **Rule Library**.
            
            **Context**:
            - Error Message: {case_info['error_msg']}
            - Fix Strategy: {case_info['strategy']}
            - Correct SQL: {case_info['corrected_sql']}
            
            **Output Format (Strictly wrap with @dialect2sql@)**:
            @dialect2sql@
            [Rule Title] (e.g., NULL Handling in LEFT JOIN):
            -- {dialect}:
               Method:
                  (Explain the constraint or rule. Explain why the error happened: "{case_info['error_msg']}")
              eg:
                  (Provide the Correct SQL Example)
                  {case_info['corrected_sql']}
            @dialect2sql@
            """
            
        response = call_modelscope_api_single(prompt, dialect)
        match = re.search(r"@dialect2sql@(.*?)@dialect2sql@", response, re.DOTALL)
        if match:
            return f"@dialect2sql@{match.group(1)}@dialect2sql@"
        return ""

    def learn_from_success(self, case_info):
        """
        [Step E] Learning Module Entry Point
        """
        try:
            # 1. Classification
            k_type = self._determine_knowledge_type(
                case_info['nl2_rewrite'], 
                case_info['error_msg'], 
                case_info['dialect']
            )
            print(f"📚 [Magic Learning] Classified as: {k_type} Library")

            # 2. Generate formatted knowledge
            guideline = self.generate_structured_guideline(case_info, k_type)
            
            if guideline:
                # 3. Save (Pass k_type to save function to decide which folder to store in)
                # save_magic_guideline needs to support k_type parameter in rag_retrieval.py
                save_magic_guideline(guideline, case_info['nl2_rewrite'], case_info['dialect'], k_type=k_type)
                print(f"💾 [Magic Learning] Experience saved to {k_type} Library")
            else:
                print(f"⚠️ [Magic Learning] Failed to generate @dialect2sql@ format")

        except Exception as e:
            print(f"❌ [Magic Learning] Exception: {e}")
            traceback.print_exc()

    def analyze_root_cause_multiverse(self, question, dialect, current_sql, current_error, nl2_rewrite, iteration=1, original_sql=None, previous_failures=None):
        """
        [Multiverse Version] Root Cause Analysis and Multi-Strategy Generation
        """
        # --- 1. Build Prompt ---
        iteration_hint = ""
        if iteration > 1:
            failure_detail = ""
            if previous_failures:
                failure_summary = "\n".join([
                    f"- Strategy '{f['strategy']}' failed with error: {str(f['error'])[:100]}" 
                    for f in previous_failures
                ])
                failure_detail = f"\n**Previous strategies tried on this path**:\n{failure_summary}"
            
            iteration_hint = f"""
            ### ⚠️ WARNING: Attempt #{iteration}
            We are in an iterative repair loop. Previous attempts failed. 
            {failure_detail}
            Please ensure the new hypotheses are DIFFERENT from the ones listed above.
            """

        repair_history = ""
        if original_sql and original_sql != current_sql:
            repair_history = f"""
            ### 🔄 REPAIR HISTORY
            - **Initial Failed SQL**: {original_sql}
            - **Current Observation**: The SQL was modified to fix an earlier issue but now fails with a new error.
            """

        prompt = f"""
You are a senior {dialect} DBA expert.
The SQL execution failed. Provide repair strategies.

**Context**:
- Question: {question}
- Schema Logic: {nl2_rewrite}

{repair_history}

**Bug Report**:
- Current SQL: {current_sql}
- Error: {current_error}

{iteration_hint}

**Task**:
1. Locate the snippet triggering the error.
2. Propose **up to 3 distinct hypotheses** for why it failed.
3. For each hypothesis, provide a specific fix strategy.

**Output Format (JSON)**:
Return a strictly valid JSON list of objects.
[
  {{
    "snippet": "code_snippet_here",
    "reason": "Explain failure...",
    "fix_strategy": "Explain fix..."
  }}
]
"""
        try:
            response = call_modelscope_api_single(prompt, dialect)
            json_match = re.search(r"\[.*\]", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            else:
                return [{"snippet": "Unknown", "reason": "JSON Parse failed", "fix_strategy": "Check syntax manually"}]
        except Exception:
            return [{"snippet": "Unknown", "reason": "Exception", "fix_strategy": "Fix syntax standard"}]
    
    def fix_sql_with_strategy(self, dialect, incorrect_sql, strategy_obj, nl2_rewrite):
        """Generate SQL based on a single strategy"""
        prompt = f"""
You are a {dialect} SQL Expert.

**Incorrect SQL**:
{incorrect_sql}

**Diagnosis**:
- Broken Snippet: {strategy_obj.get('snippet')}
- Reason: {strategy_obj.get('reason')}

**Your Task**:
Apply ONLY this specific fix strategy:
👉 **{strategy_obj.get('fix_strategy')}**

Do not change other parts of the SQL.
Output ONLY the corrected SQL wrapped in ```sql ... ```.
"""
        response = call_modelscope_api_single(prompt, dialect)
        return self.clean_sql(response)

    def run_magic_fix(self, question, nl2_rewrite, incorrect_sql, error_msg, dialect, true_tc_str=None, logger=None, max_retries=2):
        """
        [Main Loop] Iterative + Independent Branch Exploration Repair Process
        """
        # Seed queue: (Current SQL, Current Error, Parent SQL, History of Failures)
        current_seeds = [(incorrect_sql, error_msg, None, [])]
        
        # Record the very original error, used for Rule Library indexing (Rule Library usually retrieves based on initial syntax errors)
        original_initial_error = error_msg 

        for attempt in range(1, max_retries + 1):
            print(f"\n🔮 [Magic Module] Evolution Round {attempt} (Active branches: {len(current_seeds)})...")
            next_generation_seeds = [] 

            for base_sql, base_error, parent_sql, failure_history in current_seeds:
                
                # 1. Analyze current branch
                strategies = self.analyze_root_cause_multiverse(
                    question, dialect, 
                    current_sql=base_sql, 
                    current_error=base_error, 
                    nl2_rewrite=nl2_rewrite, 
                    iteration=attempt, 
                    original_sql=parent_sql, 
                    previous_failures=failure_history
                )
                
                if not strategies: continue

                # 2. Try each strategy
                for idx, strat in enumerate(strategies):
                    print(f"    👉 Branch Strategy {idx+1}: {strat.get('fix_strategy')[:50]}...")
                    
                    candidate_sql = self.fix_sql_with_strategy(dialect, base_sql, strat, nl2_rewrite)
                    
                    if true_tc_str:
                        candidate_sql = correct_sql_schema(candidate_sql, true_tc_str)
                    
                    # 3. Execute
                    sql_for_run = candidate_sql.strip().rstrip(';').rstrip('/')
                    exec_result = test_sql_execution(sql_for_run, dialect, self.db_connection)
                    
                    if exec_result["status"] == "success":
                        print(f"✨ [Magic] Fix Successful!")
                        
                        if logger:
                            logger.log_magic_fix(f"Attempt {attempt} Success", candidate_sql)
                        
                        # 4. Success -> Trigger Learning Module
                        case_info = {
                            "dialect": dialect, 
                            "question": question,
                            "nl2_rewrite": nl2_rewrite, # Used for Functional Library similarity
                            "error_msg": original_initial_error, # Used for Rule Library similarity (use original error)
                            "strategy": strat.get('fix_strategy'), 
                            "corrected_sql": candidate_sql
                        }
                        self.learn_from_success(case_info)
                            
                        return "success", candidate_sql
                    
                    else:
                        # 5. Failure -> Add to next round seeds
                        new_err = str(exec_result['error'])
                        new_history = failure_history + [{
                            "strategy": strat.get('fix_strategy'),
                            "error": new_err
                        }]
                        next_generation_seeds.append((candidate_sql, new_err, base_sql, new_history))
                        print(f"      ❌ Failed: {new_err[:60]}...")

            if not next_generation_seeds:
                print("⚠️ [Magic] All evolution paths terminated")
                break
            
            # Keep only the top 5 most promising branches per round to prevent exponential explosion
            current_seeds = next_generation_seeds[:5] 

        return "failed", incorrect_sql