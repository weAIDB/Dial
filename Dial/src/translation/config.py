# src/translation/config.py - Re-exports from conf for translation stage.
from conf import (
    RULES_ROOT_DIR,
    FUNCTIONAL_ROOT_DIR,
    RESULT_JSON_PATH,
    OUTPUT_DIR,
    JSON_OUTPUT_PATH,
    FINAL_REPORT_PATH,
    SEMANTIC_FAIL_LOG_PATH,
    DB_CONFIG,
    DB_TYPE_TO_RULE_FILE,
    SUPPORTED_DBS,
    API_KEY,
    API_BASE_URL,
    MODEL_NAME,
    SQL_EXECUTION_TIMEOUT,
    MAX_RETRY_COUNT,
    MAGIC_SIMILARITY_THRESHOLD,
)
from openai import OpenAI
client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
