import json
import re
import os
from typing import Dict, List, Any, Optional

# Import db_utils and schema_utils
from magic.db_utils import get_db_engine, execute_query, SQLITE_DB_ROOT_PATH
from magic.schema_utils import get_full_schema_context

class BaseAgent:
    def __init__(self, llm_service):
        self.llm = llm_service

    def clean_sql(self, text: str) -> str:
        """Extract SQL from markdown code blocks"""
        match = re.search(r"```sql(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip()

    def extract_json(self, text: str) -> Any:
        """Robustly extract and parse JSON from text."""
        try:
            # If the text is pure JSON already
            return json.loads(text)
        except json.JSONDecodeError:
            pass
            
        # Pattern 1: ```json ... ```
        pattern = r"```json\s*(\{.*?\})\s*```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Pattern 2: ``` ... ``` (no lang tag)
        pattern = r"```\s*(\{.*?\})\s*```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Pattern 3: Find outermost {}
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass
                
        # Failed to parse
        raise ValueError("Could not extract valid JSON from response")

class SuccessAnalysisAgent(BaseAgent):
    def analyze(self, question: str, dialect_sqls: Dict[str, str]) -> Dict[str, Any]:
        # Prepare the list of available dialects
        available_dialects = []
        sqls_text = ""
        for dialect in ['sqlite', 'mysql', 'postgres']:
            if dialect in dialect_sqls:
                available_dialects.append(dialect)
                sqls_text += f"- {dialect.capitalize()}: {dialect_sqls[dialect]}\n"
        
        prompt = f"""
You are a Cross-Dialect SQL Expert.
Question: "{question}"

You have been provided with correct SQL queries for the same question in the following dialects: {', '.join(available_dialects)}.

Correct SQL Implementations:
{sqls_text}

Your Task: 
1. Compare the provided queries.
2. Identify any syntactic or functional differences between these specific dialects.
3. If they are identical, state that.
4. If there ARE differences, formulate a concise "Dialect Translation Rule" that explains the difference.
    Focus on FUNCTION names, OPERATORS, and SYNTAX (e.g. quoting, date handling). IGNORE alias naming differences.

Output Format:
Return a JSON object:
{{
    "has_differences": boolean,
    "observation": "A brief summary of the difference.",
    "guideline": "A generalized rule (e.g., 'SQLite uses X while MySQL uses Y')."
}}
Ensure the output is valid JSON.
"""
        response = self.llm.generate_response(prompt)
        try:
            return self.extract_json(response)
        except:
            return {"error": "Failed to parse JSON", "raw_response": response}

class FeedbackAgent(BaseAgent):
    def generate_feedback(self, question: str, target_dialect: str, incorrect_sql: str, error_msg: str, correct_sibling_sqls: Dict[str, str], schema_context: str) -> str:
        
        siblings_context = ""
        if correct_sibling_sqls:
            siblings_context = "Reference (Correct implementations in other dialects):\n"
            for d, sql in correct_sibling_sqls.items():
                siblings_context += f"- {d}: {sql}\n"

        prompt = f"""
You are a SQL Debugging Expert specialized in {target_dialect}.

Database Schema:
{schema_context}

Question: "{question}"

Incorrect {target_dialect} SQL:
```sql
{incorrect_sql}
```

Execution Error / Result Mismatch:
{error_msg}

{siblings_context}

Your Task: Analyze the error and provide specific feedback to fix the {target_dialect} query.
"""
        return self.llm.generate_response(prompt)

class CorrectionAgent(BaseAgent):
    def fix_sql(self, question: str, target_dialect: str, incorrect_sql: str, feedback: str, schema_context: str, guideline_text: str = "", has_sibling_context: bool = False) -> str:
        
        guideline_context = ""
        if guideline_text:
            guideline_context = f"Relevant Correction Guidelines (Learned from previous mistakes):\n{guideline_text}\n"
        
        # Base In-Context Learning Example (General Logic Check - Always Included)
        base_example = """
## Example 1: General Logic Check
Query: SELECT COUNT(*) FROM major WHERE college = "College of Humanities and Social Sciences"
1. **Did I use the correct table for the query?**
   - Yes, the `major` table contains the `college` column which is necessary for filtering the majors based on the college name.

2. **Did I correctly specify the column to count?**
   - Yes, using `COUNT(*)` is appropriate here since we are interested in the total number of majors in the specified college, not a specific column.

3. **Did I use the correct filtering condition?**
   - I need to ensure that the filtering condition accurately matches the college name as specified in the question. The use of double quotes for string literals in SQL might be incorrect depending on the SQL dialect. Some SQL dialects prefer single quotes for string literals.

4. **Did I unnecessarily use `DISTINCT`?**
   - No, `DISTINCT` is not used in the initial query, which is correct because we want to count all majors, not just unique ones.

5. **Have I ensured that my conditions accurately target the required data without adding unnecessary complexity?**
   - The condition seems straightforward and targets the required data accurately by filtering majors based on the college name.

6. **Did I use the correct syntax for string literals?**
   - The initial query used double quotes for the string literal, which might not be correct for all SQL dialects. It's safer to use single quotes for string literals.

Revised SQL:
```sql
SELECT COUNT(*) FROM major WHERE college = 'College of Humanities and Social Sciences'
```
"""

        # Dialect-Specific Example (Included ONLY if sibling context is available)
        dialect_example = ""
        if has_sibling_context:
            dialect_example = """
## Example 2: Dialect-Specific Correction (Using Feedback)
Target Dialect: MySQL
Question: "Show the year of the first review."
Incorrect SQL: SELECT strftime('%Y', review_date) FROM reviews ORDER BY review_date LIMIT 1

Feedback from Expert: 
The function `strftime` is specific to SQLite and does not exist in MySQL. For MySQL, you should use `YEAR(date_column)` or `DATE_FORMAT(date_column, '%Y')` to extract the year.

1. **Did I use the correct function for the dialect?**
   - No. As the feedback pointed out, `strftime` is for SQLite. I am writing for MySQL. I should replace `strftime('%Y', review_date)` with `YEAR(review_date)`.

2. **Did I follow the feedback regarding syntax?**
   - Yes, the feedback explicitly mentioned the dialect mismatch. I will apply the MySQL-specific function.

Revised SQL:
```sql
SELECT YEAR(review_date) FROM reviews ORDER BY review_date LIMIT 1
```
"""
        
        cot_example = base_example + dialect_example + "\n##\n"

        prompt = f"""
You are a {target_dialect} Expert.

Database Schema:
{schema_context}

{cot_example}

Current Task:
Question: "{question}"

The following SQL was incorrect:
```sql
{incorrect_sql}
```

Feedback from Expert:
{feedback}

{guideline_context}

Please generate the Corrected SQL for {target_dialect}.
Follow the "Asking myself" step-by-step reasoning process as shown in the example above before writing the final SQL.

Output ONLY the SQL code wrapped in ```sql ... ```.
"""
        response = self.llm.generate_response(prompt)
        return self.clean_sql(response)

class ManagerAgent(BaseAgent):
    def __init__(self, llm_service, guideline_manager=None, enable_success_analysis: bool = False, max_retries: int = 3):
        super().__init__(llm_service)
        self.feedback_agent = FeedbackAgent(llm_service)
        self.correction_agent = CorrectionAgent(llm_service)
        self.success_agent = SuccessAnalysisAgent(llm_service)
        
        self.guideline_manager = guideline_manager
        self.enable_success_analysis = enable_success_analysis
        self.max_retries = max_retries

    def evaluate_sql(self, dialect, db_id, pred_sql, ground_truth_sql):
        engine = get_db_engine(dialect, db_id)
        if not engine: return False, False, "Database Connection Failed"
        
        is_exec, pred_res = execute_query(engine, pred_sql)
        if not is_exec: return False, False, f"Execution Error: {pred_res}"
            
        _, gt_res = execute_query(engine, ground_truth_sql)
        
        # Strict Order Check if GT contains 'ORDER BY'
        # We assume pred_res and gt_res are lists of tuples (result sets)
        is_correct = False
        if "order by" in ground_truth_sql.lower():
             is_correct = (pred_res == gt_res) # List comparison (Order sensitive)
        else:
             # Set comparison (Order insensitive)
             try:
                 is_correct = (set(pred_res) == set(gt_res))
             except:
                 # Fallback to list comparison if unhashable
                 is_correct = (pred_res == gt_res)
                 
        return True, is_correct, "Success" if is_correct else "Result Mismatch"

    def run(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        question = entry.get("question")
        db_id = entry.get("db_id")
        
        # Load Schema Context
        schema_context = get_full_schema_context(SQLITE_DB_ROOT_PATH, db_id)

        # 1. Initial Evaluation
        eval_results = {}
        current_sqls = {} 
        correct_sqls = {} 

        for dialect in ["sqlite", "mysql", "postgres"]:
            if dialect not in entry["model_generations"]: continue
            pred_sql = entry["model_generations"][dialect]["Answer"]
            gt_sql = entry["ground_truth"][dialect]
            
            is_exec, is_correct, msg = self.evaluate_sql(dialect, db_id, pred_sql, gt_sql)
            
            eval_results[dialect] = {"exec": is_exec, "correct": is_correct, "msg": msg}
            current_sqls[dialect] = pred_sql
            if is_correct: correct_sqls[dialect] = pred_sql

        trajectory = {
            "question": question,
            "db_id": db_id,
            "initial_status": {},
            "steps": [],
            "final_status": {}
        }

        # 2. Correction Loop 
        for dialect, status in eval_results.items():
            # Record initial status (now contains both exec and correct)
            trajectory["initial_status"][dialect] = {"exec": status["exec"], "correct": status["correct"]}
            
            if status["correct"]:
                trajectory["final_status"][dialect] = {"exec": True, "correct": True}
                continue
                
            print(f"[{db_id}] Fixing {dialect}...")
            
            is_eventually_fixed = False
            final_exec_status = status["exec"] # Track if it becomes executable even if wrong result

            for attempt in range(self.max_retries):
                incorrect_sql = current_sqls[dialect]
                error_msg = status["msg"]
                
                # Get latest guidelines (Online Rolling Update!)
                current_guidelines = ""
                if self.guideline_manager:
                    current_guidelines = self.guideline_manager.get_current_guidelines()

                # Pass currently known correct siblings to help fix this one
                feedback = self.feedback_agent.generate_feedback(
                    question, dialect, incorrect_sql, error_msg, correct_sqls, schema_context
                )
                
                # Check if we have siblings (cross-dialect references) available
                has_siblings = len(correct_sqls) > 0
                
                corrected_sql = self.correction_agent.fix_sql(
                    question, dialect, incorrect_sql, feedback, schema_context, current_guidelines, has_sibling_context=has_siblings
                )
                
                is_exec, is_fixed, new_msg = self.evaluate_sql(dialect, db_id, corrected_sql, entry["ground_truth"][dialect])
                
                # Update tracking
                final_exec_status = is_exec
                
                step_record = {
                    "dialect": dialect,
                    "attempt": attempt + 1,
                    "incorrect_sql": incorrect_sql,
                    "feedback": feedback,
                    "corrected_sql": corrected_sql,
                    "result": new_msg,
                    "success": is_fixed,
                    "executable": is_exec
                }
                trajectory["steps"].append(step_record)
                current_sqls[dialect] = corrected_sql
                status["msg"] = new_msg
                status["exec"] = is_exec
                
                if is_fixed:
                    print(f"[{db_id}] Fixed {dialect} on attempt {attempt+1}")
                    status["correct"] = True
                    correct_sqls[dialect] = corrected_sql 
                    is_eventually_fixed = True
                    
                    # Report correction success (Type A Evidence)
                    if self.guideline_manager:
                        self.guideline_manager.add_success_case({
                            "question": question,
                            "incorrect_sql": incorrect_sql,
                            "feedback": feedback,
                            "corrected_sql": corrected_sql
                        })
                        
                    break
            
            trajectory["final_status"][dialect] = {"exec": final_exec_status, "correct": is_eventually_fixed}

        # 3. Success Analysis (Trigger if >= 2 correct dialects)
        if self.enable_success_analysis and len(correct_sqls) >= 2:
            print(f"[{db_id}] {len(correct_sqls)} Dialects Correct! Running Success Analysis...")
            analysis = self.success_agent.analyze(question, correct_sqls)
            trajectory["success_analysis"] = analysis
            
            # Report dialect observation (Type B Evidence)
            if self.guideline_manager and analysis.get("has_differences"):
                self.guideline_manager.add_observation(analysis)

        return trajectory
