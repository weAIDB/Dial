# # api_client.py



##gpt5.2

# 适配 OpenAI GPT 5.2 的版本
from openai import OpenAI
import os

# -------------------------- 配置 GPT 5.2 关键参数 --------------------------
# 方式1：直接配置（建议优先用环境变量，避免硬编码）
OPENAI_API_KEY = "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"
  # 从系统环境变量读取API Key
MODEL_NAME = "gpt-5.2"  # GPT 5.2 的模型名称（以OpenAI官方命名为准，如gpt-4o-2024-08-06）

# 初始化 OpenAI 客户端
client = OpenAI(api_key=OPENAI_API_KEY)

def call_gpt_api_single(prompt_content, target_db_type):
    """调用 OpenAI GPT 5.2 生成SQL（替换原ModelScope逻辑）"""
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
            top_p=0.95,
            stream=False
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        error_detail = f"{str(e)}"
        # OpenAI 异常的错误详情获取方式（适配其异常结构）
        if hasattr(e, 'body') and e.body is not None:
            try:
                error_detail += f" | 响应内容: {e.body[:500]}"
            except:
                pass
        raise RuntimeError(f"GPT API调用失败: {error_detail}") from e

def call_gpt_analysis(prompt_content):
    """
    适配 GPT 5.2 的通用分析调用，用于语义验证
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
            temperature=0.1,  # 分析任务需要低随机性
            stream=False
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ GPT分析API调用失败: {e}")
        return None