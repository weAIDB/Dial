# step1_executor.py
import pymysql
import sqlite3
import time
import os
import psycopg2
from tqdm import tqdm


from typing import Dict, Any
from config import EXECUTE_ENGINES
from common_utils import logger, save_json, load_json


class BaseExecutor:
    def __init__(self, db_config):
        self.db_config = db_config
        self.max_rows = 1000

    def get_connection(self, db_id: str):
        raise NotImplementedError

    def execute_sql(self, sql: str, db_id: str) -> Dict[str, Any]:
        connection = None
        cursor = None
        try:
            connection = self.get_connection(db_id)
            cursor = connection.cursor()

            start_time = time.time()
            cursor.execute(sql)
            # 对于 SQLite, cursor.execute 只能执行单条，如果是 script 需要 executescript 但一般评估是单条

            sql_upper = sql.strip().upper()
            is_select = sql_upper.startswith(('SELECT', 'SHOW', 'DESCRIBE', 'DESC', 'WITH'))

            if is_select:
                results = cursor.fetchall()
                if cursor.description:
                    column_names = [desc[0] for desc in cursor.description]
                else:
                    column_names = []

                execution_time = time.time() - start_time

                truncated = False
                if len(results) > self.max_rows:
                    results = results[:self.max_rows]
                    truncated = True

                return {
                    'success': True, 'columns': column_names, 'data': list(results),
                    'execution_time': round(execution_time, 3), 'row_count': len(results), 'truncated': truncated
                }
            else:
                connection.commit()
                execution_time = time.time() - start_time
                return {
                    'success': True, 'columns': ['affected_rows'], 'data': [[cursor.rowcount]],
                    'execution_time': round(execution_time, 3), 'row_count': 1
                }
        except Exception as e:
            return {'success': False, 'error': str(e), 'execution_time': 0}
        finally:
            if cursor: cursor.close()
            if connection: connection.close()


class MySQLExecutor(BaseExecutor):
    def get_connection(self, db_id: str):
        config = self.db_config.copy()
        config['database'] = db_id  # 动态指定 DB
        config['charset'] = 'utf8mb4'
        config['autocommit'] = True
        return pymysql.connect(**config)


class PostgreSQLExecutor(BaseExecutor):
    def get_connection(self, db_id: str):
        if not psycopg2:
            raise ImportError("psycopg2 module not found")
        config = self.db_config.copy()
        config['dbname'] = db_id  # PG 使用 dbname
        return psycopg2.connect(**config)


class SQLiteExecutor(BaseExecutor):
    def __init__(self, sqlite_dir):
        super().__init__({})
        self.sqlite_dir = sqlite_dir

    def get_connection(self, db_id: str):
        # 假设路径结构为: root_dir/db_id/db_id.sqlite
        db_path = os.path.join(self.sqlite_dir, db_id, f"{db_id}.sqlite")
        if not os.path.exists(db_path):
            # 尝试直接在 root_dir/db_id.sqlite
            db_path = os.path.join(self.sqlite_dir, f"{db_id}.sqlite")

        if not os.path.exists(db_path):
            raise FileNotFoundError(f"SQLite DB not found: {db_path}")

        return sqlite3.connect(db_path)


def get_executor(engine_type, db_config_all):
    if engine_type == 'mysql':
        return MySQLExecutor(db_config_all['mysql'])
    elif engine_type == 'postgres':
        return PostgreSQLExecutor(db_config_all['postgres'])
    elif engine_type == 'sqlite':
        return SQLiteExecutor(db_config_all['sqlite_dir'])
    else:
        raise ValueError(f"Unknown engine: {engine_type}")


def run_execution(input_file, output_file, db_config_all, target_engine=None):
    """执行单个文件的SQL处理"""
    logger.info(f"[Step 1] 开始执行SQL: {input_file} | 目标引擎: {target_engine}")
    data = load_json(input_file)
    if not data: return False

    final_output = []

    # 如果指定了引擎，则只跑那一个；否则跑配置里的所有
    engines_to_run = [target_engine] if target_engine else EXECUTE_ENGINES

    for engine in engines_to_run:
        executor = get_executor(engine, db_config_all)
        for index, item in enumerate(tqdm(data, desc="执行SQL进度", unit="条")):
            try:
                item_core = item if 'item' in item else item

                question_id = item_core.get('question_id', f'index_{index}')
                # 动态获取 db_id
                db_id = item_core.get('db_id', 'bird')  # 默认 fallback 到 bird，或者改为报错

                # 动态获取对应引擎的 SQL
                # 尝试多种路径获取 SQL，优先获取 target_engine 对应的字段
                gen_obj = item_core.get("sql_generation", {}) or item_core.get("gold_sql", {})

                generated_sql = (
                    gen_obj.get(engine)
                )

                output_item = {
                    'question_id': question_id,
                    'db_id': db_id,
                    'engine': engine,
                    'generated_sql': generated_sql,
                    'result': {'status': 'skipped', 'message': f'无 {engine} 语句'}
                }

                if generated_sql and isinstance(generated_sql, str) and generated_sql.strip():
                    # 传入 db_id 进行执行
                    res = executor.execute_sql(generated_sql, db_id)
                    if res['success']:
                        output_item['result'] = {
                            'status': 'success', 'columns': res['columns'], 'data': res['data'],
                            'execution_time': res['execution_time'], 'row_count': res['row_count']
                        }
                    else:
                        output_item['result'] = {'status': 'error', 'error': res['error']}

                final_output.append(output_item)

            except Exception as e:
                logger.error(f"处理条目 {index} 失败: {e}")
                final_output.append({'question_id': f"err_{index}", 'result': {'status': 'error', 'error': str(e)}})

    save_json(final_output, output_file)
    logger.info(f"[Step 1] {target_engine} 执行完成，结果已保存至 {output_file}")
    return True