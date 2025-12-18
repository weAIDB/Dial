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



