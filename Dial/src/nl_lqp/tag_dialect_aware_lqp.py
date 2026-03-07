# src/nl_lqp/tag_dialect_aware_lqp.py
# Step 2: Tag dialect-aware LQP from NL-LQP.
# Parses NL-LQP markdown, runs cascaded operator labeling to find dialect-sensitive
# operators, maps them to functional categories via LLM. Output: dialect_aware_lqp.json.

import json
import re
import os
import math
import asyncio
import time
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
    NL_LQP_OUTPUT_JSON,
    DIALECT_AWARE_LQP_OUTPUT_JSON,
    TEMP_DIALECT_AWARE_DIR,
    TARGET_DIALECTS,
    MAX_CONCURRENT_REQUESTS,
    CATEGORY_PRIORITY,
    LEXICAL_TRIGGERS,
    SENSITIVE_DATA_TYPES,
    FUNCTIONAL_CATEGORIES,
)

RE_JSON_CODE_BLOCK = re.compile(r"```(?:json)?\s*({.*?})\s*```", re.DOTALL | re.IGNORECASE)
RE_DATA_TYPE = re.compile(r"\(([A-Za-z0-9_]+)\)")

PROMPT_TEMPLATE_CATEGORY_MAPPING = """
# Task: Functional Category Mapping & Operator Standardization

## Role
You are an expert Database Dialect Translator. Map a dialect-sensitive logical operator into a standardized functional category and a clean, standardized description.

## Allowed Functional Categories (C)
{CATEGORIES}

## Input Operator
**Original Description**: {OPERATOR_TEXT}

## Instructions
1. Assign the operator to the MOST relevant category from the list.
2. Standardize: strip unnecessary explanations; keep core intent only.

## Output Format (STRICT JSON)
Output a valid JSON object with exactly two keys: `category`, `standard_description`.

```json
{{
  "category": "...",
  "standard_description": "..."
}}
```
"""


def robust_json_load(raw_str):
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


def parse_lqp_markdown(markdown_str):
    """Parse NL-LQP markdown into a list of operators (section + original_text)."""
    operators = []
    current_section = None
    for line in markdown_str.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("###"):
            current_section = line.replace("###", "").strip()
        elif (line.startswith("-") or line.startswith("*")) and current_section:
            op_text = line.lstrip("-* ").strip()
            operators.append({"section": current_section, "original_text": op_text})
    return operators


def get_category_priority(section_name):
    for key, prio in CATEGORY_PRIORITY.items():
        if key in section_name:
            return prio
    return 99


def cascaded_operator_labeling(operators):
    """Select dialect-sensitive operators via category sort, lexical triggers, and data-type checks."""
    if not operators:
        return []
    sorted_operators = sorted(operators, key=lambda op: get_category_priority(op["section"]))
    total_ops = len(sorted_operators)
    threshold = min(max(5, math.ceil(total_ops * 0.3)), total_ops)
    candidates = sorted_operators[:threshold]
    sensitive_operators = []
    for op in candidates:
        is_sensitive = False
        reasons = []
        text_lower = op["original_text"].lower()
        matched_lexical = [kw for kw in LEXICAL_TRIGGERS if kw in text_lower]
        if matched_lexical:
            is_sensitive = True
            reasons.append(f"Lexical Triggers: {','.join(matched_lexical)}")
        types_in_text = RE_DATA_TYPE.findall(op["original_text"])
        matched_types = [t for t in types_in_text if t.upper() in SENSITIVE_DATA_TYPES]
        if matched_types:
            is_sensitive = True
            reasons.append(f"Sensitive Data Types: {','.join(matched_types)}")
        if is_sensitive:
            op["sensitivity_reasons"] = reasons
            sensitive_operators.append(op)
    return sensitive_operators


async def standardize_operator_async(client, op_text):
    """Map one operator to category and standard_description via LLM."""
    prompt_content = PROMPT_TEMPLATE_CATEGORY_MAPPING.format(
        CATEGORIES=json.dumps(FUNCTIONAL_CATEGORIES, ensure_ascii=False),
        OPERATOR_TEXT=op_text,
    )
    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a precise database dialect syntax analyzer."},
                {"role": "user", "content": prompt_content},
            ],
            temperature=0.1,
        )
        content = response.choices[0].message.content.strip()
        parsed = robust_json_load(content)
        if parsed and "category" in parsed and "standard_description" in parsed:
            return parsed
        return {"category": "Parse_Error", "standard_description": op_text}
    except Exception as e:
        return {"category": "Request_Error", "standard_description": f"Error: {str(e)}"}


async def process_item_dialect(client, item, dialect, semaphore):
    """Produce dialect-aware LQP (list of standardized ops) for one item and one dialect."""
    nl_key = f"final_NL_{dialect}"
    if nl_key not in item or not item[nl_key].get("NL-LQP"):
        return None
    markdown_plan = item[nl_key]["NL-LQP"]
    all_operators = parse_lqp_markdown(markdown_plan)
    dialect_sensitive_ops = cascaded_operator_labeling(all_operators)
    standardized_ops = []
    if dialect_sensitive_ops:
        async with semaphore:
            tasks = [standardize_operator_async(client, op["original_text"]) for op in dialect_sensitive_ops]
            standardization_results = await asyncio.gather(*tasks)
            for op, std_res in zip(dialect_sensitive_ops, standardization_results):
                standardized_ops.append({
                    "original_section": op["section"],
                    "original_text": op["original_text"],
                    "sensitivity_reasons": op["sensitivity_reasons"],
                    "mapped_category": std_res.get("category", "Unknown"),
                    "standard_description": std_res.get("standard_description", op["original_text"]),
                })
    return standardized_ops


async def process_single_item(item, client, semaphore):
    """Tag all target dialects for one item; save temp JSON."""
    qid = str(item.get("question_id"))
    for dialect in TARGET_DIALECTS:
        dialect_ops = await process_item_dialect(client, item, dialect, semaphore)
        if dialect_ops is not None:
            item[f"Dialect_Aware_LQP_{dialect}"] = dialect_ops
    temp_path = os.path.join(TEMP_DIALECT_AWARE_DIR, f"{qid}.json")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(item, f, ensure_ascii=False, indent=2)


async def main_async():
    """Load NL-LQP output, run dialect-aware tagging, merge and save."""
    os.makedirs(TEMP_DIALECT_AWARE_DIR, exist_ok=True)
    client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    if not os.path.exists(NL_LQP_OUTPUT_JSON):
        print("Error: Input JSON not found. Run generate_nl_lqp first.")
        return
    with open(NL_LQP_OUTPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    todo_data = []
    for item in data:
        qid = str(item["question_id"])
        temp_path = os.path.join(TEMP_DIALECT_AWARE_DIR, f"{qid}.json")
        if os.path.exists(temp_path):
            with open(temp_path, "r", encoding="utf-8") as f:
                cached_item = json.load(f)
                if all(
                    f"Dialect_Aware_LQP_{d}" in cached_item
                    for d in TARGET_DIALECTS
                    if f"final_NL_{d}" in item
                ):
                    continue
        todo_data.append(item)
    if not todo_data:
        print("All dialect-aware specifications already completed.")
    else:
        print(f"Starting Dialect-Aware Logic Specification for {len(todo_data)} items...")
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        tasks = [process_single_item(item, client, semaphore) for item in todo_data]
        await tqdm_asyncio.gather(*tasks, desc="Building Dialect-Aware LQP")
    print("Merging results...")
    temp_results = {}
    for f_name in os.listdir(TEMP_DIALECT_AWARE_DIR):
        if f_name.endswith(".json"):
            with open(os.path.join(TEMP_DIALECT_AWARE_DIR, f_name), "r", encoding="utf-8") as tf:
                item = json.load(tf)
                temp_results[str(item["question_id"])] = item
    final_output = []
    for item in data:
        qid = str(item["question_id"])
        final_output.append(temp_results.get(qid, item))
    os.makedirs(os.path.dirname(DIALECT_AWARE_LQP_OUTPUT_JSON) or ".", exist_ok=True)
    with open(DIALECT_AWARE_LQP_OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
    print(f"Done! Dialect-Aware LQP saved to {DIALECT_AWARE_LQP_OUTPUT_JSON}")


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main_async())
    print(f"Total time: {time.time() - start_time:.2f}s")
