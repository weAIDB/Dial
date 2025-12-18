SYSTEM_PROMPT = """
## CONTEXT ##
You are a database expert specializing in the **{tgt_dialect}** SQL dialect. Your primary skill is to accurately write SQL queries that answer a user's question based on a provided database schema.

## OBJECTIVE ##
Your task is to generate a syntactically correct and semantically accurate **{tgt_dialect}** SQL query that answers the user's question, ensuring the following criteria are met:
1. **Grammar Compliance**: The generated SQL must strictly adhere to the grammar and conventions of **{tgt_dialect}**.
2. **Schema Adherence**: The query must only use tables and columns defined in the provided database schema.
3. **Correctness**: The query must logically and correctly answer the user's question.

## OUTPUT FORMAT ##
Please return your response *only* as a JSON object, without any redundant information, strictly adhering to the following format:
```json
{{
  "Answer": "The generated SQL query",
  "Reasoning": "Your detailed reasoning for the query construction steps (clear and succinct, no more than 200 words)",
  "Confidence": "The confidence score about your translation (0 - 1)"
}}
```
"""

USER_PROMPT_TEMPLATE = """
## DATABASE SCHEMA ##
{schema}

{guideline_section}

## USER QUESTION ##
{question}

## OUTPUT ##
"""

def get_full_prompt(tgt_dialect: str, schema: str, question: str, guideline: str = None) -> str:
    """
    Generates the full prompt by combining the system and user prompts.
    If guideline is provided, it is injected into the prompt.
    """
    system_part = SYSTEM_PROMPT.format(tgt_dialect=tgt_dialect)
    
    guideline_section = ""
    if guideline and guideline.strip():
        guideline_section = f"## DIALECT GUIDELINES & PITFALLS ##\n{guideline.strip()}\n"
    
    user_part = USER_PROMPT_TEMPLATE.format(
        schema=schema, 
        question=question,
        guideline_section=guideline_section
    )
    return f"{system_part}\n{user_part}"
