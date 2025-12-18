# common_utils.py
import json
import logging
from datetime import date, datetime, timedelta
import decimal

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Pipeline')

class CustomJSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理MySQL返回的特殊类型"""
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        elif isinstance(obj, timedelta):
            return str(obj)
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载文件失败 {file_path}: {e}")
        return None

def save_json(data, file_path):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, cls=CustomJSONEncoder)
        return True
    except Exception as e:
        logger.error(f"保存文件失败 {file_path}: {e}")
        return False