# prompt_builder.py
import textwrap
from typing import Dict, Any, Optional
from .utils import truncate_content
from .config import SUPPORTED_DBS


def get_dialect_specific_warnings(db_type: str) -> str:
    """
    Get negative constraint warnings (pitfall guide) for specific databases
    """
    db_type_lower = db_type.lower()
    warnings = []

    if "oracle" in db_type_lower:
        warnings = [
            "1. 【Reserved Word Disaster】If Schema contains reserved word column names like `date`, `order`, `number`, `group`, `level`:",
            "   - Must be wrapped in double quotes in SQL and **MUST** be uppercase! E.g., `t.\"DATE\"` instead of `t.\"date\"`.",
            "   - Unless you are absolutely sure the table structure was created in lowercase, Oracle defaults to uppercase metadata.",
            "2. 【Strictly Prohibit LIMIT】Oracle does not support `LIMIT`! Must use `FETCH FIRST n ROWS ONLY` (12c+) or `ROWNUM`.",
            "3. 【Strictly Prohibit Alias AS for Tables】`FROM table t` is correct, `FROM table AS t` is wrong.",
            "4. 【Date Handling】Date literals must use `DATE 'YYYY-MM-DD'` or `TO_DATE`, strictly prohibiting direct string comparison.",
            "5. 【String Concatenation】Must use `||`, strictly prohibiting `CONCAT` (only two args) or `+`.",
            "6. 【LISTAGG Limitation】Prioritize logical correctness; if content is too long, Oracle might error, but no excessive defense is needed."
        ]
    elif "sql server" in db_type_lower:
        warnings = [
            "1. 【Reserved Words】If column names are `date` or `user` etc., please wrap in square brackets, e.g., `[date]`.",
            "2. 【Strictly Prohibit LIMIT】Must use `SELECT TOP n ...`.",
            "3. 【String Concatenation】Must use `+`."
        ]
    elif "sqlite" in db_type_lower:
        warnings = [
            "1. 【Join Limitation】Only supports `LEFT JOIN`, strictly prohibiting `RIGHT/FULL JOIN`.",
            "2. 【Date】Use `strftime` to handle string dates."
        ]
    elif "postgresql" in db_type_lower:
        warnings = [
            "1. 【Quotes】Strings use single quotes `'`, identifiers use double quotes `\"`.",
            "2. 【Fuzzy Match】Case-insensitive use `ILIKE`."
        ]
    elif "mysql" in db_type_lower:
        warnings = [
            "1. 【Identifiers】Use backticks `` ` ``.",
            "2. 【Concatenation】Use `CONCAT()`."
        ]

    if warnings:
        return "\n   ".join(warnings)
    return "Follow standard SQL syntax."


def build_prompt(
        retrieval_item: Dict[str, Any],
        target_db_type: str,
        db_rule_content: Optional[str] = None,
        secondary_rag_content: Optional[str] = None,
        error_msg: Optional[str] = None,
        first_sql: Optional[str] = None
) -> str:
    """
    Construct Prompt
    Core Optimization: Introduce "Hybrid Constraint Mechanism" to solve ID=29 (Table prefix/Foreign Key), ID=3 (Column hallucination), ID=6 (ID missing inference)
    """
    is_secondary = bool(secondary_rag_content and error_msg and first_sql)
    dialect_warnings = get_dialect_specific_warnings(target_db_type)

    # [Core] Get real table structure information (Raw String)
    # Pass through directly without any Python-side formatting
    true_tc_str = retrieval_item.get("true_tables_columns", "")
    
    if true_tc_str:
        schema_display = f"""
        #######################################################################
        ### 【CRITICAL】DATABASE SCHEMA KNOWLEDGE (Reference Standard)
        #######################################################################
        **This is the retrieved known table column list. Data format**: `TableName.ColumnName, ...`
        
        [SCHEMA START]
        {true_tc_str}
        [SCHEMA END]
        
        **Column Name Decision Logic (Must be strictly executed)**:
        
        1. **Exact Table Name Match**:
           - **Rule**: Table names must match [SCHEMA] exactly!
           - **Scenario**: If NL says "channels", but Schema has `signal_channels`, you must write `FROM signal_channels`. Do not ignore prefixes like `signal_`, `tbl_`.
        
        2. **Attribute Column Strict Match**:
           - **Rule**: For common attributes like `name`, `status`, `type`, they must exist in Schema.
           - **Pitfall Prevention (ID=29)**: If Schema only has `unit_id` but no `unit`, it means this is a foreign key! Do not select `unit` directly, but find the corresponding dictionary table (like `signal_units`) to JOIN.
           - **Naming**: If the table only has `name`, do not fabricate `company_name`.
           
        3. **Association Key Intelligent Inference**:
           - **Rule**: If during JOIN, you find that obvious Primary/Foreign Keys (like `user_id`) are accidentally missing from the [SCHEMA] list, **it is allowed and strongly recommended** to infer the ID column name based on SQL standard naming conventions.
           - **Strict Prohibition**: Absolutely prohibited to join using mismatched types just to fit the whitelist (e.g., `ON table.id = table.name`), which leads to `ORA-01722` error.
        #######################################################################
        """
    else:
        # Guidance when no Schema is provided
        schema_display = f"""
        #### Schema: No detailed column names provided
        **Note**: Since no Schema is provided, please infer based on general SQL naming conventions.
        - **Table Name Guessing**: Note possible business prefixes (like `signal_`, `emp_`).
        - **Column Name Guessing**: Prioritize most common names (like `name` instead of `company_name`).
        - **Foreign Key Awareness**: If Status/Type, consider if it is an ID reference needing a dictionary table Join.
        """

    # --- 1. Syntax Reference ---
    if not is_secondary:
        retrieval_results = retrieval_item.get("retrieval_results", {})
        target_grammar = retrieval_results.get(target_db_type, "No specific syntax reference").strip()
        grammar_section = textwrap.dedent(f"""\
            ### 1. {target_db_type} Syntax Reference
            {target_grammar}
            """)
    else:
        grammar_section = textwrap.dedent(f"""\
            ### 1. Correction Context ({target_db_type})
            **Previous Error SQL**: 
            {first_sql}
            **Error Message**: 
            {error_msg}
            """)

    # --- 2. Rules/Correction Reference ---
    if is_secondary:
        rule_section = textwrap.dedent(f"""\
            ### 2. Correction Reference Material
            {secondary_rag_content if secondary_rag_content else "None"}
            """)
    else:
        rule_section = textwrap.dedent(f"""\
            ### 2. Complete Syntax Rules
            {db_rule_content if db_rule_content else "None"}
            """)

    # --- 3. Requirements and Schema (Inject Schema) ---
    requirement_section = textwrap.dedent(f"""\
        ### 3. Core Requirements and Data Definition
        #### User Question:
        {retrieval_item.get("question", "")}

        #### Logic Rewrite (NL2SQL Logic):
        {retrieval_item.get("nl2_rewrite", "")}
        #### 【Schema Reference】
        Must use the following Schema information for SQL generation. Do not use content not provided. Also, the examples provided in the syntax are only for reference on how to use syntax, not for you to fabricate non-existent tables or columns.
        {schema_display}
        """)

    # --- 4. Generation Instructions ---
    dialect_instruction = f"【{target_db_type} Taboos】：\n   {dialect_warnings}"

    generate_rules = [
        f"1. **Strict Dialect**: Generate SQL conforming to **{target_db_type}**.",
        f"2. **Table Lookup Strategy**:\n   - **Table Name**: Full word match (note prefixes).\n   - **Attributes**: Strict table lookup (note foreign keys).\n   - **Join Keys**: Inference allowed, **Strictly Prohibit ID=Name**.",
        "3. **Logic Completeness**: Implement all filtering and aggregation in NL2SQL Logic.",
        f"{dialect_instruction}",
        f"5. **Output Format**:\n### {target_db_type}\n[{target_db_type} SQL Statement]"
    ]

    requirement_section += "### 4. Final Instructions\n" + "\n".join(generate_rules)

    full_prompt = requirement_section+grammar_section + rule_section 
    return truncate_content(full_prompt, max_length=200000).strip()


def build_logic_fix_prompt(question, nl2_rewrite, wrong_sql, analysis_reason, target_db_type, true_tables_columns=None):
    """
    Logic Fix Prompt
    """
    dialect_warnings = get_dialect_specific_warnings(target_db_type)

    schema_info = ""
    if true_tables_columns:
        schema_info = textwrap.dedent(f"""\
        #### 【Schema Reference (Whitelist)】
        [SCHEMA_START]
        {true_tables_columns}
        [SCHEMA_END]
        """)

    return textwrap.dedent(f"""\
        ### Task: Fix SQL Logic Defects ({target_db_type})

        #### 1. Core Requirements
        {nl2_rewrite}

        {schema_info}

        #### 2. Incorrect SQL
        {wrong_sql}

        #### 3. Failure Reason
        {analysis_reason}

        #### 4. Fix Instructions
        1. **Schema Validation**:
           - **Table Name**: Check for prefix errors.
           - **Column Name**: Check for fabricated column names (e.g., `company_name` vs `name`).
        2. **Type Safety (Critical)**:
           - Check JOIN conditions. If `user_id = user_name` or similar **ID = String** occurs, this is a serious error.
           - If Schema is missing ID column, please **infer** standard ID column name for fix.
        3. **Identifier Correction**:
           - Oracle reserved words (like `date`) please change to uppercase quotes `\"DATE\"`.
        4. {dialect_warnings}

        **Output Format**:
        ### {target_db_type}
        ```sql
        SELECT ... ;
        ```
        """)


def build_semantic_check_prompt(question, nl2_rewrite, sql, db_type):
    """
    Construct Semantic Verification Prompt (No modification needed)
    """
    return textwrap.dedent(f"""\
        ### Task: Strict SQL Semantic Consistency Audit

        You are a code audit expert. Your task is to verify if the generated **{db_type} SQL** strictly follows the requirement definition.

        #### 1. Core Requirement Specification (Standard)
        --------------------------------------------------
        {nl2_rewrite}
        --------------------------------------------------

        #### 2. SQL to Verify (Target: {db_type})
        {sql}

        #### 3. Audit Rules
        1. **Source & Joins**: Check if table names and joins are correct. Ensure no ID=NAME incorrect joins.
        2. **Filters**: Check if WHERE conditions are completely consistent (neither more nor less).
        3. **Aggregation**: Check calculation logic.
        4. **Return**: Check if SELECT columns correspond.

        #### 4. Output Format
        Return only JSON object:
        {{
            "status": "PASS" or "FAIL",
            "reason": "Failure reason (e.g., Filters Error: missed date filter...)"
        }}
        """)