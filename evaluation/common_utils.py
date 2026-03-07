# evaluation/common_utils.py
# Shared utilities: logging, JSON I/O, and custom JSON encoder for DB types.

import json
import logging
from datetime import date, datetime, timedelta, time
import decimal

# -----------------------------------------------------------------------------
# Logging setup
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("EvaluationPipeline")


# -----------------------------------------------------------------------------
# Custom JSON encoder for DB types (date, datetime, Decimal, bytes, etc.)
# -----------------------------------------------------------------------------
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime, time)):
            return obj.isoformat()
        elif isinstance(obj, timedelta):
            return str(obj)
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        elif isinstance(obj, bytes):
            return obj.decode("utf-8", errors="ignore")
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        try:
            if hasattr(obj, "__iter__") and not isinstance(obj, (str, dict, list, tuple)):
                return list(obj)
        except Exception:
            pass
        return str(obj)


# -----------------------------------------------------------------------------
# JSON load / save helpers
# -----------------------------------------------------------------------------
def load_json(file_path: str) -> list | dict | None:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Failed to load %s: %s", file_path, e)
        return None


def save_json(data, file_path: str) -> bool:
    try:
        json_str = json.dumps(data, ensure_ascii=False, indent=2, cls=CustomJSONEncoder)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json_str)
        return True
    except Exception as e:
        logger.error("Failed to save %s: %s", file_path, e)
        return False
