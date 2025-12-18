import json
import os
import re
import sys
import threading
from datetime import datetime
from pathlib import Path
# 数据库连接相关导入
import mysql.connector
from mysql.connector import Error as MySQLError
import psycopg2
from psycopg2 import OperationalError as PgOperationalError
import sqlite3
from sqlite3 import Error as SQLiteError


# OpenAI客户端导入
from openai import OpenAI

# ===================== 核心配置 =====================
# 路径常量（更新为多库检索结果路径，删除无用脚本路径）
RESULT_JSON_PATH = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\translator4.0\输出结果\第一次测试结果\nl2rag_multi_db_result.json"
OUTPUT_DIR = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\translator4.0\输出结果\第一次测试结果"
RULES_ROOT_DIR = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\rag\knowledge\Rule_based_dialect"
RAG_MODULE_PATH = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\rag\Model4.0_rag"  # rag_fixed_chunk.py路径

# ModelScope配置
API_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen3-max"
API_KEY = "sk-a84e13e80bc3459594537184984f32ed"

# 数据库相关映射
DB_TYPE_TO_RULE_FILE = {
    "MySQL": "MySQL.txt",
    "PostgreSQL": "PostgreSQL.txt",
    "SQLite": "SQLite.txt",
    "Oracle": "Oracle.txt",
    "SQL Server": "SQL Server.txt"
}
SUPPORTED_DBS = list(DB_TYPE_TO_RULE_FILE.keys())

# 数据库连接配置（可根据实际环境修改）
DB_CONNECT_CONFIGS = {
    "MySQL": {
        "host": "localhost",
        "user": "root",
        "password": "xuhongming3410",
        "database": "bird",
        "buffered": True,
        "autocommit": True,
        "connection_timeout": 30
    },
    "PostgreSQL": {
        "host": "localhost",
        "user": "postgres",
        "password": "postgres",
        "database": "bird",
        "port": 5432
    },
    "SQLite": {
        "database": r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\bird.db"  # SQLite数据库文件路径
    }
}

# 结果文件路径
JSON_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "rag2SQL_result.json")
FINAL_REPORT_PATH = os.path.join(OUTPUT_DIR, "final_sql_execution_report.json")

# SQL执行配置
SQL_EXECUTION_TIMEOUT = 30  # SQL执行超时时间（秒），用于检测死循环
MAX_RETRY_COUNT = 1  # 超时后的重试次数

# 初始化OpenAI客户端
client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE_URL
)

# 添加RAG模块路径（确保能导入rag_fixed_chunk.py）
sys.path.append(RAG_MODULE_PATH)
try:
    # 从rag_fixed_chunk.py导入所需核心组件（适配实际实现）
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
    raise RuntimeError(f"无法导入rag_fixed_chunk.py中的组件，请检查路径：{RAG_MODULE_PATH}") from e

# ===================== 工具函数 =====================
def ensure_dir_exists(dir_path):
    """确保输出目录存在"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"创建输出目录: {dir_path}")

def truncate_content(content, max_length=60000):
    """截断过长的检索结果内容"""
    if len(content) <= max_length:
        return content
    
    chunks = re.split(r'(=== Relevant Chunk \d+:)|(=== 相关语法参考 \d+:)', content)
    if len(chunks) > 1:
        truncated = []
        current_length = 0
        for i in range(len(chunks)):
            if current_length > max_length:
                break
            if chunks[i] and (chunks[i].startswith("=== Relevant Chunk") or chunks[i].startswith("=== 相关语法参考")):
                chunk_header = chunks[i]
                chunk_content = chunks[i+1] if (i+1 < len(chunks) and chunks[i+1]) else ""
                chunk = chunk_header + chunk_content
                if current_length + len(chunk) > max_length:
                    chunk = chunk[:max_length - current_length]
                    truncated.append(chunk)
                    break
                truncated.append(chunk)
                current_length += len(chunk)
                i += 1  # 跳过已处理的content部分
        
        return "".join(truncated) + "\n\n[内容已截断，保留关键语法信息]"
    else:
        return content[:max_length] + "\n\n[内容过长已截断]"

def clean_nl2_rewrite(text):
    """清理nl2_rewrite格式"""
    text = re.sub(r'\n+', ' ', text.strip())
    text = re.sub(r'\s+', ' ', text)
    return text

def load_db_rule_file(db_type):
    """加载指定数据库的规则文件（首次生成用）"""
    if db_type not in DB_TYPE_TO_RULE_FILE:
        raise ValueError(f"不支持的数据库类型: {db_type}，支持的类型为：{SUPPORTED_DBS}")
    
    rule_filename = DB_TYPE_TO_RULE_FILE[db_type]
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

def parse_sql_result(sql_content, target_db_type):
    """解析生成的SQL结果"""
    db_patterns = {
        "MySQL": r'### MySQL\n([\s\S]*?)(?=### |$)',
        "PostgreSQL": r'### PostgreSQL\n([\s\S]*?)(?=### |$)',
        "SQLite": r'### SQLite\n([\s\S]*?)(?=### |$)',
        "Oracle": r'### Oracle\n([\s\S]*?)(?=### |$)',
        "SQL Server": r'### SQL Server\n([\s\S]*?)(?=### |$)'
    }
    
    if target_db_type not in db_patterns:
        raise ValueError(f"不支持的数据库类型: {target_db_type}")
    
    pattern = db_patterns[target_db_type]
    match = re.search(pattern, sql_content)
    
    def clean_sql(match_obj):
        if match_obj:
            sql_str = match_obj.group(1).strip()
            sql_str = re.sub(r'\[.*?\]', '', sql_str)
            sql_str = re.sub(r'\n+', ' ', sql_str).strip()
            return sql_str if sql_str else ""
        return ""
    
    return {target_db_type: clean_sql(match)}

def get_final_sql(item_result, target_db_type):
    """
    获取最终生成的SQL语句
    执行成功则返回最终有效的SQL，失败/跳过/异常则返回空字符串
    """
    # 定义无效SQL标识
    invalid_sql_markers = ["生成失败：未获取到有效SQL", "", None]
    
    # 最终执行成功的情况
    if item_result["final_execution_status"] == "success":
        # 优先使用二次生成的SQL（如果有且有效）
        second_sql = item_result.get("second_generated_sql")
        if second_sql not in invalid_sql_markers:
            return second_sql
        # 其次使用首次生成的SQL
        first_sql = item_result.get("first_generated_sql")
        if first_sql not in invalid_sql_markers:
            return first_sql
    # 执行失败/跳过/异常的情况，返回空字符串
    return ""

# 删除无用的run_translator_script和fix_translator_script_encoding函数（不再依赖translator脚本）

def get_retrieval_items():
    """获取多库检索结果项（从新的JSON文件读取）"""
    try:
        if not os.path.exists(RESULT_JSON_PATH):
            raise FileNotFoundError(f"多库检索结果文件不存在: {RESULT_JSON_PATH}")
        
        with open(RESULT_JSON_PATH, 'r', encoding='utf-8') as f:
            output_data = json.load(f)
        
        retrieval_items = []
        if isinstance(output_data, list):
            for idx, item in enumerate(output_data):
                if isinstance(item, dict) and "retrieval_results" in item and "question" in item:
                    # 过滤无效检索结果（所有数据库都无结果且无错误）
                    all_empty = all(
                        not content or content == "No relevant content retrieved"
                        for content in item.get("retrieval_results", {}).values()
                    )
                    if all_empty and item.get("retrieval_result") != "Error":
                        print(f"⚠️ 第{idx+1}条数据无有效检索结果，跳过")
                        continue
                    
                    # 清理并构造检索项（保留retrieval_results完整结构）
                    retrieval_items.append({
                        "index": idx + 1,
                        "question": item.get("question", "").strip(),
                        "nl2_rewrite": clean_nl2_rewrite(item.get("nl2_rewrite", "")),
                        "retrieval_results": item.get("retrieval_results", {}),  # 保留5个数据库的检索结果
                        "question_id": item.get("question_id", None),
                        "difficulty": item.get("difficulty", None)
                    })
        
        if not retrieval_items:
            raise RuntimeError("多库检索结果文件中未找到有效的检索结果项")
            
        print(f"成功加载 {len(retrieval_items)} 个有效检索结果项")
        return retrieval_items
            
    except Exception as e:
        raise RuntimeError(f"获取检索结果项失败: {str(e)}") from e

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
            temperature=0.1,
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

# ===================== 数据库执行相关函数（无修改） =====================
def get_db_connection(db_type):
    """创建数据库连接"""
    if db_type not in DB_CONNECT_CONFIGS:
        raise ValueError(f"不支持的数据库类型：{db_type}")
    
    config = DB_CONNECT_CONFIGS[db_type]
    connection = None
    
    try:
        if db_type == "MySQL":
            connection = mysql.connector.connect(**config)
        elif db_type == "PostgreSQL":
            connection = psycopg2.connect(**config)
        elif db_type == "SQLite":
            connection = sqlite3.connect(config["database"], timeout=30)
        
        if connection:
            print(f"✅ {db_type} 连接成功")
        return connection
    except Exception as e:
        print(f"❌ {db_type} 连接失败：{str(e)[:200]}")
        return None

def reconnect_db(db_type):
    """数据库重连"""
    print(f"⚠️ {db_type} 连接失效，尝试重连...")
    return get_db_connection(db_type)

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
    """测试SQL执行（支持超时检测，用于处理死循环）"""
    cursor = None
    execution_result = {"status": "failed", "error": "未知错误"}
    
    try:
        # 检查连接有效性
        if not connection:
            connection = reconnect_db(db_type)
            if not connection:
                return {"status": "failed", "error": f"{db_type} 连接不可用"}
        
        # 不同数据库的连接检查
        if db_type == "MySQL" and not connection.is_connected():
            connection = reconnect_db(db_type)
        elif db_type == "PostgreSQL" and connection.closed:
            connection = reconnect_db(db_type)
        
        if not connection:
            return {"status": "failed", "error": f"{db_type} 重连失败"}
        
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
    
    return execution_result

# ===================== 二次RAG检索函数（无修改） =====================
def secondary_rag_retrieval(question, error_msg, db_type):
    """
    二次RAG检索（返回2个最相关chunk）
    适配rag_fixed_chunk.py的实际实现：单文件加载+临时向量库+固定分割器
    """
    try:
        # 1. 构建检索查询（融合问题+错误信息，提升相关性）
        # 针对死循环场景增加关键词，提高检索准确性
        retrieval_query = f"问题：{question} | SQL执行错误：{error_msg} | 关键词：死循环、超时、查询优化、避免笛卡尔积、递归查询限制、索引优化、查询性能"
        print(f"二次检索查询：{retrieval_query[:100]}...")
        
        # 2. 获取目标数据库的规则文件路径（Rule_based_dialect下的对应文件）
        rule_filename = DB_TYPE_TO_RULE_FILE[db_type]
        rule_file_path = os.path.join(RULES_ROOT_DIR, rule_filename)
        if not os.path.exists(rule_file_path):
            print(f"⚠️ 规则文件不存在：{rule_file_path}")
            return "无相关语法参考"
        
        # 3. 加载单个规则文件（适配rag_fixed_chunk.py的TextLoader）
        loader = TextLoader(rule_file_path, encoding='utf-8')
        docs = loader.load()
        if not docs:
            print(f"⚠️ 规则文件{rule_file_path}加载后无内容")
            return "无相关语法参考"
        
        # 4. 用HomyMarkerSplitter分割文档（与rag_fixed_chunk.py保持一致）
        text_splitter = HomyMarkerSplitter()
        split_docs = text_splitter.split_documents(docs)
        print(f"规则文件分割为 {len(split_docs)} 个文档块")
        
        if len(split_docs) < 2:
            print(f"⚠️ 文档块数量不足2个，仅获取{len(split_docs)}个")
        
        # 5. 创建临时向量库（不持久化，避免干扰原有向量库）
        temp_vector_store = Chroma(
            embedding_function=embedding_model,
            persist_directory=None  # 临时向量库，退出即销毁
        )
        temp_vector_store.add_documents(split_docs)
        
        # 6. 构建检索器（强制返回2个最相关chunk）
        temp_retriever = temp_vector_store.as_retriever(
            search_kwargs={"k": 2}  # 覆盖原rag的k=5，改为返回2个
        )
        
        # 7. 构建检索链（与rag_fixed_chunk.py的chain结构一致）
        temp_chain = (
            {"question": RunnablePassthrough()}
            | RunnablePassthrough.assign(context=itemgetter("question") | temp_retriever)
            | format_retrieval_result  # 复用原有格式化函数
            | StrOutputParser()
        )
        
        # 8. 执行检索
        retrieval_result = temp_chain.invoke(retrieval_query)
        
        # 9. 处理检索结果（确保返回2个chunk格式）
        if "No relevant content retrieved" in retrieval_result:
            return "=== 相关语法参考 1 ===\n无相关语法参考\n\n=== 相关语法参考 2 ===\n无相关语法参考"
        
        # 解析检索结果中的chunk（匹配rag_fixed_chunk.py的格式化输出）
        chunk_pattern = r'=== Relevant Chunk (\d+): (.*?) ===\n([\s\S]*?)(?=\n=== |$)'
        matches = re.findall(chunk_pattern, retrieval_result, re.DOTALL)
        
        # 格式化前2个chunk
        formatted_chunks = []
        for i, (chunk_idx, title, content) in enumerate(matches[:2], 1):
            # 截断过长的chunk内容（避免Prompt溢出）
            truncated_content = content[:8000] + "..." if len(content) > 8000 else content
            formatted_chunks.append(
                f"=== 相关语法参考 {i}（{title}）===\n{truncated_content.strip()}"
            )
        
        # 不足2个时补充空chunk
        while len(formatted_chunks) < 2:
            formatted_chunks.append(f"=== 相关语法参考 {len(formatted_chunks)+1} ===\n无更多相关语法参考")
        
        final_retrieval = "\n\n".join(formatted_chunks)
        print(f"二次检索结果（前200字符）：{final_retrieval[:200]}...")
        return final_retrieval
    
    except Exception as e:
        error_detail = str(e)[:200]
        print(f"⚠️ 二次RAG检索失败：{error_detail}...")
        return (
            f"=== 相关语法参考 1 ===\n检索失败：{error_detail}（无相关语法参考）\n\n"
            f"=== 相关语法参考 2 ===\n检索失败：{error_detail}（无相关语法参考）"
        )

# ===================== Prompt构造函数（核心优化） =====================
def build_prompt(
    retrieval_item, 
    target_db_type, 
    db_rule_content=None,  # 首次生成用：完整规则；二次生成用：None
    secondary_rag_content=None,  # 二次生成用：错误相关语法
    error_msg=None,
    first_sql=None  # 二次生成用：首次错误SQL
):
    """
    构造Prompt（支持首次生成和二次修正）
    核心优化：1. 区分多库检索结果；2. 二次生成精简语法+传入错误SQL
    """
    # 第一步：处理多库检索结果，构建语法参考部分
    retrieval_results = retrieval_item["retrieval_results"]
    
    # 1. 目标数据库语法（可使用）
    # 修复：将f-string内的换行符表达式提前赋值，避免{}内出现反斜杠
    target_grammar = retrieval_results.get(target_db_type, "").strip()
    target_grammar_content = target_grammar if target_grammar else "无相关语法片段"
    target_grammar_section = f"""### 1. 目标数据库语法参考（{target_db_type}，可直接使用）
{target_grammar_content}

"""
    
    # 2. 其他数据库语法（仅参考通用部分，勿混用）
    other_dbs_grammar = []
    for db in SUPPORTED_DBS:
        if db == target_db_type:
            continue
        grammar = retrieval_results.get(db, "").strip()
        grammar_content = grammar if grammar else "无相关语法片段"
        # 修复：提前拼接每行内容，避免f-string{}内的反斜杠
        other_db_line = f"#### {db}（非目标数据库，勿直接使用）\n{grammar_content}"
        other_dbs_grammar.append(other_db_line)
    
    # 关键修复：将"\n\n".join提前赋值给变量，避免f-string{}内出现反斜杠
    other_dbs_joined = "\n\n".join(other_dbs_grammar)
    other_grammar_section = f"""### 2. 其他数据库语法参考（仅参考通用逻辑，避免混用非通用语法）
{other_dbs_joined}

"""
    
    # 第二步：构建规则文件语法部分（分首次/二次生成）
    rule_section = ""
    if secondary_rag_content and error_msg and first_sql:
        # 二次生成：仅传入错误相关语法+首次错误SQL
        # 修复：拆分f-string内的表达式，避免{}内反斜杠
        secondary_rag_content_val = secondary_rag_content if secondary_rag_content else "无针对性语法片段"
        rule_section = f"""### 3. 错误修正参考（仅使用以下针对性语法）
#### 3.1 上一次生成的错误SQL语句：
{first_sql}

#### 3.2 错误原因：
{error_msg}

#### 3.3 针对性语法参考（基于错误检索，必须严格遵循）：
{secondary_rag_content_val}

"""
    else:
        # 首次生成：传入完整规则文件语法
        db_rule_content_val = db_rule_content if db_rule_content else "无完整语法规则"
        rule_section = f"""### 3. 完整语法规则（{target_db_type}，首次生成需严格遵循）
{db_rule_content_val}

"""
    
    # 第三步：拼接问题需求部分
    # 修复：拆分表达式，避免{}内反斜杠
    requirement_section = f"""### 4. 问题需求
#### 原始问题：
{retrieval_item["question"]}

#### 详细描述：
{retrieval_item["nl2_rewrite"]}

"""
    
    # 第四步：生成要求
    # 修复：拆分f-string，避免{}内反斜杠
    requirement_section += f"""### 5. 生成要求
1. 必须生成严格符合{target_db_type}语法规范的SQL，优先使用目标数据库语法参考，其次参考完整语法规则；
2. 可借鉴其他数据库的通用语法逻辑，但严禁直接使用非目标数据库的特有语法（如函数、关键字差异）；
3. 确保SQL准确实现需求，避免死循环、笛卡尔积过大等性能问题，必要时添加LIMIT/OFFSET；
4. 二次修正时需重点解决上一次的错误，基于针对性语法参考优化SQL；
5. 输出格式严格按照以下结构，不要任何额外内容，SQL语句结尾必须加分号：

### {target_db_type}
[{target_db_type} SQL语句]
"""
    
    # 拼接完整Prompt并截断
    full_prompt = target_grammar_section + other_grammar_section + rule_section + requirement_section
    full_prompt = truncate_content(full_prompt, max_length=210000)
    
    return full_prompt.strip()
# ===================== 结果保存函数（无修改） =====================
def save_final_report(final_results):
    """保存最终执行报告（包含完整流程信息）"""
    try:
        # 备份原有报告（如果存在）
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
        
        # 统计结果（增加死循环/超时统计）
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
        raise RuntimeError(f"保存最终报告失败：{str(e)}") from e

# ===================== 命令行选择数据库（无修改） =====================
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
                # 检查数据库连接配置是否存在
                if target_db not in DB_CONNECT_CONFIGS:
                    print(f"⚠️  {target_db} 的连接配置未启用，是否继续？（y/n）")
                    confirm = input().strip().lower()
                    if confirm != 'y':
                        continue
                print(f"\n✅ 已选择目标数据库：{target_db}")
                return target_db
            else:
                print(f"❌ 输入无效！请输入1-{len(SUPPORTED_DBS)}之间的数字")
        else:
            print("❌ 输入无效！请输入数字")

# ===================== 主函数（核心修改输出字段） =====================
def main():
    """主流程：生成→执行→失败修正→保存结果"""
    try:
        ensure_dir_exists(OUTPUT_DIR)
        
        # 步骤1：选择目标数据库（预先输入，用于Prompt区分多库语法）
        target_db_type = select_target_db()
        
        # 步骤2：加载规则文件（仅首次生成用）
        print(f"\n正在加载{target_db_type}完整规则文件...")
        db_rule_content = load_db_rule_file(target_db_type)
        
        # 步骤3：初始化数据库连接
        print(f"\n正在初始化{target_db_type}数据库连接...")
        db_connection = get_db_connection(target_db_type)
        if not db_connection:
            print(f"⚠️ 数据库连接初始化失败，将跳过执行验证环节")
        
        # 步骤4：获取多库检索结果项
        print("\n正在加载多库检索结果项...")
        retrieval_items = get_retrieval_items()
        
        # 步骤5：逐个处理（生成→执行→修正）
        final_results = []
        total_items = len(retrieval_items)
        
        for idx, item in enumerate(retrieval_items):
            item_index = item["index"]
            question = item["question"]
            nl2_rewrite = item["nl2_rewrite"]
            
            print(f"\n==================================================")
            print(f"正在处理第 {item_index}/{total_items} 个项目")
            print(f"问题：{question[:100]}...")
            print(f"目标数据库：{target_db_type}")
            print(f"==================================================")
            
            # 初始化项目结果
            item_result = {
                "index": item_index,
                "question": question,
                "nl2_rewrite": nl2_rewrite,
                "question_id": item.get("question_id", None),
                "difficulty": item.get("difficulty", None),
                "first_generated_sql": "",
                "first_execution_status": "",
                "first_error_msg": None,
                "second_generated_sql": None,
                "second_execution_status": None,
                "second_error_msg": None,
                "final_execution_status": "",
                "secondary_rag_content": None,
                "execution_timeout": False,
                "target_db_type": target_db_type
            }
            
            try:
                # ---------------------- 第一次生成SQL（核心修改：传入多库检索结果+完整规则） ----------------------
                print(f"\n1. 首次生成SQL...")
                prompt_first = build_prompt(
                    retrieval_item=item,
                    target_db_type=target_db_type,
                    db_rule_content=db_rule_content  # 首次生成：传入完整规则
                )
                sql_result_first = call_modelscope_api_single(prompt_first, target_db_type)
                parsed_sql_first = parse_sql_result(sql_result_first, target_db_type)
                first_sql = parsed_sql_first[target_db_type]
                
                if not first_sql:
                    print(f"❌ 首次生成失败：未获取到有效SQL")
                    item_result.update({
                        "first_generated_sql": "生成失败：未获取到有效SQL",
                        "first_execution_status": "skip",
                        "final_execution_status": "skip"
                    })
                    final_results.append(item_result)
                    continue
                
                item_result["first_generated_sql"] = first_sql
                print(f"首次生成SQL：{first_sql[:100]}...")
                
                # ---------------------- 第一次执行验证（无修改） ----------------------
                if not db_connection:
                    print(f"⚠️ 无数据库连接，跳过执行验证")
                    item_result.update({
                        "first_execution_status": "skip",
                        "final_execution_status": "skip"
                    })
                    final_results.append(item_result)
                    continue
                
                print(f"\n2. 执行首次生成的SQL（超时时间：{SQL_EXECUTION_TIMEOUT}秒）...")
                exec_result_first = test_sql_execution(first_sql, target_db_type, db_connection)
                
                item_result["first_execution_status"] = exec_result_first["status"]
                item_result["first_error_msg"] = exec_result_first["error"]
                
                # 标记是否为超时/死循环场景
                if exec_result_first["error"] and ("死循环" in exec_result_first["error"] or "超时" in exec_result_first["error"]):
                    item_result["execution_timeout"] = True
                    print(f"⚠️ 检测到SQL执行超时/死循环场景")
                
                if exec_result_first["status"] == "success":
                    print(f"✅ 首次执行成功")
                    item_result["final_execution_status"] = "success"
                    final_results.append(item_result)
                    continue
                else:
                    print(f"❌ 首次执行失败：{exec_result_first['error'][:100]}...")
                
                # ---------------------- 二次修正流程（核心修改：传入错误SQL+针对性语法） ----------------------
                print(f"\n3. 启动二次修正流程...")
                
                # 3.1 二次RAG检索（无修改）
                print(f"3.1 执行二次RAG检索（返回2个相关chunk）...")
                secondary_rag_content = secondary_rag_retrieval(
                    question=question,
                    error_msg=exec_result_first["error"],
                    db_type=target_db_type
                )
                item_result["secondary_rag_content"] = secondary_rag_content
                print(f"二次检索结果已获取（长度：{len(secondary_rag_content)} 字符）")
                
                # 3.2 构造修正Prompt（核心修改：传入错误SQL+针对性语法，不传入完整规则）
                print(f"3.2 构造修正Prompt...")
                prompt_second = build_prompt(
                    retrieval_item=item,
                    target_db_type=target_db_type,
                    secondary_rag_content=secondary_rag_content,  # 二次生成：仅传入错误相关语法
                    error_msg=exec_result_first["error"],
                    first_sql=first_sql  # 传入首次错误SQL
                )
                
                # 3.3 第二次生成SQL（无修改）
                print(f"3.3 重新生成SQL...")
                sql_result_second = call_modelscope_api_single(prompt_second, target_db_type)
                parsed_sql_second = parse_sql_result(sql_result_second, target_db_type)
                second_sql = parsed_sql_second[target_db_type]
                
                if not second_sql:
                    print(f"❌ 二次生成失败：未获取到有效SQL")
                    item_result.update({
                        "second_generated_sql": "生成失败：未获取到有效SQL",
                        "second_execution_status": "skip",
                        "final_execution_status": "failed"
                    })
                    final_results.append(item_result)
                    continue
                
                item_result["second_generated_sql"] = second_sql
                print(f"二次生成SQL：{second_sql[:100]}...")
                
                # 3.4 第二次执行验证（无修改）
                print(f"3.4 执行二次生成的SQL（超时时间：{SQL_EXECUTION_TIMEOUT}秒）...")
                exec_result_second = test_sql_execution(second_sql, target_db_type, db_connection)
                
                item_result["second_execution_status"] = exec_result_second["status"]
                item_result["second_error_msg"] = exec_result_second["error"]
                item_result["final_execution_status"] = exec_result_second["status"]
                
                # 检查二次执行是否仍为超时/死循环
                if exec_result_second["error"] and ("死循环" in exec_result_second["error"] or "超时" in exec_result_second["error"]):
                    item_result["execution_timeout"] = True
                    print(f"⚠️ 二次生成的SQL仍执行超时/死循环")
                
                if exec_result_second["status"] == "success":
                    print(f"✅ 二次执行成功")
                else:
                    print(f"❌ 二次执行失败：{exec_result_second['error'][:100]}...")
                
                # 添加到最终结果
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
        
        # 步骤6：保存结果（核心修改：仅保留指定字段）
        print(f"\n==================================================")
        print(f"所有项目处理完成，正在保存结果...")
        print(f"==================================================")
        
        # 构造精简的输出结果（仅保留指定字段）
        all_json_results = []
        for r in final_results:
            final_sql = get_final_sql(r, target_db_type)
            all_json_results.append({
                "question": r["question"],
                "nl2_rewrite": r["nl2_rewrite"],
                "question_id": r.get("question_id"),
                "final_execution_status": r["final_execution_status"],
                "difficulty": r.get("difficulty"),
                target_db_type: final_sql  # 最终生成的SQL，失败则为空
            })
        
        # 保存精简的SQL生成结果（仅指定字段）
        save_json_results(
            all_json_results=all_json_results,
            output_path=JSON_OUTPUT_PATH,
            target_db_type=target_db_type
        )
        
        # 保存完整执行报告（保留完整信息，便于调试）
        save_final_report(final_results)
        
        # 关闭数据库连接
        if db_connection:
            try:
                if target_db_type == "MySQL" and db_connection.is_connected():
                    db_connection.close()
                elif target_db_type == "PostgreSQL" and not db_connection.closed:
                    db_connection.close()
                else:
                    db_connection.close()
                print(f"\n✅ {target_db_type} 数据库连接已关闭")
            except Exception as e:
                print(f"\n⚠️ 关闭数据库连接时警告：{str(e)}")
        
        print(f"\n🎉 流程全部完成！")
        
    except Exception as e:
        print(f"\n❌ 程序执行出错：{str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)

# ===================== 原有保存函数（无修改） =====================
def save_json_results(all_json_results, output_path, target_db_type):
    """保存原始SQL生成结果"""
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
    """保存文本格式结果（保留）"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"all_sql_results_{target_db_type}_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"SQL生成结果汇总（{target_db_type}）\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"使用模型: {MODEL_NAME}\n")
        f.write(f"SQL执行超时时间: {SQL_EXECUTION_TIMEOUT}秒\n")
        f.write(f"总处理项数: {len(all_results)}\n")
        f.write("="*80 + "\n\n")
        
        for idx, result in enumerate(all_results, 1):
            f.write(f"=== 结果项 {idx}/{len(all_results)} ===\n")
            f.write(f"原始问题: {result['question']}\n")
            f.write(f"{target_db_type}: {result[target_db_type]}\n")
            f.write("\n" + "-"*80 + "\n\n")
    
    print(f"文本结果文件已保存到: {filepath}")
    return filepath

if __name__ == "__main__":
    print("=== NL2SQL批量生成+执行验证工具（多库检索优化版）===")
    print(f"使用模型: {MODEL_NAME}")
    print(f"API基础地址: {API_BASE_URL}")
    print(f"支持数据库: {', '.join(SUPPORTED_DBS)}")
    print(f"多库检索结果路径: {RESULT_JSON_PATH}")
    print(f"完整语法规则路径: {RULES_ROOT_DIR}")
    print(f"SQL执行超时时间: {SQL_EXECUTION_TIMEOUT}秒（用于检测死循环）")
    main()