# src/nl_lqp/generate_nl_lqp.py
# Step 1: Generate dialect-agnostic NL-LQP from natural language questions and schema.
# Uses LLM to produce a linearized logical plan; optionally reviews with DDL/samples.
# Output: NL-LQP JSON (and final_NL_{dialect} per target dialect) for downstream tagging.

import json
import re
import os
import asyncio
import time
import shutil
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm_asyncio

import sys
from pathlib import Path
_DIAL_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_DIAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_DIAL_ROOT))

from conf import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL_NAME,
    GLOBAL_DB_CONFIG,
    TARGET_DIALECTS,
    PIPELINE_INPUT_JSON,
    SCHEMA_LINKING_OUTPUT_JSON,
    NL_LQP_OUTPUT_JSON,
    PROMPT_CACHE_DIR,
    TEMP_NL_LQP_DIR,
    MAX_CONCURRENT_REQUESTS,
)
from src.schema.ddl_fetcher import DDLFetcher

# -----------------------------------------------------------------------------
# Prompt templates (NL-LQP generation and review)
# -----------------------------------------------------------------------------

PROMPT_TEMPLATE_REWRITE = """
    # Task: Generate Natural Language Logical Query Plan (NL-LQP)

    ## Role
    You are a Senior Data Architect with strong business understanding.
    Your task is to translate a natural language question into a **complete, logically executable, dialect-agnostic Natural Language Logical Query Plan(NL-LQP)**.
    The NL-LQP must bridge natural language and SQL while compensating for missing or implicit business logic.

    The NL-LQP acts as an intermediate representation that decouples "What-to-Do" (Business Logic) from "How-to-Implement" (SQL Dialect).

    ---

    ## Inputs
    1. **User Question**
       - The original natural language question.
       - May be ambiguous, incomplete, or business-oriented.

    2. **Selected Schema**
       - A focused list of `Table.Column` pairs that are considered relevant.
       - You MUST prioritize these fields before introducing others.

    3. **DDL**
       - Full table definitions.
       - Use this to:
         - Verify data types
         - Identify implicit or non-standard relationships
         - Detect missing or indirect foreign key paths

    ---

    ## Core Principles (MANDATORY)

    ### 1. Business Logic Depth & Heuristic Compensation
    - For complex or multi-step questions:
      - Decompose the problem into a **business chain** (e.g., event → state → aggregation → comparison).
      - Explicitly state **implicit business constraints** (e.g., "active users", "latest record", "valid period").
      - If the question assumes logic not explicitly stated, apply **reasonable heuristic compensation** and describe it clearly.

    ### 2. Field Usage Priority
    - ALWAYS prefer fields listed in **Selected Schema**.
    - Only introduce additional columns from DDL if:
      - They are strictly required for joins, filters, or correctness.
      - Their necessity is explicitly justified in the logical steps.
    - NEVER invent fields, metrics, or business concepts not grounded in schema or Evidence.

    ### 3. Operand Completeness & Dimension Clarity
    - Ensure every computation has:
      - Clearly defined operands
      - Explicit source columns
    - Clearly distinguish:
      - **Grouping / aggregation dimensions**
      - **Ordering (sorting) dimensions**
      - **Returned (display) columns**
    - Sorting by a column does NOT imply it is returned, and vice versa.

    ### 4. Question Completion Guarantee
    - You MUST fully answer what the User Question asks.
    - Partial plans, vague placeholders, or missing outputs are FORBIDDEN.
    - The `### Return` section must exactly and completely satisfy the question.

    ### 5. Dialect-Agnostic Enforcement
    - FORBIDDEN:
      - Any SQL functions or dialect-specific syntax (e.g., STRFTIME, DATEADD, DATEDIFF, LIMIT).
    - REQUIRED:
      - Use semantic descriptions only (e.g., "extract year from date", "rank by descending value").
    - Use only standard logical operators: =, >, <, >=, <=, ≠.

    ### 6. Aggregation-First & Join Discipline
    - Follow a **CTE-like logical order**, even though no SQL is written:
      1. Filter raw data
      2. Aggregate / compute metrics
      3. THEN join aggregated results to other entities if needed
    - Explicitly reason about:
      - LEFT vs RIGHT vs INNER join semantics
      - Cardinality (One-to-One, One-to-Many, Many-to-Many)
      - Non-standard or indirect join conditions (not just declared foreign keys)

    ---

    ## Data Typing Rule (STRICT)
    - EVERY time a column is mentioned using `Table.Column`,
      you MUST append its data type in parentheses.
      Example:
      - 'orders.OrderDate' (DATE)
      - 'customers.CustomerID' (INT)

    ### Conditional Rationale Rule (STRICT)
    - Rationale is OPTIONAL, not mandatory for every bullet point.
    - ONLY include a rationale when the step involves:
      - Non-obvious reasoning
      - Heuristic or business compensation
      - Ambiguity resolution
      - Join direction justification (LEFT vs INNER vs RIGHT)
      - Grain alignment or de-duplication logic
    - DO NOT include rationale for:
      - Simple filters
      - Direct equality joins on explicit keys
      - Straightforward aggregations without business assumptions
    - When a rationale is included:
      - It MUST be written inline at the end of the bullet point.
      - It MUST be enclosed in parentheses.
      - It MUST NOT appear on a separate line.


    ---

    ## Output Format (STRICT)

    You must output a JSON object with **ONE key only**: `NL-LQP`.

    The value of `NL-LQP` must be a STRING containing a structured logical plan.

    Use Markdown headers (`###`) and bullet points (`-`).

    ### Allowed Categories (ONLY include if relevant)
    - `### Data Sourcing & Association`
    - `### Constraint & Filtering`
    - `### Aggregation & Grouping`
    - `### Scalar Calculation & Transformation`
    - `### Result Organization & Selection`
    - `### Auxiliary & Fallback Operations`

    If a category is not involved, DO NOT include it.

    ---

    ## Category-Specific Rules

    1. **### Data Sourcing & Association**
    - Identify primary tables.
    - Define join topology (Inner/Left/Full) and set operations (Union/Intersect).

    2. **### Constraint & Filtering**
    - Prune search space (row-level filtering).
    - Handle NULLs and complex predicates.

    3. **### Aggregation & Grouping**
    - Define dimensional grouping (Group By).
    - Define metric reduction (Sum, Count, Avg, etc.).

    4. **### Scalar Calculation & Transformation** (Crucial for Dialect Decoupling)
    - Deriving new values from existing attributes.
    - For example: **Temporal Manipulation**: e.g., "Extract year from date", "Calculate duration". **String Processing**: e.g., "Concatenate names", "Substring". **Math/Logic**: e.g., "Round value", "Case-When branching".
    - *Note: Do NOT write SQL functions (e.g., DATE_FORMAT). Write semantic actions.*

    5. **### Result Organization & Selection**
    - Deterministic Sorting (Order By).
    - Cardinality Slicing (Top-K, Limit).
    - Attribute Projection (Select final columns).

    6. **### Auxiliary & Fallback Operations** (Fallback)
    - Any complex logic that strictly does not fit above (e.g., Recursive logic, Window Function hints).
    - Use this only when absolutely necessary.

    ---

    ## Current Task

    **User Question**: {AUGMENTED_QUESTION}  
    **Selected Schema**: {SELECTED_SCHEMA_LIST}  
    **DDL**:
    {RELEVANT_DDL}

    Generate the JSON response now.
"""

PROMPT_TEMPLATE_REVIEW = """
# Task: Logical Query Plan Validator & Optimizer

## Role
You are a Lead Data QA Engineer. Your goal is to verify if a "Natural Language Logical Query Plan"(NL-LQP) is accurate, executable, and business-compliant.You do NOT rewrite from scratch.
You ONLY:
1. Validate whether the NL-LQP is correct
2. Identify concrete errors
3. Fix ONLY the incorrect parts if needed

---

## Context Inputs
1. **User Question**: {QUESTION}
2. **DDL**: {DDL}
3. **Data Samples (Top 3 rows)**:
{SAMPLES}
4. **Candidate NL-LQP**:
{LQP}

---

## Validation Checklist (MUST FOLLOW IN ORDER)

### Check 1: Schema Validity
- Verify every referenced Table exists in DDL.
- Verify every referenced Table.Column exists in the corresponding table.
- Verify data types are consistent with DDL.
- Verify that columns not listed in Selected Schema are only used when strictly necessary.
- If additional columns are introduced without justification, mark as Schema issue.


### Check 2: Value & Operation Correctness
- Verify that operations on column values are logically valid given:
  - Column data type
  - Sample data values
- Examples:
  - String columns are not treated as numeric
  - Date-like strings are not used with unsupported operations
  - Data cleaning / deduplication logic matches observed data patterns
- If an operation is heuristic, check whether it is reasonable.

### Check 3: Format & Structural Correctness
- Output MUST be valid JSON.
- When returning Modified NL-LQP, Modified NL-LQP content must follow NL-LQP format rules.
- Inside NL-LQP:
  - Only allowed sections may appear
  - Markdown headers must use "###"
  - Bullet points must start with "-"
  - Rationale (if present) must be inline and in parentheses
  - No SQL functions or dialect-specific syntax

### Check 4: Question Completion
- Verify that NL-LQP fully answers the original User Question.
- Verify that:
  - All requested entities / metrics are returned
  - No required output is missing
  - The Return section matches the question intent exactly

---

## Output
If correct: {{ "valid": true }}
If issues: {{ "valid": false, "issues": [{{ "type": "...", "description": "..." }}], "Modified NL-LQP": "<corrected plan>" }}
"""

RE_JSON_CODE_BLOCK = re.compile(r"```(?:json)?\s*({.*?})\s*```", re.DOTALL | re.IGNORECASE)


def robust_json_load(raw_str):
    """Extract and parse JSON from LLM output (handles code blocks and stray text)."""
    if not raw_str:
        return None
    clean_str = raw_str.replace("\xa0", " ").replace("\u202f", " ").strip()
    match = RE_JSON_CODE_BLOCK.search(clean_str)
    if match:
        clean_str = match.group(1)
    else:
        start, end = clean_str.find("{"), clean_str.rfind("}")
        if start != -1 and end != -1:
            clean_str = clean_str[start : end + 1]
    try:
        return json.loads(clean_str)
    except Exception:
        return None


def count_steps_by_header(question2_text):
    """Count logical steps per NL-LQP section for stats."""
    stats = {
        "total": 0,
        "breakdown": {
            "Data Sourcing & Association": 0,
            "Constraint & Filtering": 0,
            "Aggregation & Grouping": 0,
            "Scalar Calculation & Transformation": 0,
            "Result Organization & Selection": 0,
            "Auxiliary & Fallback Operations": 0,
        },
    }
    if not question2_text:
        return stats
    current_section = None
    for line in question2_text.split("\n"):
        line = line.strip()
        lower_line = line.lower()
        if line.startswith("###"):
            if "sourcing" in lower_line or "association" in lower_line:
                current_section = "Data Sourcing & Association"
            elif "constraint" in lower_line or "filtering" in lower_line:
                current_section = "Constraint & Filtering"
            elif "aggregation" in lower_line or "grouping" in lower_line:
                current_section = "Aggregation & Grouping"
            elif "scalar" in lower_line or "calculation" in lower_line:
                current_section = "Scalar Calculation & Transformation"
            elif "result" in lower_line or "organization" in lower_line:
                current_section = "Result Organization & Selection"
            elif "fallback" in lower_line or "auxiliary" in lower_line:
                current_section = "Auxiliary & Fallback Operations"
            else:
                current_section = None
        elif current_section and (line.startswith("-") or line.startswith("*")) and len(line) > 2:
            stats["breakdown"][current_section] += 1
            stats["total"] += 1
    return stats


class AsyncDDLLoader:
    """Async wrapper around DDLFetcher with caching for concurrent NL-LQP generation."""

    def __init__(self, config):
        self.fetcher = DDLFetcher(config)
        self.cache = {}
        self.lock = asyncio.Lock()

    async def get_enriched_ddl(self, db_id, tables_str, dialect):
        """Fetch DDL for db_id and tables (cached per dialect:db_id:tables)."""
        cache_key = f"{dialect}:{db_id}:{tables_str}"
        async with self.lock:
            if cache_key in self.cache:
                return self.cache[cache_key]
        tables = self.fetcher.extract_tables(tables_str)
        try:
            ddl_result = await asyncio.to_thread(self._fetch_ddl_sync, db_id, tables, dialect)
        except Exception as e:
            ddl_result = f"-- Error fetching DDL: {str(e)}"
        async with self.lock:
            self.cache[cache_key] = ddl_result
        return ddl_result

    def _fetch_ddl_sync(self, db_id, tables, dialect):
        if dialect == "mysql":
            return self.fetcher.get_mysql_ddl(db_id, tables)
        if dialect == "sqlite":
            return self.fetcher.get_sqlite_ddl(db_id, tables)
        if dialect == "postgres":
            return self.fetcher.get_postgres_ddl(db_id, tables)
        if dialect == "sqlserver":
            return self.fetcher.get_sqlserver_ddl(db_id, tables)
        if dialect == "oracle":
            return self.fetcher.get_oracle_ddl(db_id, tables)
        if dialect == "duckdb":
            return self.fetcher.get_duckdb_ddl(db_id, tables)
        return f"-- Unsupported dialect: {dialect}"


async def generate_nl_lqp_async(client, question, evidence, schema_list_str, ddl_str, dialect):
    """Call LLM to generate NL-LQP for one question and dialect."""
    formatted_evidence = (evidence or "").strip() or "None"
    prompt_content = PROMPT_TEMPLATE_REWRITE.format(
        AUGMENTED_QUESTION=question,
        HINT=formatted_evidence,
        SELECTED_SCHEMA_LIST=schema_list_str,
        RELEVANT_DDL=ddl_str,
    )
    retries = 3
    for attempt in range(retries):
        try:
            response = await client.chat.completions.create(
                model=OPENAI_MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a helpful database architect."},
                    {"role": "user", "content": prompt_content},
                ],
                temperature=0.5,
            )
            content = response.choices[0].message.content.strip()
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
            parsed = robust_json_load(content)
            if parsed:
                return parsed, usage
            raise ValueError("Invalid JSON format")
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                return {"NL-LQP": f"Error: {str(e)}"}, {}


async def review_and_optimize_lqp_with_ddl(client, item, ddl_str, dialect):
    """Optional review step: validate NL-LQP and optionally replace with Modified NL-LQP."""
    nl2_key = f"NL-LQP_{dialect}"
    if nl2_key not in item or not item[nl2_key].get("NL-LQP"):
        return
    nl2_plan = item[nl2_key]["NL-LQP"]
    try:
        samples_str = item.get("samples", "None")
        prompt_content = PROMPT_TEMPLATE_REVIEW.format(
            QUESTION=item.get("question", ""),
            DDL=ddl_str,
            SAMPLES=samples_str,
            LQP=nl2_plan,
        )
        response = await client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a strict data logic auditor."},
                {"role": "user", "content": prompt_content},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
        review_result = robust_json_load(response.choices[0].message.content)
        item[f"NL-LQP_review_{dialect}"] = {
            "valid": review_result.get("valid", False),
            "issues": review_result.get("issues", []),
            "Modified NL-LQP": review_result.get("Modified NL-LQP"),
            "usage": usage,
        }
    except Exception as e:
        item[f"NL-LQP_review_{dialect}"] = {
            "valid": False,
            "issues": [{"type": "Error", "description": str(e)}],
            "Modified NL-LQP": None,
            "usage": {},
        }


def build_final_nl(item, dialect):
    """Build final NL-LQP text (use Modified NL-LQP if review fixed it)."""
    nl2 = item.get(f"NL-LQP_{dialect}", {}).get("NL-LQP", "")
    review = item.get(f"NL-LQP_review_{dialect}", {})
    final_text = nl2
    source = "NL-LQP"
    if review.get("valid") is False and review.get("Modified NL-LQP"):
        final_text = review["Modified NL-LQP"]
        source = "Modified NL-LQP"
    return {
        "NL-LQP": final_text,
        "final_source": source,
        "Steps Count": count_steps_by_header(final_text),
    }


async def process_single_item(item, client, ddl_loader, semaphore):
    """Generate NL-LQP for one item across all target dialects; save temp JSON."""
    async with semaphore:
        qid = str(item.get("question_id"))
        for dialect in TARGET_DIALECTS:
            cache_path = os.path.join(PROMPT_CACHE_DIR, f"{qid}_{dialect}.json")
            if not os.path.exists(cache_path):
                item[f"NL-LQP_{dialect}"] = {"NL-LQP": "Error: DDL cache missing"}
                continue
            with open(cache_path, "r", encoding="utf-8") as f:
                ddl_str = json.load(f).get("ddl_str")
            llm_result, usage_info = await generate_nl_lqp_async(
                client,
                item["question"],
                item.get("evidence", ""),
                item.get("true_tables_columns", ""),
                ddl_str,
                dialect,
            )
            q2_text = llm_result.get("NL-LQP", "")
            item[f"NL-LQP_{dialect}"] = {"NL-LQP": q2_text, "usage": usage_info}
            if q2_text and "Error" not in q2_text:
                await review_and_optimize_lqp_with_ddl(client, item, ddl_str, dialect)
            item[f"final_NL_{dialect}"] = build_final_nl(item, dialect)
        temp_path = os.path.join(TEMP_NL_LQP_DIR, f"{qid}.json")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(item, f, ensure_ascii=False, indent=2)


def _get_effective_pipeline_input_path():
    """Use schema linking output if present, else raw pipeline input."""
    if os.path.isfile(SCHEMA_LINKING_OUTPUT_JSON):
        return SCHEMA_LINKING_OUTPUT_JSON
    return PIPELINE_INPUT_JSON


async def main_async():
    """Build prompt cache (DDL), run NL-LQP generation, merge and save output."""
    os.makedirs(TEMP_NL_LQP_DIR, exist_ok=True)
    os.makedirs(PROMPT_CACHE_DIR, exist_ok=True)
    ddl_loader = AsyncDDLLoader(GLOBAL_DB_CONFIG)
    client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    input_path = _get_effective_pipeline_input_path()
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    finished_qids = {
        f.replace(".json", "")
        for f in os.listdir(TEMP_NL_LQP_DIR)
        if f.endswith(".json")
    }
    todo_data = []
    for item in data:
        qid = str(item["question_id"])
        temp_path = os.path.join(TEMP_NL_LQP_DIR, f"{qid}.json")
        if os.path.exists(temp_path):
            with open(temp_path, "r", encoding="utf-8") as f:
                cached_item = json.load(f)
                if all(f"final_NL_{d}" in cached_item for d in TARGET_DIALECTS):
                    continue
        todo_data.append(item)
    if not todo_data:
        print("All tasks already completed.")
        return
    print("Pre-processing: Fetching DDLs and building prompt cache...")
    async def prepare_prompt(item):
        qid = str(item["question_id"])
        tables_cols_str = item.get("true_tables_columns", "")
        for dialect in TARGET_DIALECTS:
            cache_path = os.path.join(PROMPT_CACHE_DIR, f"{qid}_{dialect}.json")
            if not os.path.exists(cache_path):
                ddl = await ddl_loader.get_enriched_ddl(item["db_id"], tables_cols_str, dialect)
                if ddl and not ddl.startswith("-- Error"):
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump({"ddl_str": ddl}, f, ensure_ascii=False, indent=2)
                else:
                    print(f"Warning: Failed to fetch DDL for {qid} ({dialect}): {ddl}")
    prep_semaphore = asyncio.Semaphore(5)
    async def sem_prepare(item):
        async with prep_semaphore:
            await prepare_prompt(item)
    await tqdm_asyncio.gather(*[sem_prepare(item) for item in todo_data], desc="Building Prompt Cache")
    print("Starting LLM inference...")
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    tasks = [process_single_item(item, client, ddl_loader, semaphore) for item in todo_data]
    await tqdm_asyncio.gather(*tasks, desc="Generating Logic Plans")
    print("Merging results...")
    temp_results = {}
    for f_name in os.listdir(TEMP_NL_LQP_DIR):
        if f_name.endswith(".json"):
            with open(os.path.join(TEMP_NL_LQP_DIR, f_name), "r", encoding="utf-8") as tf:
                item = json.load(tf)
                temp_results[str(item["question_id"])] = item
    final_output = []
    for item in data:
        qid = str(item["question_id"])
        final_output.append(temp_results[qid] if qid in temp_results else item)
    os.makedirs(os.path.dirname(NL_LQP_OUTPUT_JSON) or ".", exist_ok=True)
    with open(NL_LQP_OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
    shutil.rmtree(TEMP_NL_LQP_DIR)
    print(f"Done! Saved to {NL_LQP_OUTPUT_JSON}")


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main_async())
    print(f"Time: {time.time() - start_time:.2f}s")
