import json
import os
from threading import Lock
from typing import List, Dict

class GuidelineManager:
    def __init__(self, llm_service, output_path: str):
        self.llm = llm_service
        self.output_path = output_path
        
        # Current guideline state
        self.current_guidelines = ""
        
        # Buffers
        self.correction_buffer: List[str] = []
        self.observation_buffer: List[str] = []
        self.buffer_size_limit = 10
        
        self.lock = Lock()
        
        # Load existing guidelines
        if os.path.exists(output_path):
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    self.current_guidelines = f.read()
            except Exception as e:
                print(f"Error loading existing guidelines: {e}")

    def get_current_guidelines(self) -> str:
        with self.lock:
            return self.current_guidelines

    def _generalize_case(self, case: Dict) -> str:
        """Uses an LLM call to convert a specific correction case into a general rule."""
        prompt = f"""
Analyze the following SQL correction case.
Extract the single, underlying, generic SQL syntax or function principle that caused the error.

**CRITICAL RULE**: Do NOT mention specific table names (e.g., 'reviews'), column names (e.g., 'review_date'), or data values (e.g., 'Al-Qaeda', '2023'). Focus ONLY on the abstract principle.

**Case Details:**
- Question: {case['question']}
- Mistake: {case['incorrect_sql']}
- Fix: {case['corrected_sql']}

**Example 1:**
- Input: Mistake: `SELECT * FROM users WHERE name = "John"`. Fix: `... name = 'John'`
- Output: In SQL, string literals should be enclosed in single quotes (''), not double quotes ("").

**Example 2:**
- Input: Mistake: `SELECT strftime('%Y', review_date) ...`. Fix: `SELECT YEAR(review_date) ...` for MySQL.
- Output: To extract the year from a date, use `YEAR(date_column)` in MySQL, not the SQLite-specific function `strftime('%Y', ...)`.

**Example 3:**
- Input: Mistake: `SELECT ... GROUP BY name`. Fix: `SELECT ... GROUP BY name, id` in MySQL.
- Output: In MySQL with ONLY_FULL_GROUP_BY mode, all non-aggregated columns in the SELECT list must also appear in the GROUP BY clause.

Output ONLY the single, abstract rule.
"""
        try:
            abstract_rule = self.llm.generate_response(prompt)
            # Basic validation to ensure the response is a rule, not an error or empty.
            if abstract_rule and len(abstract_rule) > 15 and 'rule' not in abstract_rule.lower() and 'output' not in abstract_rule.lower():
                return abstract_rule.strip()
            else:
                return ""
        except Exception:
            return ""

    def add_success_case(self, case: Dict):
        """Generalizes a success case into an abstract rule before adding to buffer."""
        # First, generalize the case into an abstract rule.
        abstract_rule = self._generalize_case(case)
        
        if abstract_rule:
            with self.lock:
                # Now, only the clean, abstract rule is added to the buffer.
                formatted_rule = f"[General Rule from Correction]: {abstract_rule}"
                self.correction_buffer.append(formatted_rule)
                self._check_and_update()

    def add_observation(self, analysis: Dict):
        """Add a dialect observation (Comparison Rule)."""
        with self.lock:
            if not analysis.get("has_differences"):
                return
                
            formatted = f"""
[Dialect Observation]
Observation: {analysis.get('observation')}
Rule: {analysis.get('guideline')}
"""
            self.observation_buffer.append(formatted)
            self._check_and_update()

    def _check_and_update(self):
        """Check if total evidence exceeds limit."""
        total_evidence = len(self.correction_buffer) + len(self.observation_buffer)
        if total_evidence >= self.buffer_size_limit:
            print(f"Guideline Manager: Buffer full ({total_evidence} items). Updating guidelines...")
            self._update_guidelines_unsafe()

    def _update_guidelines_unsafe(self):
        """Internal LLM call to synthesize new guidelines."""
        
        evidence_text = "\n".join(self.correction_buffer + self.observation_buffer)
        
        prompt = f"""
You are a SQL Knowledge Engineer. Your task is to maintain and update a "Multi-Dialect SQL Cheatsheet".

# Current Cheatsheet:
{self.current_guidelines if self.current_guidelines else "(No cheatsheet exists yet.)"}

# New Rules (A list of generalized rules learned from recent events):
{evidence_text}

# YOUR TASK:
Merge the "New Rules" into the "Current Cheatsheet" to produce a single, clean, and perfectly structured document.

**CRITICAL GUIDELINES FOR WRITING**:
1.  **Cheatsheet Style**: Do NOT write a narrative or long paragraphs. Use bullet points, bold keywords, and `code snippets`.
2.  **Atomic & Actionable**: Every rule must be a small, actionable piece of advice.
3.  **No Business Logic**: IGNORE and REMOVE all specific business context (e.g., table/column names, specific data values like 'Al-Qaeda'). Focus ONLY on pure SQL syntax and function rules.
4.  **Enforce Structure**: The final output MUST strictly follow this exact Markdown structure. Do not deviate.

    ## 1. Dialect Rules
    ### <Category Name e.g., Date/Time Functions>
    - **<Functionality e.g., Year Extraction>**:
      - SQLite: `code_snippet`
      - MySQL: `code_snippet`
      - PostgreSQL: `code_snippet`

    ## 2. Common Pitfalls
    ### <Category Name e.g., Type Handling>
    - **<Specific Trap e.g., Text-to-Numeric Casting>**:
      - **PostgreSQL**: <Specific, actionable warning, e.g., Requires explicit casting `::numeric` for text columns before aggregation.>
      - **MySQL**: <Specific, actionable warning, e.g., Handles implicit casting automatically but can be slow.>
      - **SQLite**: <Specific, actionable warning, e.g., Requires `CAST(column AS REAL)` for math operations.>
      - *(Note: If a dialect has no specific pitfall for an item, it can be omitted or grouped, e.g., `- **MySQL/SQLite**: ...`)*

Return ONLY the complete, updated Markdown for the entire cheatsheet.

# Updated Cheatsheet:
"""
        try:
            new_guidelines = self.llm.generate_response(prompt)
            
            if new_guidelines and len(new_guidelines) > 10:
                self.current_guidelines = new_guidelines
                # Clear buffers
                self.correction_buffer = []
                self.observation_buffer = []
                
                with open(self.output_path, 'w', encoding='utf-8') as f:
                    f.write(self.current_guidelines)
                
                print("Guideline Manager: Guidelines updated and saved.")
            else:
                print("Guideline Manager: LLM returned invalid response. Skipping.")
                
        except Exception as e:
            print(f"Guideline Manager: Error updating guidelines: {e}")
