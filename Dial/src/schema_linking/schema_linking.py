# src/schema_linking/schema_linking.py
# Step 0: Schema linking. If input item has true_tables_columns, keep it; else fetch full schema
# from target DB by db_id, ask LLM to select relevant Table.Column as true_tables_columns for downstream.

import json
import re
import os
import asyncio
import time
from pathlib import Path
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm_asyncio

import sys
_DIAL_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_DIAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_DIAL_ROOT))

from conf import (
    PIPELINE_INPUT_JSON,
    SCHEMA_LINKING_OUTPUT_JSON,
    SCHEMA_LINKING_DIALECT,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL_NAME,
    GLOBAL_DB_CONFIG,
    MAX_CONCURRENT_REQUESTS,
)
from src.schema.ddl_fetcher import DDLFetcher


PROMPT_TEMPLATE_SCHEMA_LINKING = """# Task: Schema Linking for Natural Language Question

## Role
You are a database schema expert. Given a natural language question and the **full schema** of a database (all tables and columns with types and sample values), select the **minimal set of Table.Column** that are likely needed to answer the question.

## Inputs
1. **Question**: {QUESTION}
2. **Database schema (DDL with column types and sample values)**:
{SCHEMA_DDL}

## Instructions
- Output only the relevant Table.Column pairs that the question will likely use (for SELECT, JOIN, WHERE, GROUP BY, ORDER BY, etc.).
- Use exact table and column names as they appear in the schema.
- Format: comma-separated list, e.g. `TableA.col1, TableA.col2, TableB.col3`.
- Do not include columns that are clearly irrelevant to the question.
- If the question is ambiguous, include all plausible Table.Column that might be used.

## Output Format (STRICT)
Output a valid JSON object with exactly one key: `tables_columns`. The value must be a single string of comma-separated `Table.Column` (no extra spaces except after commas if you prefer).

Example: {{ "tables_columns": "users.id, users.name, orders.user_id, orders.amount" }}

Generate the JSON now.
"""

RE_JSON_CODE_BLOCK = re.compile(r"```(?:json)?\s*({.*?})\s*```", re.DOTALL | re.IGNORECASE)


def robust_json_load(raw_str):
    """Extract and parse JSON from LLM output."""
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


def normalize_tables_columns(s: str) -> str:
    """Normalize to 'Table.Col, Table.Col' format (trim, single space after comma)."""
    if not s or not isinstance(s, str):
        return ""
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return ", ".join(parts)


def get_full_schema_sync(fetcher: DDLFetcher, db_id: str, dialect: str) -> str:
    """Fetch full DDL (all tables) for db_id on the given dialect."""
    tables = []
    dialect = dialect.lower()
    if dialect == "mysql":
        return fetcher.get_mysql_ddl(db_id, tables)
    if dialect == "sqlite":
        return fetcher.get_sqlite_ddl(db_id, tables)
    if dialect == "postgres":
        return fetcher.get_postgres_ddl(db_id, tables)
    if dialect == "sqlserver":
        return fetcher.get_sqlserver_ddl(db_id, tables)
    if dialect == "oracle":
        return fetcher.get_oracle_ddl(db_id, tables)
    if dialect == "duckdb":
        return fetcher.get_duckdb_ddl(db_id, tables)
    return f"-- Unsupported dialect: {dialect}"


async def schema_linking_single_async(client: AsyncOpenAI, question: str, schema_ddl: str) -> str:
    """Call LLM to predict relevant tables_columns from question and full schema."""
    if not schema_ddl or schema_ddl.strip().startswith("-- Error"):
        return ""
    prompt = PROMPT_TEMPLATE_SCHEMA_LINKING.format(
        QUESTION=question,
        SCHEMA_DDL=schema_ddl,
    )
    for attempt in range(3):
        try:
            response = await client.chat.completions.create(
                model=OPENAI_MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a precise schema linking assistant. Output only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            content = (response.choices[0].message.content or "").strip()
            parsed = robust_json_load(content)
            if parsed and "tables_columns" in parsed:
                return normalize_tables_columns(parsed["tables_columns"])
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
            else:
                return f"Error: {str(e)}"
    return ""


async def process_item(item: dict, client: AsyncOpenAI, fetcher: DDLFetcher, semaphore: asyncio.Semaphore) -> dict:
    """For one item: keep true_tables_columns if present; else run schema linking and set it."""
    out = dict(item)
    existing = (item.get("true_tables_columns") or "").strip()
    if existing:
        return out

    db_id = (item.get("db_id") or "").strip()
    question = (item.get("question") or "").strip()
    if not db_id or not question:
        out["true_tables_columns"] = ""
        return out

    async with semaphore:
        loop = asyncio.get_event_loop()
        schema_ddl = await loop.run_in_executor(
            None,
            lambda: get_full_schema_sync(fetcher, db_id, SCHEMA_LINKING_DIALECT),
        )
        tables_columns = await schema_linking_single_async(client, question, schema_ddl)
        out["true_tables_columns"] = tables_columns
    return out


async def main_async():
    """Load pipeline input; for items without true_tables_columns run schema linking; write output."""
    if not os.path.exists(PIPELINE_INPUT_JSON):
        print(f"Pipeline input not found: {PIPELINE_INPUT_JSON}. Skipping schema linking.")
        return

    with open(PIPELINE_INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("Pipeline input must be a JSON array. Skipping schema linking.")
        return

    need_linking = [i for i, item in enumerate(data) if not (item.get("true_tables_columns") or "").strip()]
    if not need_linking:
        print("All items already have true_tables_columns. Copying input to schema linking output.")
        os.makedirs(os.path.dirname(SCHEMA_LINKING_OUTPUT_JSON) or ".", exist_ok=True)
        with open(SCHEMA_LINKING_OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved to {SCHEMA_LINKING_OUTPUT_JSON}")
        return

    print(f"Schema linking for {len(need_linking)} items (dialect={SCHEMA_LINKING_DIALECT})...")
    fetcher = DDLFetcher(GLOBAL_DB_CONFIG)
    client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def process_idx(idx):
        return await process_item(data[idx], client, fetcher, semaphore)

    results = await tqdm_asyncio.gather(
        *[process_idx(i) for i in need_linking],
        desc="Schema linking",
    )
    # Merge back: replace only indices that were processed
    output = list(data)
    for pos, idx in enumerate(need_linking):
        output[idx] = results[pos]

    os.makedirs(os.path.dirname(SCHEMA_LINKING_OUTPUT_JSON) or ".", exist_ok=True)
    with open(SCHEMA_LINKING_OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Done. Saved to {SCHEMA_LINKING_OUTPUT_JSON}")


if __name__ == "__main__":
    start = time.time()
    asyncio.run(main_async())
    print(f"Time: {time.time() - start:.2f}s")
