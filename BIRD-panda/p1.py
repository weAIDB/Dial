import os
import re
import json
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from pandasai import Agent
import pandasai as pai  
import pymysql
from pandasai_litellm import LiteLLM
import numpy as np
import pandas as pd  # 需要添加pandas导入

# 配置日志系统（关闭所有日志输出）
def configure_logging():
    # 日志级别设置为最高级以上，确保不记录任何日志
    logger = logging.getLogger('pandasai')
    logger.setLevel(logging.CRITICAL + 1)  # 高于最高级别，不记录任何日志
    
    llm_logger = logging.getLogger('pandasai_litellm')
    llm_logger.setLevel(logging.CRITICAL + 1)  # 关闭LLM相关日志
    
    return logger

# 初始化日志（仅初始化，不输出任何内容）
logger = configure_logging()

# 加载环境变量
load_dotenv()

# 配置 LLM
llm = LiteLLM(
    model="deepseek/deepseek-chat",  
    api_key=os.getenv("DEEPSEEK_API_KEY", "sk-578f63b08e74438692e3ebdb42b49934"),
    stream=False,
    temperature=0.0   
)

# 设置全局配置
pai.config.set({
    "llm": llm,
    "system_prompt": (
        "你是 SQL 专家，需利用 BIRD 数据库的表生成准确 SQL。特别注意：\n"
        "1. 生成的 SQL 必须完整且语法正确\n"
        "2. 包含特殊字符的列名必须用反引号(`)括起来\n"
        "3. 在引用列时，必要时使用 `this` 关键字\n"
        "4. 确保 WHERE 子句完整\n"
        "5. 示例格式：SELECT `T-CHO` FROM laboratory WHERE `T-CHO` > 200"
        "6. 包含空格的列名必须用反引号(`)括起来；\n"
        "7. 多表关联必须使用正确外键（如 player.player_api_id = player_attributes.player_api_id）；\n"
    ),
    "verbose": False,
    "show_code": True,
})

# 获取数据库表名和配置
def get_all_table_names():
    try:
        db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", 3306)),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", "xuhongming3410"),
            "database": os.getenv("DB_NAME", "BIRD"),
            "charset": "utf8mb4"
        }
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        tables = [table[0] for table in cursor.fetchall()]  
        cursor.close()
        conn.close()
        return tables, db_config
    except Exception as e:
        print(f"数据库连接失败：{str(e)}")
        raise

# 从JSON文件读取问题
def load_questions_from_json(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载JSON文件失败：{str(e)}")
        raise

# 保存结果到JSON文件
def save_results_to_json(results, output_path):
    try:
        # 自定义序列化处理器
        def default_serializer(obj):
            if isinstance(obj, (np.integer, np.int64)):
                return int(obj)  # 转换int64为Python int
            elif isinstance(obj, (np.float64, np.float32)):
                return float(obj)  # 转换float64为Python float
            elif isinstance(obj, (np.ndarray, pd.Series)):
                return obj.tolist()  # 转换数组/序列为列表
            elif isinstance(obj, pd.Timestamp):
                return obj.isoformat()  # 转换时间戳为字符串
            else:
                return str(obj)  # 其他类型转为字符串
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=default_serializer)
        
        print(f"结果已保存到 {output_path}")
    except Exception as e:
        print(f"保存结果失败：{str(e)}")
        raise

# 主处理函数
def main():
    all_tables, db_config = get_all_table_names()
    print(f"已获取数据库所有表: {all_tables[:5]}...（共{len(all_tables)}张）\n")
    
    sql_datasets = []
    for table in all_tables: 
        try:
            processed_table = re.sub(r'[^a-z0-9-]', '', table.lower().replace(' ', '-').replace('_', '-'))
            unique_path = f"datasets/{processed_table}"
            
            sql_dataset = pai.create(
                path=unique_path,  
                description=f"BIRD database table: {table}",  
                source={
                    "type": "mysql",  
                    "connection": db_config,  
                    "table": table,
                    "preview_rows": 5
                }
            )
            sql_datasets.append(sql_dataset)
        except Exception as e:
            print(f"创建数据源 {table} 失败：{str(e)}")
    
    agent = Agent(sql_datasets)
    input_json = r"C:\copy\code\minidev\MINIDEV\mini_dev_mysql.json"
    output_json = "generated_sql.json"
    questions_data = load_questions_from_json(input_json)
    
    results = []
    print(f"开始处理 {len(questions_data)} 个问题...\n")
    
    for item in questions_data:
        question_id = item["question_id"]
        db_id = item["db_id"]
        question_text = item["question"]
        difficulty = item["difficulty"]
        
        print(f"=== 问题 ID: {question_id} ===\n数据库: {db_id}\n难度: {difficulty}\n问题: {question_text}")
        
        try:
            response = agent.chat(question_text)
    
            # 调试输出

         
            
            # 获取生成的SQL
            generated_sql = ""
            if hasattr(response, 'generated_code') and response.generated_code:
                generated_sql = response.generated_code
            elif hasattr(response, 'last_sql') and response.last_sql:
                generated_sql = response.last_sql
            elif hasattr(response, 'sql_query') and response.sql_query:  # 尝试其他可能的属性名
                generated_sql = response.sql_query
            else:
                generated_sql = str(response)
            
            # 构建结果项，去除answer字段，将generated_SQL改为answer
            result_item = {
                "question_id": question_id,
                "db_id": db_id,
                "question": question_text,
                "difficulty": difficulty,
              
                "original_SQL": item.get("SQL", ""),
                "status": "success",  # 默认设为成功
                "answer": generated_sql  # 关键修改：将generated_SQL改为answer
            }
            
        except Exception as e:
            error_msg = f"执行异常: {str(e)}"
            print(f"{error_msg}\n")
            result_item = {
                "question_id": question_id,
                "db_id": db_id,
                "question": question_text,
                "difficulty": difficulty,
                "status": "error",
                "error": error_msg
            }
        
        results.append(result_item)
        print(f"问题 {question_id} 处理完成\n")
    
    save_results_to_json(results, output_json)
    print(f"所有问题处理完毕，结果已保存到 {output_json}")

if __name__ == "__main__":
    main()