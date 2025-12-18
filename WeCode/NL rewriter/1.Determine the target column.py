import json
import re
import os
import asyncio
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm_asyncio
import time

# ==========================================
# [USER CONFIGURATION] 用户配置区域
# ==========================================

OPENAI_CONFIG = {
    "api_key": "sk-537b00fe9a444de096505eca44f7c6bc",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat",
}

FILE_CONFIG = {
    'input_json': '数据/schema_linking98.json',
    'output_json': '数据/deepseekV3.2/semantic_analysis98.json'
}

# 并发数 (根据 API 限流调整)
MAX_CONCURRENT_REQUESTS = 15

# ==========================================
# [OPTIMIZED PROMPT] 语义意图分析模板
# ==========================================

PROMPT_TEMPLATE_SEMANTIC = """
# Task: Identify Semantic Result Content

Your goal is to determine **exactly what the user wants to see** based on the Question and Evidence.
Focus on the *business answer*, not SQL columns.

## Strict Guidelines
1. **Boolean / Existence**: If the question asks "Is there...", "Did...", "Does...", or "True/False", return `"YES or NO"`.
2. **Status / Choice**: If checking a specific state (e.g., "Is it finished?"), return the descriptive states (e.g., `"Finished or NOT finished"`).
3. **Entities & Attributes**: Describe the target attribute naturally (e.g., "Student Name", "Average Score").
   - **Composite Names**: If the evidence implies a name is split (e.g., first/last), return `"forename, surname"`.
   - **Calculations**: Do NOT use SQL functions (e.g., NO `MAX(age)`). Instead, say `"Maximum Age"` or `"Calculated Age"`.
4. **Distinctness**: If the question implies a list of unique values (e.g., "List ages of...", "Types of..."), prefix with "Distinct".

## Few-Shot Examples

**Ex 1 (Boolean)**
Q: "For the set of cards with 'Ancestor's Chosen', is there a Korean version?"
Ev: Korean version refers to language = 'Korean'
> Output:
```json
{{
  "Chain-of-Thought": "The user is asking a Yes/No question about the existence of a specific version. No data list is needed, just the boolean state.",
  "return_num": 1,
  "return_content": "YES or NO"
}}
```

**Ex 2 (Binary State)**
Q: "User No.23853 gave a comment to a post at 9:08:18 on 2013/7/12, was that post well-finished?"
Ev: user no. 23853 refers to UserId = '23853'; at 9:08:18 on 2013/7/12 refers to CreationDate = '2013-07-12 09:08:18.0'; not well-finished refers to ClosedDate IS NULL and vice versa
> Output:
```json
{{
  "Chain-of-Thought": "The user asks to classify the user into one of two states based on the definition provided.",
  "return_num": 1,
  "return_content": "well-finished or NOT well-finished"
}}
```

**Ex 3 (Composite Entity)**
Q: "List top 3 German drivers who have the shortest average pit stop."
Ev: Full name refers to drivers.forename and drivers.surname
> Output:
```json
{{
  "Chain-of-Thought": "The user wants to identify the drivers. The evidence indicates names are split into forename and surname.",
  "return_num": 2,
  "return_content": "forename, surname"
}}
```

**Ex 4 (Calculation & Distinctness)**
Q: "Calculate for the player's age who have a sprint speed of no less than 97."
Ev: players age = SUBTRACT(Now, birthday)
> Output:
```json
{{
  "Chain-of-Thought": "The question asks for 'age' derived from calculation. Since multiple players might have the same age and the user asks for the ages satisfying the condition, we list the distinct calculated values.",
  "return_num": 1,
  "return_content": "Distinct calculated age"
}}
```

## Current Task
**Question**: {QUESTION}
**Evidence**: {EVIDENCE}

Please generate the JSON response.
"""


# ==========================================
# [HELPER FUNCTIONS]
# ==========================================

def clean_json_string(content):
    match = re.search(r'```(?:json)?\s*({.*})\s*```', content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1)
    start = content.find('{')
    end = content.rfind('}')
    if start != -1 and end != -1:
        return content[start:end + 1]
    return content


# ==========================================
# [CORE LOGIC]
# ==========================================

async def analyze_intent_async(client, question, evidence):
    # 处理 Evidence 为空的情况，避免传入 None
    formatted_evidence = evidence.strip() if evidence and isinstance(evidence, str) else "None"

    prompt_content = PROMPT_TEMPLATE_SEMANTIC.format(
        QUESTION=question,
        EVIDENCE=formatted_evidence
    )

    retries = 3
    for attempt in range(retries):
        try:
            response = await client.chat.completions.create(
                model=OPENAI_CONFIG['model'],
                messages=[
                    {"role": "system", "content": "You are a Semantic Data Analyst."},
                    {"role": "user", "content": prompt_content}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content.strip()
            cleaned_json = clean_json_string(content)
            result = json.loads(cleaned_json)

            # 默认值保护
            return {
                "Chain-of-Thought": result.get("Chain-of-Thought", ""),
                "return_num": result.get("return_num", 0),
                "return_content": result.get("return_content", "")
            }

        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(1)
            else:
                return {
                    "Chain-of-Thought": f"Error: {str(e)}",
                    "return_num": 0,
                    "return_content": "Error"
                }


async def process_single_item(item, client, semaphore):
    question = item.get('question', '')
    evidence = item.get('evidence', '')

    async with semaphore:
        result = await analyze_intent_async(client, question, evidence)

    # 结果回写
    item['semantic_analysis'] = result


async def main_async():
    client = AsyncOpenAI(
        api_key=OPENAI_CONFIG['api_key'],
        base_url=OPENAI_CONFIG['base_url']
    )

    if not os.path.exists(FILE_CONFIG['input_json']):
        print(f"Error: Input file not found at {FILE_CONFIG['input_json']}")
        return

    with open(FILE_CONFIG['input_json'], 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Loaded {len(data)} items. Starting analysis...")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    tasks = [process_single_item(item, client, semaphore) for item in data]

    try:
        await tqdm_asyncio.gather(*tasks, desc="Analyzing Intents")
    except KeyboardInterrupt:
        print("\nProcess interrupted.")

    output_path = FILE_CONFIG['output_json']
    output_dir = os.path.dirname(output_path)
    if output_dir:  # 只有当存在一个明确的目录名时才尝试创建
        os.makedirs(output_dir, exist_ok=True)

    print(f"Saving results to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Done. Saved to {FILE_CONFIG['output_json']}")


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main_async())
    print(f"Time elapsed: {time.time() - start_time:.2f}s")