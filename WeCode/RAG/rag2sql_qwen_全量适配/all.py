# qwen3-max api_client.py
from config import client, MODEL_NAME

def call_modelscope_api_single(prompt_content, target_db_type):
    """调用ModelScope API生成SQL"""
    if len(prompt_content) > 250000:
        raise RuntimeError(f"单个Prompt过长（{len(prompt_content)}字符），超过API限制")
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": f"你是专业的{target_db_type} SQL生成助手，精通该数据库的语法规范，生成的SQL必须准确实现需求，结尾加分号，只返回指定格式的内容。特别注意避免生成可能导致死循环的SQL（如无限递归查询、笛卡尔积过大的关联查询等）。"
                },
                {
                    "role": "user",
                    "content": prompt_content
                }
            ],
            temperature=0.2,
            max_tokens=1500,
            top_p=0.95,
            stream=False
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        error_detail = f"{str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail += f" | 响应内容: {e.response.text[:500]}"
            except:
                pass
        raise RuntimeError(f"API调用失败: {error_detail}") from e

def call_modelscope_analysis(prompt_content):
    """
    通用分析调用，用于语义验证
    不需要强制返回SQL格式，而是返回分析结果（建议JSON）
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个严谨的SQL代码审计专家。你的任务是对比用户的自然语言需求和生成的SQL语句，判断SQL是否完全实现了需求。请客观、逻辑严密地分析，不要编造理由。"
                },
                {
                    "role": "user",
                    "content": prompt_content
                }
            ],
            temperature=0.1, # 分析任务需要低随机性
            stream=False
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ 分析API调用失败: {e}")
        return None

# qwen3-max config.py
import os
import sys
from openai import OpenAI

# ===================== 路径常量 =====================
RESULT_JSON_PATH = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\方言匹配\输出结果\retrieval_results.json"
OUTPUT_DIR = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\方言匹配\输出结果"
RULES_ROOT_DIR = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\rag\knowledge\Rule_based_dialect"
RAG_MODULE_PATH = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\rag\Model4.0_rag"  # rag_fixed_chunk.py路径
FUNCTIONAL_ROOT_DIR = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\rag\knowledge\Functional_dialect"

# ===================== ModelScope配置 =====================
API_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen3-max"
API_KEY = "sk-a84e13e80bc3459594537184984f32ed"

# ===================== 数据库配置 =====================
# 数据库规则文件映射
DB_TYPE_TO_RULE_FILE = {
    "MySQL": "MySQL.txt",
    "PostgreSQL": "PostgreSQL.txt",
    "SQLite": "SQLite.txt",
    "Oracle": "Oracle.txt",
    "SQL Server": "SQL Server.txt"
}
SUPPORTED_DBS = list(DB_TYPE_TO_RULE_FILE.keys())

# 数据库连接配置
DB_CONNECT_CONFIGS = {
    "MySQL": {
        "host": "192.168.10.100",
        "user": "root",
        "password": "123456",
        "buffered": True,
        "autocommit": True,
        "connection_timeout": 30
    },
    "PostgreSQL": {
        "host": "192.168.10.100",
        "user": "postgres",
        "password": "123456",
        "port": 5433
    },
    "SQLite": {
        "database": r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\bird.db"
    }
}

# ===================== 执行配置 =====================
SQL_EXECUTION_TIMEOUT = 30  # SQL执行超时时间（秒）
MAX_RETRY_COUNT = 1         # 超时重试次数

# ===================== 输出文件路径 =====================
JSON_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "rag2SQL_result.json")
FINAL_REPORT_PATH = os.path.join(OUTPUT_DIR, "final_sql_execution_report.json")
SEMANTIC_FAIL_LOG_PATH = os.path.join(OUTPUT_DIR, "semantic_validation_failures.json")

# ===================== 全局初始化 =====================
# 添加RAG模块路径
sys.path.append(RAG_MODULE_PATH)

# 初始化OpenAI客户端
client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE_URL
)

MAGIC_SIMILARITY_THRESHOLD = 0.75 # 相似度阈值# db_operations.py
import threading
import mysql.connector
from mysql.connector import Error as MySQLError
import psycopg2
from psycopg2 import OperationalError as PgOperationalError
import sqlite3
from sqlite3 import Error as SQLiteError
from config import DB_CONNECT_CONFIGS, SQL_EXECUTION_TIMEOUT
import os
def get_db_connection(db_type, specific_db_name=None):
    """
    创建数据库连接
    :param db_type: 数据库类型 (MySQL, PostgreSQL 等)
    :param specific_db_name: 具体的数据库名 (对应 JSON 中的 db_id)
    """
    if db_type not in DB_CONNECT_CONFIGS:
        raise ValueError(f"不支持的数据库类型：{db_type}")

    # 复制配置，避免污染全局配置
    config = DB_CONNECT_CONFIGS[db_type].copy()
    connection = None

    try:
        # [核心修改] 动态注入数据库名称
        if specific_db_name:
            if db_type == "MySQL":
                config["database"] = specific_db_name
                # print(f"正在连接 MySQL 数据库: {config['host']} -> {specific_db_name}")
                
            elif db_type == "PostgreSQL":
                config["dbname"] = specific_db_name
                # print(f"正在连接 PostgreSQL 数据库: {config['host']} -> {specific_db_name}")
        else:
            print(f"⚠️ 警告: 未指定 specific_db_name (db_id)，尝试使用默认配置连接...")

        # 建立连接
        if db_type == "MySQL":
            connection = mysql.connector.connect(**config)
        elif db_type == "PostgreSQL":
            connection = psycopg2.connect(**config)
        elif db_type == "SQLite":
            # 如果不使用本地文件，通常不支持 SQLite 服务器连接，除非是特殊环境
            # 这里暂时保留 pass 或抛出错误
            print("⚠️ SQLite 模式下通常需要本地文件路径，当前配置未启用文件模式。")
            pass

        if connection:
            # print(f"✅ {db_type} [{specific_db_name}] 连接成功")
            pass
            
        return connection

    except MySQLError as e:
        # 常见错误：数据库不存在 (Error 1049)
        if e.errno == 1049:
            print(f"❌ 数据库 '{specific_db_name}' 在服务器上不存在。请检查 db_id 是否正确。")
        else:
            print(f"❌ MySQL 连接失败：{str(e)[:200]}")
        return None
    except Exception as e:
        print(f"❌ {db_type} 连接失败：{str(e)[:200]}")
        return None

# 注意：移除了 reconnect_db 对 reconnect_db(db_type) 的依赖，
# 因为重连也需要 db_id，这在 test_sql_execution 中比较难传递，
# 建议由主程序控制连接生命周期。

def reconnect_db(db_type, specific_db_name=None):
    """数据库重连"""
    print(f"⚠️ {db_type} [{specific_db_name}] 连接失效，尝试重连...")
    return get_db_connection(db_type, specific_db_name)

def _execute_sql_without_timeout(sql, db_type, connection, cursor):
    """无超时执行SQL（供线程调用）"""
    try:
        if db_type == "PostgreSQL":
            cursor.execute(sql)
            if cursor.description:
                cursor.fetchall()
        elif db_type == "SQLite":
            cursor.execute(sql)
            connection.commit()
        else:  # MySQL
            cursor.execute(sql)
            if cursor.with_rows:
                cursor.fetchall()
        return {"status": "success", "error": None}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def test_sql_execution(sql, db_type, connection):
    """测试SQL执行（逻辑基本保持不变，但connection由外部传入）"""
    cursor = None
    execution_result = {"status": "failed", "error": "未知错误"}

    try:
        # 简单检查连接对象是否存在
        if not connection:
            return {"status": "failed", "error": f"{db_type} 连接对象为空"}
        
        # 注意：这里移除了内部的 reconnect_db 逻辑，
        # 因为 reconnect 需要 db_id，而此函数签名未传递 db_id。
        # 建议在调用此函数前确保 connection 是 fresh 的。
        
        # 创建游标
        cursor = connection.cursor()
        
        # 使用线程执行SQL，设置超时
        result = None
        thread = None
        
        def worker():
            nonlocal result
            result = _execute_sql_without_timeout(sql, db_type, connection, cursor)
        
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
        
        # 等待线程完成，超时则判定为死循环
        thread.join(timeout=SQL_EXECUTION_TIMEOUT)
        
        if thread.is_alive():
            # SQL执行超时，判定为死循环或查询过于复杂
            execution_result = {
                "status": "failed", 
                "error": f"SQL执行超时（超过{SQL_EXECUTION_TIMEOUT}秒），可能陷入死循环或查询过于复杂。请优化SQL，避免无限递归、笛卡尔积过大的关联查询、未加限制条件的大范围扫描等情况。"
            }
            print(f"⚠️ SQL执行超时，已终止执行")
            
            # 强制关闭游标和重置连接（避免资源泄漏）
            try:
                if db_type == "MySQL":
                    connection.reset_session()
                elif db_type == "PostgreSQL":
                    connection.rollback()
                elif db_type == "SQLite":
                    connection.rollback()
            except:
                pass
        else:
            # 线程正常结束，获取执行结果
            execution_result = result if result else {"status": "failed", "error": "执行结果未知"}
        
        return execution_result
    
    except MySQLError as e:
        err_msg = f"MySQL错误：{str(e)}"
        execution_result = {"status": "failed", "error": err_msg}
    except PgOperationalError as e:
        err_msg = f"PostgreSQL错误：{str(e)}"
        execution_result = {"status": "failed", "error": err_msg}
    except SQLiteError as e:
        err_msg = f"SQLite错误：{str(e)}"
        execution_result = {"status": "failed", "error": err_msg}
    except Exception as e:
        err_msg = f"未知错误：{str(e)}"
        execution_result = {"status": "failed", "error": err_msg}
    
    finally:
        # 确保游标关闭
        if cursor:
            try:
                cursor.close()
            except:
                pass
    
    # 截断过长错误信息
    if len(execution_result["error"]) > 500:
        execution_result["error"] = execution_result["error"][:500] + "..."
    
    return execution_result# magic_adapter.py
import re
import textwrap
from api_client import call_modelscope_api_single
from db_operations import test_sql_execution
from rag_retrieval import save_magic_guideline

class MagicAdapter:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def clean_sql(self, text: str) -> str:
        """从 LLM 输出中提取 SQL"""
        # 优先匹配 markdown sql
        match = re.search(r"```sql\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        # 其次匹配 markdown (无sql标记)
        match_generic = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match_generic:
            return match_generic.group(1).strip()
        
        return text.strip().replace("```", "").replace("sql", "")

    def propose_syntax_fix(self, question, dialect, incorrect_sql, error_msg, nl2_rewrite):
        """
        Magic Step A: 生成语法修正规则
        [Correction] 增加了 nl2_rewrite 作为 Schema 上下文，对应原 agent 中的 schema 参数
        """
        prompt = f"""
You are a {dialect} SQL Expert.
The following SQL failed to execute.

**Context**:
- Question: {question}
- Schema & Requirements: 
{nl2_rewrite}

- Incorrect SQL: {incorrect_sql}
- Error Message: {error_msg}

**Task**:
Analyze the error. Identify the specific syntax or function misuse.
Provide a specific "Syntax Correction Rule" to fix this. 
Do NOT write the full SQL yet. Just explain the rule in natural language.

**Output**:
A concise rule description.
"""
        try:
            return call_modelscope_api_single(prompt, dialect)
        except Exception as e:
            print(f"Magic Syntax Rule Gen Error: {e}")
            return "Ensure standard SQL syntax is used."

    def fix_sql_with_rule(self, question, dialect, incorrect_sql, rule, nl2_rewrite):
        """
        Magic Step B: 根据规则修复 SQL
        [Correction] 增加了 nl2_rewrite 作为 Schema 上下文
        """
        prompt = f"""
You are a {dialect} SQL Expert.

**Schema & Requirements**:
{nl2_rewrite}

**Task**:
Fix the following SQL based on the provided Syntax Rule.

- Question: {question}
- Incorrect SQL: {incorrect_sql}
- **Mandatory Syntax Rule**: {rule}

Output ONLY the corrected SQL wrapped in ```sql ... ```.
Ensure the SQL ends with a semicolon.
"""
        response = call_modelscope_api_single(prompt, dialect)
        return self.clean_sql(response)

    def generate_structured_guideline(self, case):
        """Magic Step D: 生成结构化指南 (保持原样，逻辑一致)"""
        prompt = f"""
Analyze the following SQL correction case and extract a syntax rule.
Case:
- Dialect: {case.get('dialect')}
- Question: {case.get('question')}
- Mistake: {case.get('incorrect_sql')}
- Error: {case.get('error_msg')}
- Fix: {case.get('corrected_sql')}

Format Output EXACTLY as follows (start/end with @homy@):

@homy@
<Category ID & Name>

<Sub-category>:
   1. Common Scenarios:
      <Description>
   2. Function Description:
      <Description>

    -- {case.get('dialect')}
       - Correct: {case.get('corrected_sql')}
       - Incorrect: {case.get('incorrect_sql')}
       - Reason: <Reason>
@homy@

Output ONLY the text.
"""
        response = call_modelscope_api_single(prompt, case.get('dialect'))
        # 简单的清洗逻辑
        if "@homy@" in response:
            return response.replace("```text", "").replace("```", "").strip()
        # 如果模型没输出 @homy@，尝试直接返回内容（容错）
        return response.strip()

    # 修改 run_magic_fix 方法签名，增加 logger 参数
    def run_magic_fix(self, question, nl2_rewrite, incorrect_sql, error_msg, dialect, logger=None):
        """
        执行 Magic 修复流程
        """
        print(f"\n🔮 [Magic Module] 启动! 正在尝试修复 {dialect} SQL...")
        
        # 1. 提出语法修正建议
        syntax_rule = self.propose_syntax_fix(question, dialect, incorrect_sql, error_msg, nl2_rewrite)
        print(f"🔮 [Magic] 生成修正规则: {syntax_rule[:100]}...")

        # 2. 根据规则修复 SQL
        fixed_sql = self.fix_sql_with_rule(question, dialect, incorrect_sql, syntax_rule, nl2_rewrite)
        print(f"🔮 [Magic] 修复后的 SQL: {fixed_sql[:100]}...")

        # [新增] 记录日志
        if logger:
            logger.log_magic_fix(syntax_rule, fixed_sql)

        # 3. 验证执行 (后续代码保持不变...)
        exec_result = test_sql_execution(fixed_sql, dialect, self.db_connection)

        if exec_result["status"] == "success":
            print(f"🔮 [Magic] 修复成功! SQL 可执行。")
            
            # 4. 生成并保存指南
            case_info = {
                "dialect": dialect,
                "question": question,
                "incorrect_sql": incorrect_sql,
                "error_msg": error_msg,
                "corrected_sql": fixed_sql,
                "syntax_rule": syntax_rule
            }
            try:
                guideline_text = self.generate_structured_guideline(case_info)
                if guideline_text:
                    print(f"🔮 [Magic] 生成指南，正在进行分类存储...")
                    # 传入 nl2_rewrite 用于计算相似度
                    save_magic_guideline(guideline_text, nl2_rewrite, dialect)
            except Exception as e:
                print(f"⚠️ [Magic] 指南保存失败: {e}")
            
            return "success", fixed_sql
        else:
            print(f"🔮 [Magic] 修复后执行依旧失败: {exec_result['error'][:100]}...")
            return "failed", fixed_sql

# qwen3-max main.py
import traceback
from config import OUTPUT_DIR, JSON_OUTPUT_PATH, MODEL_NAME, SQL_EXECUTION_TIMEOUT, SUPPORTED_DBS, RESULT_JSON_PATH, RULES_ROOT_DIR
from utils import ensure_dir_exists, load_db_rule_file, get_retrieval_items, parse_sql_result, get_final_sql, select_target_db
from api_client import call_modelscope_api_single
from db_operations import get_db_connection, test_sql_execution
from rag_retrieval import secondary_rag_retrieval
from result_saver import save_json_results, save_text_results, save_final_report
# 新增导入
from prompt_builder import build_prompt, build_logic_fix_prompt 
from semantic_checker import verify_sql_logic, save_semantic_failure
from magic_adapter import MagicAdapter
# [新增] 导入日志模块
from process_logger import ProcessLogger 
def main():
    """主流程：生成→执行→失败修正(语法)→成功后验证逻辑→逻辑修正→保存结果"""
    try:
        # 初始化目录
        ensure_dir_exists(OUTPUT_DIR)
        
        # 打印程序信息
        print("=== NL2SQL批量生成+执行验证工具（多库动态连接版）===")
        print(f"使用模型: {MODEL_NAME}")
        print(f"支持数据库: {', '.join(SUPPORTED_DBS)}")
        print(f"数据源路径: {RESULT_JSON_PATH}")
        print(f"SQL执行超时时间: {SQL_EXECUTION_TIMEOUT}秒")
        
        # 步骤1：选择目标数据库 (SQL方言)
        target_db_type = select_target_db()
        
        # 步骤2：加载规则文件
        print(f"\n正在加载{target_db_type}完整规则文件...")
        db_rule_content = load_db_rule_file(target_db_type)
        
        # 步骤4：获取多库检索结果项
        print("\n正在加载多库检索结果项...")
        retrieval_items = get_retrieval_items()
        
        # 步骤5：逐个处理
        final_results = []
        total_items = len(retrieval_items)
        
        for idx, item in enumerate(retrieval_items):
            item_index = item["index"]
            question = item["question"]
            nl2_rewrite = item["nl2_rewrite"]
            db_id = item.get("db_id")  # [新增] 获取 db_id
            
            print(f"\n==================================================")
            print(f"正在处理第 {item_index}/{total_items} 个项目")
            print(f"Database ID: {db_id}")
            print(f"Target Dialect: {target_db_type}")
            print(f"==================================================")
            
            # [新增] --- 动态数据库连接逻辑 ---
            current_db_connection = None
            magic_adapter = None
            
            if db_id:
                # 尝试连接具体的数据库 (例如: bird, smart_home...)
                current_db_connection = get_db_connection(target_db_type, specific_db_name=db_id)
                
                if current_db_connection:
                    # 初始化 Magic 适配器 (绑定当前连接)
                    magic_adapter = MagicAdapter(current_db_connection)
                else:
                    print(f"⚠️ 无法连接到数据库 '{db_id}'，后续执行验证环节将跳过")
            else:
                print(f"⚠️ 当前数据项缺少 db_id，无法建立连接")

            # 初始化项目结果
            item_result = {
                "index": item["index"],
                "question": item["question"],
                "nl2_rewrite": item["nl2_rewrite"],
                "db_id": db_id, 
                "question_id": item.get("question_id", None),
                "difficulty": item.get("difficulty", None),
                "first_generated_sql": "",
                "first_execution_status": "",
                "first_error_msg": None,
                "second_generated_sql": None,
                "second_execution_status": None,
                "second_error_msg": None,
                "magic_generated_sql": None,
                "magic_execution_status": None, 
                "final_execution_status": "",
                "secondary_rag_content": None,
                "execution_timeout": False,
                "target_db_type": target_db_type
            }
            
            # 用于追踪当前最好的SQL
            current_best_sql = ""
            current_execution_status = "failed"
            
            try:
                # ================= 1. 首次生成 & 执行 =================
                print(f"\n1. 首次生成SQL...")
                prompt_first = build_prompt(
                    retrieval_item=item,
                    target_db_type=target_db_type,
                    db_rule_content=db_rule_content
                )
                sql_result_first = call_modelscope_api_single(prompt_first, target_db_type)
                parsed_sql_first = parse_sql_result(sql_result_first, target_db_type)
                first_sql = parsed_sql_first[target_db_type]
                
                if not first_sql:
                    print(f"❌ 首次生成失败：未获取到有效SQL")
                    item_result["first_generated_sql"] = "生成失败"
                    item_result["final_execution_status"] = "skip"
                else:
                    item_result["first_generated_sql"] = first_sql
                    print(f"首次生成SQL：{first_sql[:100]}...")
                    
                    if not current_db_connection:
                        item_result["first_execution_status"] = "skip"
                        item_result["final_execution_status"] = "skip"
                    else:
                        print(f"\n2. 执行首次生成的SQL (DB: {db_id})...")
                        exec_result_first = test_sql_execution(first_sql, target_db_type, current_db_connection)
                        
                        item_result["first_execution_status"] = exec_result_first["status"]
                        item_result["first_error_msg"] = exec_result_first["error"]
                        
                        if exec_result_first["error"] and ("死循环" in exec_result_first["error"] or "超时" in exec_result_first["error"]):
                            item_result["execution_timeout"] = True
                        
                        if exec_result_first["status"] == "success":
                            print(f"✅ 首次执行成功")
                            current_best_sql = first_sql
                            current_execution_status = "success"
                            item_result["final_execution_status"] = "success"
                        else:
                            print(f"❌ 首次执行失败：{exec_result_first['error'][:100]}...")

                # ================= 2. 语法错误修正 (如果首次执行失败) =================
                if current_execution_status != "success" and item_result["final_execution_status"] != "skip":
                    print(f"\n3. 启动语法错误修正流程...")
                    
                    print(f"3.1 执行错误RAG检索...")
                    secondary_rag_content = secondary_rag_retrieval(
                        question=question,
                        error_msg=item_result["first_error_msg"],
                        db_type=target_db_type
                    )
                    item_result["secondary_rag_content"] = secondary_rag_content
                    
                    prompt_second = build_prompt(
                        retrieval_item=item,
                        target_db_type=target_db_type,
                        secondary_rag_content=secondary_rag_content,
                        error_msg=item_result["first_error_msg"],
                        first_sql=item_result["first_generated_sql"]
                    )
                    
                    sql_result_second = call_modelscope_api_single(prompt_second, target_db_type)
                    parsed_sql_second = parse_sql_result(sql_result_second, target_db_type)
                    second_sql = parsed_sql_second[target_db_type]
                    
                    if second_sql:
                        item_result["second_generated_sql"] = second_sql
                        print(f"二次生成SQL：{second_sql[:100]}...")
                        
                        print(f"3.4 执行二次生成的SQL...")
                        exec_result_second = test_sql_execution(second_sql, target_db_type, current_db_connection)
                        
                        item_result["second_execution_status"] = exec_result_second["status"]
                        item_result["second_error_msg"] = exec_result_second["error"]
                        item_result["final_execution_status"] = exec_result_second["status"]
                        
                        if exec_result_second["status"] == "success":
                            print(f"✅ 二次执行成功")
                            current_best_sql = second_sql
                            current_execution_status = "success"
                        else:
                            print(f"❌ 二次执行失败：{exec_result_second['error'][:100]}...")
                    else:
                        print(f"❌ 二次生成失败：未获取到有效SQL")

                # ================= 3. Magic 模块调用 =================
                if current_execution_status != "success" and item_result["final_execution_status"] != "skip":
                    if magic_adapter and item_result["second_generated_sql"]:
                        print(f"\n--------------------------------------------------")
                        print(f"⚠️ Standard RAG 修正失败，激活 Magic Module...")
                        print(f"--------------------------------------------------")
                        
                        magic_status, magic_sql = magic_adapter.run_magic_fix(
                            question=item["question"],
                            nl2_rewrite=item["nl2_rewrite"],
                            incorrect_sql=item_result["second_generated_sql"],
                            error_msg=item_result["second_error_msg"],
                            dialect=target_db_type
                        )
                        
                        item_result["magic_generated_sql"] = magic_sql
                        item_result["magic_execution_status"] = magic_status
                        
                        if magic_status == "success":
                            current_best_sql = magic_sql
                            current_execution_status = "success"
                            item_result["final_execution_status"] = "success"
                    else:
                        print("⚠️ 无法激活 Magic 模块 (数据库连接缺失或无前序SQL)")

                # ================= 4. 语义一致性验证 & 逻辑修正 =================
                if current_execution_status == "success" and current_best_sql:
                    print(f"\n4. 正在进行语义一致性验证...")
                    
                    is_pass, fail_reason = verify_sql_logic(
                        item["question"], item["nl2_rewrite"], current_best_sql, target_db_type
                    )
                    
                    if is_pass:
                        print(f"✅ 语义验证通过：SQL逻辑符合需求")
                        pass 
                    else:
                        print(f"⚠️ 语义验证不通过：{fail_reason}")
                        print(f"   -> 尝试进行逻辑修正 (第3轮生成)...")
                        
                        prompt_logic_fix = build_logic_fix_prompt(
                            question=item["question"],
                            nl2_rewrite=item["nl2_rewrite"],
                            wrong_sql=current_best_sql,
                            analysis_reason=fail_reason,
                            target_db_type=target_db_type
                        )
                        
                        try:
                            # ========================================================
                            # [插入/修改的位置 START]
                            # ========================================================
                            sql_result_fix = call_modelscope_api_single(prompt_logic_fix, target_db_type)
                            
                            # 【新增】打印原始返回内容，看看到底生成了什么
                            print(f"\n[DEBUG] 逻辑修正原始返回内容:\n{sql_result_fix}\n[DEBUG END]")
                            
                            parsed_sql_fix = parse_sql_result(sql_result_fix, target_db_type)
                            # 使用 .get 更加安全
                            fixed_sql = parsed_sql_fix.get(target_db_type, "")
                            # ========================================================
                            # [插入/修改的位置 END]
                            # ========================================================
                            
                            if fixed_sql:
                                print(f"   逻辑修正SQL: {fixed_sql[:100]}...")
                                
                                exec_result_fix = test_sql_execution(fixed_sql, target_db_type, current_db_connection)
                                
                                if exec_result_fix["status"] == "success":
                                    print(f"✅ 逻辑修正后执行成功")
                                    item_result["second_generated_sql"] = fixed_sql 
                                    item_result["second_execution_status"] = "success"
                                    item_result["final_execution_status"] = "success"
                                    item_result["second_error_msg"] = None 
                                    
                                    save_semantic_failure(item_index, question, nl2_rewrite, current_best_sql, fail_reason, fixed_sql)
                                else:
                                    print(f"❌ 逻辑修正后执行失败（语法错误）：{exec_result_fix['error'][:100]}...")
                                    save_semantic_failure(
                                        item_index, question, nl2_rewrite, current_best_sql, 
                                        f"{fail_reason} | 尝试修正但引入了执行错误: {exec_result_fix['error']}", 
                                        fixed_sql
                                    )
                            else:
                                print(f"❌ 逻辑修正生成失败：未获取到有效SQL")
                                
                        except Exception as e:
                            print(f"❌ 逻辑修正过程异常: {str(e)}")
                            save_semantic_failure(item_index, question, nl2_rewrite, current_best_sql, f"{fail_reason} | 修正过程API异常: {str(e)}")
                else:
                    pass

                final_results.append(item_result)
                
            except Exception as e:
                error_detail = str(e)[:100]
                print(f"\n❌ 项目处理异常：{error_detail}...")
                item_result.update({
                    "first_execution_status": "error",
                    "final_execution_status": "error",
                    "error_msg": error_detail
                })
                final_results.append(item_result)
                continue
            
            finally:
                if current_db_connection:
                    try:
                        current_db_connection.close()
                    except Exception as e:
                        print(f"⚠️ 关闭连接异常: {e}")
        
        # 步骤6：保存结果
        print(f"\n==================================================")
        print(f"所有项目处理完成，正在保存结果...")
        
        all_json_results = []
        for r in final_results:
            final_sql = get_final_sql(r, target_db_type)
            all_json_results.append({
                "question": r["question"],
                "nl2_rewrite": r["nl2_rewrite"],
                "question_id": r.get("question_id"),
                "db_id": r.get("db_id"), 
                "final_execution_status": r["final_execution_status"],
                "difficulty": r.get("difficulty"),
                target_db_type: final_sql
            })
        
        save_json_results(
            all_json_results=all_json_results,
            output_path=JSON_OUTPUT_PATH,
            target_db_type=target_db_type
        )
        
        save_text_results(all_json_results, OUTPUT_DIR, target_db_type)
        save_final_report(final_results)
        
        print(f"\n🎉 流程全部完成！")
        
    except Exception as e:
        print(f"\n❌ 程序执行出错：{str(e)}")
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()# process_logger.py
import os
import datetime

class ProcessLogger:
    def __init__(self, output_dir):
        # 创建日志目录
        self.log_dir = os.path.join(output_dir, "process_logs")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # 以时间戳命名日志文件
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.log_dir, f"run_log_{timestamp}.md")
        
        # 初始化文件头
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"# NL2SQL Execution Process Log\n")
            f.write(f"**Start Time:** {timestamp}\n\n")
            f.write("---\n")

    def _write(self, content):
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(content + "\n")

    def start_question(self, index, question_id, db_id, question, nl2_rewrite):
        content = f"\n# 🟢 Question Process [Index: {index} | ID: {question_id}]\n"
        content += f"**Database:** `{db_id}`\n\n"
        content += f"**Original Question:**\n> {question}\n\n"
        content += f"**NL2SQL Rewrite (Schema Context):**\n> {nl2_rewrite}\n"
        content += "\n---"
        self._write(content)

    def log_phase(self, phase_name):
        self._write(f"\n## 🔹 Phase: {phase_name}")

    def log_rag_content(self, content):
        self._write(f"\n### 📚 RAG Retrieval Content")
        self._write(f"```text\n{content}\n```")

    def log_prompt(self, prompt_type, prompt_content):
        self._write(f"\n### 📝 Prompt Constructed ({prompt_type})")
        self._write(f"```markdown\n{prompt_content}\n```")

    def log_llm_response(self, response_content):
        self._write(f"\n### 🤖 LLM Raw Response")
        self._write(f"```text\n{response_content}\n```")

    def log_sql_execution(self, sql, status, error_msg=None):
        self._write(f"\n### ⚙️ SQL Execution")
        self._write(f"- **SQL:** `{sql}`")
        if status == "success":
            self._write(f"- **Status:** ✅ SUCCESS")
        else:
            self._write(f"- **Status:** ❌ FAILED")
            self._write(f"- **Error:** `{error_msg}`")

    def log_semantic_check(self, is_pass, reason, fixed_sql=None):
        self._write(f"\n### 🧠 Semantic & Logic Check")
        if is_pass:
            self._write(f"- **Result:** ✅ PASS")
        else:
            self._write(f"- **Result:** ⚠️ FAIL")
            self._write(f"- **Reason:** {reason}")
            if fixed_sql:
                self._write(f"- **Logic Fix Proposed SQL:**\n```sql\n{fixed_sql}\n```")

    def log_magic_fix(self, syntax_rule, fixed_sql):
        self._write(f"\n### 🔮 Magic Module Fix")
        self._write(f"- **Generated Rule:** {syntax_rule}")
        self._write(f"- **Fixed SQL:**\n```sql\n{fixed_sql}\n```")

    def end_question(self, final_status):
        self._write(f"\n**🏁 Final Status:** {final_status}")
        self._write("\n---\n")# prompt_builder.py
import textwrap
from typing import Dict, Any, Optional
from utils import truncate_content
from config import SUPPORTED_DBS

def build_prompt(
    retrieval_item: Dict[str, Any], 
    target_db_type: str, 
    db_rule_content: Optional[str] = None,
    secondary_rag_content: Optional[str] = None,
    error_msg: Optional[str] = None,
    first_sql: Optional[str] = None
) -> str:
    """
    构造 Prompt（支持首次生成和二次修正 - 针对执行报错）
    
    核心优化：
    1. 首次生成：保留多库语法参考；二次生成：移除首次检索语法，聚焦复用首次SQL正确语法+修正错误
    2. 突出 nl2_rewrite 的核心价值（功能、表/列、返回内容）
    """
    
    # 标记是否为二次生成（基于执行报错的修正）
    is_secondary = bool(secondary_rag_content and error_msg and first_sql)
    
    # --- 第一步：处理语法参考部分 ---
    grammar_section = ""
    if not is_secondary:
        # 首次生成：保留原多库语法参考逻辑
        retrieval_results = retrieval_item.get("retrieval_results", {})
        
        # 1. 目标数据库语法
        target_grammar = retrieval_results.get(target_db_type, "").strip()
        target_grammar_content = target_grammar if target_grammar else "无相关语法片段"
        
        target_grammar_section = textwrap.dedent(f"""\
            ### 1. 目标数据库语法参考（{target_db_type}，可直接使用）
            {target_grammar_content}
            
            """)
        
        # 2. 其他数据库语法
        other_dbs_grammar = []
        for db in SUPPORTED_DBS:
            if db == target_db_type:
                continue
            grammar = retrieval_results.get(db, "").strip()
            grammar_content = grammar if grammar else "无相关语法片段"
            other_dbs_grammar.append(f"#### {db}（非目标数据库，勿直接使用）\n{grammar_content}")
        
        other_dbs_joined = "\n\n".join(other_dbs_grammar)
        other_grammar_section = textwrap.dedent(f"""\
            ### 2. 其他数据库语法参考（仅参考通用逻辑，避免混用非通用语法）
            {other_dbs_joined}
            
            """)
        grammar_section = target_grammar_section + other_grammar_section
    else:
        # 二次生成：移除首次检索语法，替换为首次SQL的语法复用说明
        grammar_section = textwrap.dedent(f"""\
            ### 1. 首次生成SQL复用说明
            #### 1.1 上一次生成的SQL语句：
            {first_sql}

            #### 1.2 复用规则：
            请完全复用上述SQL语句中**语法正确的部分**（如表名、列名、函数调用、关联逻辑等），仅修改导致以下错误的部分：
            {error_msg}
            
            """)

    # --- 第二步：构建规则文件/错误修正参考部分 ---
    rule_section = ""
    if is_secondary:
        # 二次生成：仅保留针对性语法参考
        secondary_rag_content_val = secondary_rag_content if secondary_rag_content else "无针对性语法片段"
        rule_section = textwrap.dedent(f"""\
            ### 2. 错误修正针对性语法参考
            #### 2.1 错误核心原因：
            {error_msg}

            #### 2.2 修正需遵循的语法规则（必须严格遵循）：
            {secondary_rag_content_val}
            
            """)
    else:
        # 首次生成：保留完整规则文件逻辑
        db_rule_content_val = db_rule_content if db_rule_content else "无完整语法规则"
        rule_section = textwrap.dedent(f"""\
            ### 3. 完整语法规则{target_db_type}，首次生成需严格遵循下面的规则内容，不要遗漏细节:
            {db_rule_content_val}
            
            """)

    # --- 第三步：拼接问题需求部分 ---
    # 动态计算章节号：二次生成时前两部分占了 1,2，所以这里是 3；首次生成前两部分占了 1,2,3，所以这里是 4
    req_section_num = 3 if is_secondary else 4
    
    requirement_section = textwrap.dedent(f"""\
        ### {req_section_num}. 问题核心需求（关键！以下详细描述是SQL生成的唯一依据）
        #### 原始问题：
        {retrieval_item.get("question", "")}

        #### 核心功能&数据说明（必须完全遵循）：
        {retrieval_item.get("nl2_rewrite", "")}

        #### 重要提示：
        上述「核心功能&数据说明」中包含：
        1. 你需要实现的**核心业务功能**；
        2. 必须使用的**表名/列名**（需要从上述字段中找寻），不要将列名弄混,比如CreaionDate当成CreationDate；
        3. 需要返回的**字段/数据范围/计算逻辑**；
        请严格基于此内容生成/修正SQL，不得偏离任何细节。
        
        """)

    # --- 第四步：生成要求 ---
    # 动态计算章节号
    gen_rule_num = req_section_num + 1
    
    if not is_secondary:
        # 首次生成要求
        generate_rules_list = [
            f"1. 必须生成严格符合{target_db_type}语法规范的SQL，优先使用目标数据库语法参考，其次参考完整语法规则；",
            "2. 可借鉴其他数据库的通用语法逻辑，但严禁直接使用非目标数据库的特有语法（如函数、关键字差异）；",
            "3. 确保SQL准确实现「核心功能&数据说明」中的所有需求，避免死循环、笛卡尔积过大等性能问题，必要时添加LIMIT/OFFSET；",
            f"4. 输出格式严格按照以下结构，不要任何额外内容，SQL语句结尾必须加分号：\n\n### {target_db_type}\n[{target_db_type} SQL语句]"
        ]
    else:
        # 二次生成要求
        generate_rules_list = [
            f"1. 必须生成严格符合{target_db_type}语法规范的SQL，优先复用首次SQL中正确的语法部分；",
            "2. 仅修改导致错误的部分，不得改变首次SQL中符合「核心功能&数据说明」的业务逻辑；",
            "3. 严格遵循「核心功能&数据说明」中的所有要求（功能、表/列、返回内容），不得偏离；",
            f"4. 基于「错误修正针对性语法参考」优化SQL，解决以下错误：{error_msg}；",
            f"5. 输出格式严格按照以下结构，不要任何额外内容，SQL语句结尾必须加分号：\n### {target_db_type}\n[{target_db_type} SQL语句]"
        ]

    requirement_section += f"### {gen_rule_num}. 生成要求\n" + "\n".join(generate_rules_list) + "\n"

    # 拼接完整Prompt并截断
    full_prompt = grammar_section + rule_section + requirement_section
    full_prompt = truncate_content(full_prompt, max_length=210000)
    
    return full_prompt.strip()

# prompt_builder.py
import textwrap
from typing import Dict, Any, Optional
from utils import truncate_content
from config import SUPPORTED_DBS

# ... (build_prompt 函数保持不变) ...

def build_prompt(
    retrieval_item: Dict[str, Any], 
    target_db_type: str, 
    db_rule_content: Optional[str] = None,
    secondary_rag_content: Optional[str] = None,
    error_msg: Optional[str] = None,
    first_sql: Optional[str] = None
) -> str:
    # ... (原有代码保持不变) ...
    # 为了节省篇幅，这里省略 build_prompt 的具体实现，请保留你原有的代码
    # 标记是否为二次生成（基于执行报错的修正）
    is_secondary = bool(secondary_rag_content and error_msg and first_sql)
    
    # --- 第一步：处理语法参考部分 ---
    grammar_section = ""
    if not is_secondary:
        retrieval_results = retrieval_item.get("retrieval_results", {})
        target_grammar = retrieval_results.get(target_db_type, "").strip()
        target_grammar_content = target_grammar if target_grammar else "无相关语法片段"
        
        target_grammar_section = textwrap.dedent(f"""\
            ### 1. 目标数据库语法参考（{target_db_type}，可直接使用）
            {target_grammar_content}
            
            """)
        
        other_dbs_grammar = []
        for db in SUPPORTED_DBS:
            if db == target_db_type:
                continue
            grammar = retrieval_results.get(db, "").strip()
            grammar_content = grammar if grammar else "无相关语法片段"
            other_dbs_grammar.append(f"#### {db}（非目标数据库，勿直接使用）\n{grammar_content}")
        
        other_dbs_joined = "\n\n".join(other_dbs_grammar)
        other_grammar_section = textwrap.dedent(f"""\
            ### 2. 其他数据库语法参考（仅参考通用逻辑，避免混用非通用语法）
            {other_dbs_joined}
            
            """)
        grammar_section = target_grammar_section + other_grammar_section
    else:
        grammar_section = textwrap.dedent(f"""\
            ### 1. 首次生成SQL复用说明
            #### 1.1 上一次生成的SQL语句：
            {first_sql}

            #### 1.2 复用规则：
            请完全复用上述SQL语句中**语法正确的部分**（如表名、列名、函数调用、关联逻辑等），仅修改导致以下错误的部分：
            {error_msg}
            
            """)

    # --- 第二步：构建规则文件/错误修正参考部分 ---
    rule_section = ""
    if is_secondary:
        secondary_rag_content_val = secondary_rag_content if secondary_rag_content else "无针对性语法片段"
        rule_section = textwrap.dedent(f"""\
            ### 2. 错误修正针对性语法参考
            #### 2.1 错误核心原因：
            {error_msg}

            #### 2.2 修正需遵循的语法规则（必须严格遵循）：
            {secondary_rag_content_val}
            
            """)
    else:
        db_rule_content_val = db_rule_content if db_rule_content else "无完整语法规则"
        rule_section = textwrap.dedent(f"""\
            ### 3. 完整语法规则{target_db_type}，首次生成需严格遵循下面的规则内容，不要遗漏细节:
            {db_rule_content_val}
            
            """)

    # --- 第三步：拼接问题需求部分 ---
    req_section_num = 3 if is_secondary else 4
    
    requirement_section = textwrap.dedent(f"""\
        ### {req_section_num}. 问题核心需求（关键！以下详细描述是SQL生成的唯一依据）
        #### 原始问题：
        {retrieval_item.get("question", "")}

        #### 核心功能&数据说明（必须完全遵循）：
        {retrieval_item.get("nl2_rewrite", "")}

        #### 重要提示：
        上述「核心功能&数据说明」中包含：
        1. 你需要实现的**核心业务功能**；
        2. 必须使用的**表名/列名**（需要从上述字段中找寻），不要将列名弄混,比如CreaionDate当成CreationDate；
        3. 需要返回的**字段/数据范围/计算逻辑**；
        请严格基于此内容生成/修正SQL，不得偏离任何细节。
        
        """)

    # --- 第四步：生成要求 ---
    gen_rule_num = req_section_num + 1
    
    if not is_secondary:
        generate_rules_list = [
            f"1. 必须生成严格符合{target_db_type}语法规范的SQL，优先使用目标数据库语法参考，其次参考完整语法规则；",
            "2. 可借鉴其他数据库的通用语法逻辑，但严禁直接使用非目标数据库的特有语法（如函数、关键字差异）；",
            "3. 确保SQL准确实现「核心功能&数据说明」中的所有需求，避免死循环、笛卡尔积过大等性能问题，必要时添加LIMIT/OFFSET；",
            f"4. 输出格式严格按照以下结构，不要任何额外内容，SQL语句结尾必须加分号：\n\n### {target_db_type}\n[{target_db_type} SQL语句]"
        ]
    else:
        generate_rules_list = [
            f"1. 必须生成严格符合{target_db_type}语法规范的SQL，优先复用首次SQL中正确的语法部分；",
            "2. 仅修改导致错误的部分，不得改变首次SQL中符合「核心功能&数据说明」的业务逻辑；",
            "3. 严格遵循「核心功能&数据说明」中的所有要求（功能、表/列、返回内容），不得偏离；",
            f"4. 基于「错误修正针对性语法参考」优化SQL，解决以下错误：{error_msg}；",
            f"5. 输出格式严格按照以下结构，不要任何额外内容，SQL语句结尾必须加分号：\n### {target_db_type}\n[{target_db_type} SQL语句]"
        ]

    requirement_section += f"### {gen_rule_num}. 生成要求\n" + "\n".join(generate_rules_list) + "\n"

    full_prompt = grammar_section + rule_section + requirement_section
    full_prompt = truncate_content(full_prompt, max_length=210000)
    
    return full_prompt.strip()

def build_semantic_check_prompt(question, nl2_rewrite, sql, db_type):
    """
    构造语义验证Prompt (严格分块审计版)
    
    针对 nl2_rewrite 的四个特定字段进行逻辑验收：
    1. --- Source & Joins        -> 检查 SQL 的表引用、别名使用、连接字段是否正确。
    2. --- Filters               -> 检查 SQL 的 WHERE 条件是否严格一致（严禁多加或漏加）。
    3. --- Aggregation & Computation -> 检查 SQL 的核心计算逻辑（函数）和分组。
    4. --- Return                -> 检查 SQL 的 SELECT 输出列。
    """
    return textwrap.dedent(f"""\
        ### 任务：SQL 语义一致性严格审计
        
        你是一名代码审计专家。你的唯一任务是验证生成的 SQL 是否**严格遵循** "核心需求说明书 (nl2_rewrite)" 的定义。
        
        #### 1. 核心需求说明书 (nl2_rewrite) - 绝对标准
        请注意以下四个字段的定义，这是唯一的真理：
        --------------------------------------------------
        {nl2_rewrite}
        --------------------------------------------------
        
        #### 2. 待验证的 SQL ({db_type})
        {sql}
        
        #### 3. 审计核心规则 (Strict Check)
        请按照以下步骤逐一检查，任何一项不符都视为 FAIL：
        
        **步骤 1: 检查表与连接 (Source & Joins)**
        *   SQL 中 `FROM` 和 `JOIN` 使用的表名必须存在于 `--- Source & Joins` 中。
        *   检查 SQL 中使用的**列名**是否归属于正确的表（特别是多表关联时，严禁张冠李戴）。
        
        **步骤 2: 检查筛选条件 (Filters) - [零容忍]**
        *   **严格匹配**：SQL 的 `WHERE` 子句必须包含 `--- Filters` 中列出的**所有**条件。
        *   **禁止私加**：绝对禁止添加 `--- Filters` 中未提及的额外筛选条件。
        *   **禁止遗漏**：绝对禁止遗漏任何条件。
        *   **数值/逻辑精确**：比较符号 (>, <, =, LIKE) 和具体数值必须一致。
        
        **步骤 3: 检查核心功能 (Aggregation & Computation)**
        *   SQL 是否正确实现了 `--- Aggregation & Computation` 要求的计算逻辑（如 `COUNT`, `SUM`, `AVG`, `MAX` 或 `DISTINCT`）？
        *   如果涉及分组，`GROUP BY` 的字段是否符合要求？
        
        **步骤 4: 检查输出结果 (Return)**
        *   SQL 的 `SELECT` 列表返回的字段，必须与 `--- Return` 中要求的输出内容完全对应。
        
        #### 4. 输出格式
        请仅返回一个纯 JSON 对象，**严禁**包含 Markdown 格式符：
        {{
            "status": "PASS" 或 "FAIL",
            "reason": "如果为FAIL，请指明是哪个板块不符。例如：'Filters错误：SQL遗漏了对 date > 2020 的筛选' 或 'Source错误：列名 usage 归属错误，应属于表 T1'。如果为PASS，请保持为空字符串"
        }}
        """)

def build_logic_fix_prompt(question, nl2_rewrite, wrong_sql, analysis_reason, target_db_type):
    """
    构造逻辑修正Prompt (分块修复版)
    """
    return textwrap.dedent(f"""\
        ### 任务：修复 SQL 逻辑缺陷
        
        上一轮生成的 SQL 在语义审计中被判定为不合格。请严格基于 `nl2_rewrite` 的四个字段重新编写 SQL。
        
        #### 1. 核心需求说明书 (标准答案)
        --------------------------------------------------
        {nl2_rewrite}
        --------------------------------------------------
        *   **Source & Joins**: 规定了表名、列名和 Join 逻辑。
        *   **Filters**: 规定了 `WHERE` 必须包含（且仅包含）的条件。
        *   **Aggregation & Computation**: 规定了 `GROUP BY` 和聚合函数。
        *   **Return**: 规定了 `SELECT` 返回的列。
        
        #### 2. 错误 SQL
        {wrong_sql}
        
        #### 3. 审计意见 (失败原因)
        {analysis_reason}
        
        #### 4. 修复指令
        1.  **修正 Filters**：对照 `--- Filters`，删除多余条件，补全遗漏条件，修正错误的表列引用。
        2.  **修正 Return**：对照 `--- Return`，确保 `SELECT` 的列名和数量一致。
        3.  **修正 Logic**：对照 `--- Aggregation & Computation`，修正聚合方式。
        4.  **修正 Source**：对照 `--- Source & Joins`，确保使用了正确的表名和列名。
        
        **输出要求（非常重要）**：
        1. 直接输出修正后的 SQL 代码。
        2. **不要**输出任何解释、道歉或分析过程（如 "Sure, here is the fixed SQL..."）。
        3. 必须包含在 Markdown 代码块中。
        4. SQL 必须以分号结尾。
        
        格式示例：
        ### {target_db_type}
        ```sql
        SELECT ... ;
        ```
        """)# rag_retrieval.py
import re
from config import RULES_ROOT_DIR, FUNCTIONAL_ROOT_DIR, DB_TYPE_TO_RULE_FILE, MAGIC_SIMILARITY_THRESHOLD # <--- 导入阈值
import os
import numpy as np
# 导入RAG相关组件
try:
    from rag_fixed_chunk import (
        embedding_model,
        HomyMarkerSplitter,
        Chroma,
        format_retrieval_result
    )
    from langchain_core.output_parsers import StrOutputParser
    from langchain_community.document_loaders import TextLoader
    from operator import itemgetter
    from langchain_core.runnables import RunnablePassthrough
except ImportError as e:
    raise RuntimeError(f"无法导入rag_fixed_chunk.py中的组件，请检查路径") from e

def secondary_rag_retrieval(question, error_msg, db_type):
    """
    二次RAG检索（返回1个最相关chunk）  # 注释修改：2→1
    适配rag_fixed_chunk.py的实际实现：单文件加载+临时向量库+固定分割器
    """
    try:
        # 1. 构建检索查询（融合问题+错误信息，提升相关性）
        retrieval_query = f"问题：{question} | SQL执行错误：{error_msg} | 关键词：死循环、超时、查询优化、避免笛卡尔积、递归查询限制、索引优化、查询性能"
        print(f"二次检索查询：{retrieval_query[:100]}...")
        
        # 2. 获取目标数据库的规则文件路径
        rule_filename = DB_TYPE_TO_RULE_FILE[db_type]
        rule_file_path = os.path.join(RULES_ROOT_DIR, rule_filename)
        if not os.path.exists(rule_file_path):
            print(f"⚠️ 规则文件不存在：{rule_file_path}")
            return "无相关语法参考"
        
        # 3. 加载单个规则文件
        loader = TextLoader(rule_file_path, encoding='utf-8')
        docs = loader.load()
        if not docs:
            print(f"⚠️ 规则文件{rule_file_path}加载后无内容")
            return "无相关语法参考"
        
        # 4. 用HomyMarkerSplitter分割文档
        text_splitter = HomyMarkerSplitter()
        split_docs = text_splitter.split_documents(docs)
        print(f"规则文件分割为 {len(split_docs)} 个文档块")
        
        # 校验文档块数量：从2→1
        if len(split_docs) < 1:
            print(f"⚠️ 文档块数量不足1个，仅获取{len(split_docs)}个")
        
        # 5. 创建临时向量库
        temp_vector_store = Chroma(
            embedding_function=embedding_model,
            persist_directory=None  # 临时向量库，退出即销毁
        )
        temp_vector_store.add_documents(split_docs)
        
        # 6. 构建检索器（强制返回1个最相关chunk）  # 核心修改：k=1
        temp_retriever = temp_vector_store.as_retriever(
            search_kwargs={"k": 1}
        )
        
        # 7. 构建检索链
        temp_chain = (
            {"question": RunnablePassthrough()}
            | RunnablePassthrough.assign(context=itemgetter("question") | temp_retriever)
            | format_retrieval_result
            | StrOutputParser()
        )
        
        # 8. 执行检索
        retrieval_result = temp_chain.invoke(retrieval_query)
        
        # 9. 处理检索结果
        if "No relevant content retrieved" in retrieval_result:
            # 返回格式调整：仅保留1个参考块
            return "=== 相关语法参考 1 ===\n无相关语法参考"
        
        # 解析检索结果中的chunk
        chunk_pattern = r'=== Relevant Chunk (\d+): (.*?) ===\n([\s\S]*?)(?=\n=== |$)'
        matches = re.findall(chunk_pattern, retrieval_result, re.DOTALL)
        
        # 格式化前1个chunk  # 修改：[:2]→[:1]
        formatted_chunks = []
        for i, (chunk_idx, title, content) in enumerate(matches[:1], 1):
            truncated_content = content[:8000] + "..." if len(content) > 8000 else content
            formatted_chunks.append(
                f"=== 相关语法参考 {i}（{title}）===\n{truncated_content.strip()}"
            )
        
        # 不足1个时补充空chunk  # 修改：补到1个而非2个
        while len(formatted_chunks) < 1:
            formatted_chunks.append(f"=== 相关语法参考 {len(formatted_chunks)+1} ===\n无更多相关语法参考")
        
        final_retrieval = "\n\n".join(formatted_chunks)
        print(f"二次检索结果（前200字符）：{final_retrieval[:200]}...")
        return final_retrieval
    
    except Exception as e:
        error_detail = str(e)[:200]
        print(f"⚠️ 二次RAG检索失败：{error_detail}...")
        # 异常返回格式调整：仅1个参考块
        return (
            f"=== 相关语法参考 1 ===\n检索失败：{error_detail}（无相关语法参考）"
        )
        
def calculate_cosine_similarity(text1, text2):
    """计算两段文本的余弦相似度"""
    try:
        # 使用 embedding_model (来自 rag_fixed_chunk)
        vec1 = embedding_model.embed_query(text1)
        vec2 = embedding_model.embed_query(text2)
        
        # 计算余弦相似度
        dot_product = np.dot(vec1, vec2)
        norm_a = np.linalg.norm(vec1)
        norm_b = np.linalg.norm(vec2)
        return dot_product / (norm_a * norm_b)
    except Exception as e:
        print(f"⚠️ 相似度计算失败: {e}")
        return 0.0

def save_magic_guideline(guideline_text, nl2_rewrite, db_type):
    """
    根据相似度判断并保存 Magic 生成的 Guideline
    """
    if not guideline_text:
        return

    # 1. 计算 Guideline 内容与 nl2_rewrite 的相似度
    # Guideline通常包含 "Reason: ..." 或具体的规则描述，我们提取主要部分
    similarity = calculate_cosine_similarity(guideline_text, nl2_rewrite)
    
    print(f"🔍 Guideline 与 需求(nl2_rewrite) 相似度: {similarity:.4f}")

    # 2. 决定保存路径
    if similarity >= MAGIC_SIMILARITY_THRESHOLD:
        # 高相似度 -> 存入 Functional_dialect
        target_dir = FUNCTIONAL_ROOT_DIR
        print(f"   -> 判定为【功能类】知识 (Sim >= {MAGIC_SIMILARITY_THRESHOLD:})")
    else:
        # 低相似度 -> 存入 Rule_based_dialect
        target_dir = RULES_ROOT_DIR
        print(f"   -> 判定为【规则类】知识 (Sim < {MAGIC_SIMILARITY_THRESHOLD:})")

    # 3. 构造保存路径
    filename = DB_TYPE_TO_RULE_FILE.get(db_type, f"{db_type}.txt")
    file_path = os.path.join(target_dir, filename)

    # 4. 追加写入
    try:
        # 确保目录存在
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write("\n\n" + guideline_text)
        print(f"✅ Guideline 已追加保存至: {file_path}")
    except Exception as e:
        print(f"❌ 保存 Guideline 失败: {e}")# result_saver.py
import json
import os
from datetime import datetime
from config import JSON_OUTPUT_PATH, FINAL_REPORT_PATH

def save_json_results(all_json_results, output_path, target_db_type):
    """保存精简的SQL生成结果"""
    try:
        if os.path.exists(output_path):
            backup_path = output_path.replace('.json', f'_backup_{target_db_type}.json')
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            print(f"已备份原有JSON文件到: {backup_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_json_results, f, ensure_ascii=False, indent=2, separators=(',', ': '))
        
        print(f"JSON结果文件已保存到: {output_path}")
        print(f"共包含 {len(all_json_results)} 条结果（仅保留指定字段）")
        
        return output_path
        
    except Exception as e:
        raise RuntimeError(f"保存JSON文件失败: {str(e)}") from e

def save_text_results(all_results, output_dir, target_db_type):
    """保存文本格式结果"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"all_sql_results_{target_db_type}_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"SQL生成结果汇总（{target_db_type}）\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"使用模型: {os.getenv('MODEL_NAME', 'unknown')}\n")
        f.write(f"SQL执行超时时间: {os.getenv('SQL_EXECUTION_TIMEOUT', 'unknown')}秒\n")
        f.write(f"总处理项数: {len(all_results)}\n")
        f.write("="*80 + "\n\n")
        
        for idx, result in enumerate(all_results, 1):
            f.write(f"=== 结果项 {idx}/{len(all_results)} ===\n")
            f.write(f"原始问题: {result['question']}\n")
            f.write(f"{target_db_type}: {result[target_db_type]}\n")
            f.write("\n" + "-"*80 + "\n\n")
    
    print(f"文本结果文件已保存到: {filepath}")
    return filepath

def save_final_report(final_results):
    """保存最终执行报告（包含完整流程信息）"""
    try:
        # 备份原有报告
        if os.path.exists(FINAL_REPORT_PATH):
            backup_path = FINAL_REPORT_PATH.replace('.json', f'_backup_{datetime.now().strftime("%Y%m%d%H%M%S")}.json')
            with open(FINAL_REPORT_PATH, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            print(f"已备份原有报告到：{backup_path}")
        
        # 写入新报告
        with open(FINAL_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 最终执行报告已保存到：{FINAL_REPORT_PATH}")
        
        # 统计结果
        total = len(final_results)
        success_first = len([r for r in final_results if r["first_execution_status"] == "success"])
        success_second = len([r for r in final_results if r["final_execution_status"] == "success"])
        failed = len([r for r in final_results if r["final_execution_status"] == "failed"])
        skipped = len([r for r in final_results if r["final_execution_status"] == "skip"])
        error = len([r for r in final_results if r["final_execution_status"] == "error"])
        dead_loop_count = len([r for r in final_results if 
                             (r["first_error_msg"] and ("死循环" in r["first_error_msg"] or "超时" in r["first_error_msg"])) or
                             (r["second_error_msg"] and ("死循环" in r["second_error_msg"] or "超时" in r["second_error_msg"]))])
        
        print(f"\n统计汇总：")
        print(f"总处理项数：{total}")
        print(f"首次执行成功：{success_first}")
        print(f"最终执行成功（含二次修正）：{success_second}")
        print(f"最终执行失败：{failed}")
        print(f"跳过项：{skipped}")
        print(f"处理异常：{error}")
        print(f"死循环/超时案例数：{dead_loop_count}")
        
        return FINAL_REPORT_PATH
    except Exception as e:
        raise RuntimeError(f"保存最终报告失败：{str(e)}") from e# qwen3-max semantic_checker.py
import json
import os
import re
from config import SEMANTIC_FAIL_LOG_PATH
from api_client import call_modelscope_analysis
from prompt_builder import build_semantic_check_prompt

def parse_json_response(content):
    """尝试解析LLM返回的JSON"""
    try:
        # 清理可能存在的 markdown 代码块标记
        cleaned = re.sub(r'```json\s*', '', content, flags=re.IGNORECASE)
        cleaned = re.sub(r'```', '', cleaned).strip()
        return json.loads(cleaned)
    except:
        return None

def verify_sql_logic(question, nl2_rewrite, sql, db_type):
    """
    验证SQL逻辑
    返回: (is_pass: bool, reason: str)
    """
    prompt = build_semantic_check_prompt(question, nl2_rewrite, sql, db_type)
    analysis_result = call_modelscope_analysis(prompt)
    
    if not analysis_result:
        print("⚠️ 语义验证 API 无响应，默认跳过验证")
        return True, ""
        
    result_json = parse_json_response(analysis_result)
    
    if result_json:
        status = result_json.get("status", "PASS").upper()
        reason = result_json.get("reason", "")
        if status == "FAIL":
            return False, reason
        else:
            return True, ""
    else:
        # 如果无法解析JSON，保守策略：认为验证通过，或者是模型输出了非JSON的肯定回答
        # 也可以选择根据关键词判断，这里简单处理
        if "FAIL" in analysis_result.upper():
             return False, analysis_result
        return True, ""

def save_semantic_failure(item_index, question, nl2_rewrite, wrong_sql, reason, fixed_sql=None):
    """保存未实现需求的原因到文件"""
    log_entry = {
        "index": item_index,
        "timestamp": os.path.getmtime(SEMANTIC_FAIL_LOG_PATH) if os.path.exists(SEMANTIC_FAIL_LOG_PATH) else 0, # 这里仅作示意，实际用 append
        "question": question,
        "nl2_rewrite": nl2_rewrite,
        "unimplemented_reason": reason,
        "original_executable_sql": wrong_sql,
        "fixed_sql": fixed_sql
    }
    
    # 追加写入列表模式
    data = []
    if os.path.exists(SEMANTIC_FAIL_LOG_PATH):
        try:
            with open(SEMANTIC_FAIL_LOG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = []
            
    data.append(log_entry)
    
    with open(SEMANTIC_FAIL_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"📝 已记录语义不一致日志: {reason[:50]}...")
# utils.py
import os
import re
import json
import textwrap
from config import RESULT_JSON_PATH, DB_TYPE_TO_RULE_FILE, SUPPORTED_DBS, RULES_ROOT_DIR

def ensure_dir_exists(dir_path):
    """确保输出目录存在"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"创建输出目录: {dir_path}")

def truncate_content(content, max_length=60000):
    """截断过长的检索结果内容"""
    if not content:
        return ""
    if len(content) <= max_length:
        return content
    
    # 尝试按 Chunk 分割截断
    chunks = re.split(r'(=== Relevant Chunk \d+:)|(=== 相关语法参考 \d+:)', content)
    if len(chunks) > 1:
        truncated = []
        current_length = 0
        for chunk in chunks:
            if not chunk: continue
            if current_length + len(chunk) > max_length:
                remaining = max_length - current_length
                truncated.append(chunk[:remaining])
                break
            truncated.append(chunk)
            current_length += len(chunk)
        return "".join(truncated) + "\n\n[内容已截断，保留关键语法信息]"
    else:
        return content[:max_length] + "\n\n[内容过长已截断]"

def clean_nl2_rewrite(text):
    """清理nl2_rewrite格式"""
    if not text: return ""
    text = re.sub(r'\n+', ' ', text.strip())
    text = re.sub(r'\s+', ' ', text)
    return text

def load_db_rule_file(db_type):
    """加载指定数据库的规则文件"""
    if db_type not in DB_TYPE_TO_RULE_FILE:
        raise ValueError(f"不支持的数据库类型: {db_type}，支持的类型为：{SUPPORTED_DBS}")
    
    rule_filename = DB_TYPE_TO_RULE_FILE[db_type]
    # 直接使用从 config 导入的 RULES_ROOT_DIR
    rule_file_path = os.path.join(RULES_ROOT_DIR, rule_filename)
    
    if not os.path.exists(rule_file_path):
        raise FileNotFoundError(f"规则文件不存在: {rule_file_path}")
    
    try:
        with open(rule_file_path, 'r', encoding='utf-8') as f:
            rule_content = f.read().strip()
        print(f"✅ 成功加载{db_type}完整规则文件，文件大小：{len(rule_content)} 字符")
        return rule_content
    except Exception as e:
        raise RuntimeError(f"加载{db_type}规则文件失败: {str(e)}") from e

def get_retrieval_items():
    """获取数据项，解析 db_id"""
    try:
        if not os.path.exists(RESULT_JSON_PATH):
            raise FileNotFoundError(f"数据文件不存在: {RESULT_JSON_PATH}")

        with open(RESULT_JSON_PATH, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        
        items = []
        if isinstance(input_data, list):
            for idx, entry in enumerate(input_data):
                if "question" not in entry: continue
                
                # [读取 db_id]
                db_id = entry.get("db_id", "").strip()
                
                items.append({
                    "index": idx + 1,
                    "question": entry.get("question", "").strip(),
                    "nl2_rewrite": clean_nl2_rewrite(entry.get("nl2_rewrite", "")),
                    "db_id": db_id,  # 核心字段
                    "question_id": entry.get("question_id"),
                    "difficulty": entry.get("difficulty"),
                    "retrieval_results": entry.get("retrieval_results", {})
                })
        
        print(f"成功加载 {len(items)} 条数据")
        return items
    except Exception as e:
        raise RuntimeError(f"加载数据失败: {str(e)}") from e
    
def parse_sql_result(sql_content, target_db_type):
    """
    解析生成的SQL结果（增强版：支持多种Markdown格式及纯文本后备）
    """
    if not sql_content:
        return {target_db_type: ""}

    # 清理输入
    sql_content = sql_content.strip()

    # 1. 尝试匹配 ### DB_TYPE 格式 (Prompt中要求的标准格式)
    # 兼容: ### SQLite \n ```sql ... ``` 或 ### SQLite \n SELECT ...
    header_pattern = r'###\s*' + re.escape(target_db_type) + r'\s*(?:```(?:sql|'+ re.escape(target_db_type.lower()) +r')?\s*)?([\s\S]*?)(?:```|###|$)'
    match = re.search(header_pattern, sql_content, re.IGNORECASE)
    
    def clean_sql(raw_sql):
        if not raw_sql: return ""
        # 去除 markdown 结尾
        sql = re.sub(r'```.*$', '', raw_sql, flags=re.MULTILINE)
        # 去除 [MySQL SQL语句] 这种提示符
        sql = re.sub(r'\[.*?SQL语句\]', '', sql)
        # 去除解释性文字 (如果模型在代码块外废话)
        # 简单清洗：去除首尾空白
        return sql.strip()

    if match:
        extracted = match.group(1).strip()
        if extracted:
            return {target_db_type: clean_sql(extracted)}

    # 2. 尝试匹配通用的 Markdown 代码块 (```sql ... ```)
    # 针对模型忽略了 ### 头的情况
    fallback_match = re.search(r'```(?:sql|'+ re.escape(target_db_type.lower()) +r')?\s*([\s\S]*?)```', sql_content, re.IGNORECASE)
    if fallback_match:
        return {target_db_type: clean_sql(fallback_match.group(1))}

    # 3. [新增] 终极后备：如果全是文本，尝试通过关键字提取
    # 查找第一个 SELECT 或 WITH，直到分号结束
    # 这是一个比较暴力的匹配，防止模型只返回了纯代码
    raw_sql_match = re.search(r'\b(SELECT|WITH)\b[\s\S]+?;', sql_content, re.IGNORECASE)
    if raw_sql_match:
        return {target_db_type: clean_sql(raw_sql_match.group(0))}

    # 4. 如果连分号都没有，但看起来像SQL（以SELECT开头），直接返回全部
    if sql_content.upper().startswith("SELECT") or sql_content.upper().startswith("WITH"):
         return {target_db_type: clean_sql(sql_content)}

    return {target_db_type: ""}

def get_final_sql(item_result, target_db_type):
    """获取最终生成的有效SQL语句"""
    invalid_sql_markers = ["生成失败：未获取到有效SQL", "", None, "生成失败"]
    
    # 1. 优先检查 Magic 结果 (因为它是最后尝试的修复手段)
    magic_status = item_result.get("magic_execution_status")
    magic_sql = item_result.get("magic_generated_sql")
    if magic_status == "success" and magic_sql not in invalid_sql_markers:
        return magic_sql

    # 2. 检查第二次 (Standard RAG Fix) 结果
    # 注意：如果逻辑修正(Logic Fix)成功，它通常覆盖在 second_generated_sql 或者有单独字段
    # 原代码中逻辑修正在 main.py 里将结果写回了 second_generated_sql (第318行左右)
    # 所以这里检查 second 即可
    if item_result.get("final_execution_status") == "success":
        second_sql = item_result.get("second_generated_sql")
        if second_sql and second_sql not in invalid_sql_markers:
            return second_sql
        
        first_sql = item_result.get("first_generated_sql")
        if first_sql and first_sql not in invalid_sql_markers:
            return first_sql

    # 3. 如果都失败，按顺序返回非空内容
    if magic_sql and magic_sql not in invalid_sql_markers:
        return magic_sql
    
    second_sql = item_result.get("second_generated_sql")
    if second_sql and second_sql not in invalid_sql_markers:
        return second_sql
        
    first_sql = item_result.get("first_generated_sql")
    if first_sql and first_sql not in invalid_sql_markers:
        return first_sql
        
    return "生成失败"

def select_target_db():
    """命令行选择目标数据库"""
    print("\n=== 请选择要生成SQL的数据库类型 ===")
    for i, db_type in enumerate(SUPPORTED_DBS, 1):
        print(f"{i}. {db_type}")
    
    while True:
        user_input = input("\n请输入数字（1-5）选择数据库：").strip()
        if user_input.isdigit():
            selected_idx = int(user_input) - 1
            if 0 <= selected_idx < len(SUPPORTED_DBS):
                target_db = SUPPORTED_DBS[selected_idx]
                # 检查是否配置了连接
                if target_db in ["MySQL", "PostgreSQL", "SQLite"]:
                     if target_db not in os.getenv("DB_CONNECT_CONFIGS", {}):
                         # 这里简单的逻辑检查，实际上config里有
                         pass
                print(f"\n✅ 已选择目标数据库：{target_db}")
                return target_db
            else:
                print(f"❌ 输入无效！请输入1-{len(SUPPORTED_DBS)}之间的数字")
        else:
            print("❌ 输入无效！请输入数字")
