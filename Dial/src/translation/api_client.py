# # qwen3-max api_client.py
# from config import client, MODEL_NAME

# def call_modelscope_api_single(prompt_content, target_db_type):
#     """Call ModelScope API to generate SQL"""
#     if len(prompt_content) > 250000:
#         raise RuntimeError(f"Single Prompt is too long ({len(prompt_content)} characters), exceeding API limits")
    
#     try:
#         response = client.chat.completions.create(
#             model=MODEL_NAME,
#             messages=[
#                 {
#                     "role": "system",
#                     "content": f"You are a professional {target_db_type} SQL generation assistant, proficient in the syntax specifications of this database. The generated SQL must accurately implement the requirements, end with a semicolon, and return only the specified format content. Pay special attention to avoiding SQL that may cause infinite loops (such as infinite recursive queries, associated queries with excessive Cartesian products, etc.)."
#                 },
#                 {
#                     "role": "user",
#                     "content": prompt_content
#                 }
#             ],
#             temperature=0.2,
#             max_tokens=1500,
#             top_p=0.95,
#             stream=False
#         )
        
#         return response.choices[0].message.content.strip()
        
#     except Exception as e:
#         error_detail = f"{str(e)}"
#         if hasattr(e, 'response') and e.response is not None:
#             try:
#                 error_detail += f" | Response content: {e.response.text[:500]}"
#             except:
#                 pass
#         raise RuntimeError(f"API call failed: {error_detail}") from e

# def call_modelscope_analysis(prompt_content):
#     """
#     General analysis call, used for semantic verification.
#     Does not enforce returning SQL format, but returns analysis results (JSON recommended).
#     """
#     try:
#         response = client.chat.completions.create(
#             model=MODEL_NAME,
#             messages=[
#                 {
#                     "role": "system",
#                     "content": "You are a rigorous SQL code audit expert. Your task is to compare the user's natural language requirements with the generated SQL statements to determine if the SQL completely implements the requirements. Please analyze objectively and logically; do not fabricate reasons."
#                 },
#                 {
#                     "role": "user",
#                     "content": prompt_content
#                 }
#             ],
#             temperature=0.1, # Low randomness required for analysis tasks
#             stream=False
#         )
#         return response.choices[0].message.content.strip()
#     except Exception as e:
#         print(f"⚠️ Analysis API call failed: {e}")
#         return None



# ##deepseek api_client.py

# # api_client.py
# import requests
# import json
# from config import API_KEY, API_BASE_URL, MODEL_NAME  # Ensure deepseek parameters are configured in config

# # ========== Global Configuration (can also be moved to config.py) ==========
# TIMEOUT = 60  # Request timeout
# MAX_RETRIES = 3  # Maximum retry attempts
# RETRY_DELAY = 1  # Retry interval (seconds)

# def call_modelscope_api_single(prompt_content, target_db_type):
#     """
#     Deepseek-adapted SQL generation function (retains original function name and parameters).
#     Replaces original ModelScope call logic with deepseek API call.
#     """
#     if len(prompt_content) > 250000:
#         raise RuntimeError(f"Single Prompt is too long ({len(prompt_content)} characters), exceeding API limits")
    
#     # Construct deepseek request headers
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {API_KEY}"
#     }
    
#     # Construct deepseek message body (retain original system prompt logic)
#     messages = [
#         {
#             "role": "system",
#             "content": f"You are a professional {target_db_type} SQL generation assistant, proficient in the syntax specifications of this database. The generated SQL must accurately implement the requirements, end with a semicolon, and return only the specified format content. Pay special attention to avoiding SQL that may cause infinite loops (such as infinite recursive queries, associated queries with excessive Cartesian products, etc.)."
#         },
#         {
#             "role": "user",
#             "content": prompt_content
#         }
#     ]
    
#     # Construct request parameters
#     data = {
#         "model": MODEL_NAME,  # deepseek-chat
#         "messages": messages,
#         "temperature": 0.2,
#         "max_tokens": 1500,
#         "top_p": 0.95,
#         "stream": False
#     }
    
#     retry_count = 0
#     while retry_count < MAX_RETRIES:
#         try:
#             # Call deepseek API
#             response = requests.post(
#                 url=f"{API_BASE_URL}/chat/completions",
#                 headers=headers,
#                 json=data,
#                 timeout=TIMEOUT
#             )
#             response.raise_for_status()  # Raise HTTP error (4xx/5xx)
#             result = response.json()
            
#             # Extract and return result (consistent with original logic)
#             if result.get("choices") and len(result["choices"]) > 0:
#                 return result["choices"][0]["message"]["content"].strip()
#             else:
#                 raise RuntimeError(f"DeepSeek returned empty content: {json.dumps(result, ensure_ascii=False)}")
                
#         except Exception as e:
#             retry_count += 1
#             error_detail = f"{str(e)}"
#             # Capture response content (consistent with original logic)
#             if hasattr(e, 'response') and e.response is not None:
#                 try:
#                     error_detail += f" | Response content: {e.response.text[:500]}"
#                 except:
#                     pass
            
#             # Raise exception if the last retry fails
#             if retry_count >= MAX_RETRIES:
#                 raise RuntimeError(f"API call failed: {error_detail}") from e
            
#             # Wait before retrying
#             import time
#             time.sleep(RETRY_DELAY)

# def call_modelscope_analysis(prompt_content):
#     """
#     Deepseek-adapted semantic analysis function (retains original function name and parameters).
#     General analysis call used for semantic verification.
#     """
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {API_KEY}"
#     }
    
#     messages = [
#         {
#             "role": "system",
#             "content": "You are a rigorous SQL code audit expert. Your task is to compare the user's natural language requirements with the generated SQL statements to determine if the SQL completely implements the requirements. Please analyze objectively and logically; do not fabricate reasons."
#         },
#         {
#             "role": "user",
#             "content": prompt_content
#         }
#     ]
    
#     data = {
#         "model": MODEL_NAME,  # deepseek-chat
#         "messages": messages,
#         "temperature": 0.1,  # Low randomness ensures analysis accuracy
#         "stream": False
#     }
    
#     try:
#         response = requests.post(
#             url=f"{API_BASE_URL}/chat/completions",
#             headers=headers,
#             json=data,
#             timeout=TIMEOUT
#         )
#         response.raise_for_status()
#         result = response.json()
        
#         if result.get("choices") and len(result["choices"]) > 0:
#             return result["choices"][0]["message"]["content"].strip()
#         else:
#             print(f"⚠️ DeepSeek analysis interface returned empty content: {json.dumps(result, ensure_ascii=False)}")
#             return None
            
#     except Exception as e:
#         error_detail = f"{str(e)}"
#         if hasattr(e, 'response') and e.response is not None:
#             try:
#                 error_detail += f" | Response content: {e.response.text[:500]}"
#             except:
#                 pass
#         print(f"⚠️ Analysis API call failed: {error_detail}")
#         return None

#gpt5.2

# api_client.py
import requests
import json
import time
from .config import API_KEY, API_BASE_URL, MODEL_NAME

# ========== Global Configuration ==========
TIMEOUT = 60  # Request timeout
MAX_RETRIES = 3  # Maximum retry attempts
RETRY_DELAY = 1  # Retry interval (seconds)
OPENAI_COMPATIBLE_HEADER = True  # OpenAI interface compatible mode

def call_modelscope_api_single(prompt_content, target_db_type):
    """
    GPT-5.2-adapted SQL generation function (retains original function name and parameters).
    Compatible with OpenAI official API standards, seamlessly replacing original logic.
    """
    if len(prompt_content) > 250000:
        raise RuntimeError(f"Single Prompt is too long ({len(prompt_content)} characters), exceeding API limits")
    
    # 1. Construct request headers (OpenAI standard)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"  # OpenAI standard authorization method
    }
    
    # 2. Construct message body (retain original system prompt logic, adapt to OpenAI format)
    messages = [
        {
            "role": "system",
            "content": f"You are a professional {target_db_type} SQL generation assistant, proficient in the syntax specifications of this database. The generated SQL must accurately implement the requirements, end with a semicolon, and return only the specified format content. Pay special attention to avoiding SQL that may cause infinite loops (such as infinite recursive queries, associated queries with excessive Cartesian products, etc.)."
        },
        {
            "role": "user",
            "content": prompt_content
        }
    ]
    
    # 3. Construct request parameters (fully aligned with OpenAI standards)
    data = {
        "model": MODEL_NAME,  # GPT-5.2 Model Name (e.g., "gpt-5.2" / "gpt-4o")
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1500,
        "top_p": 0.95,
        "frequency_penalty": 0.0,  # OpenAI standard parameters (added to ensure compatibility)
        "presence_penalty": 0.0,
        "stream": False,
        "stop": None  # Add stop words as needed
    }
    
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            # Call OpenAI/GPT-5.2 API
            response = requests.post(
                url=f"{API_BASE_URL}/chat/completions",  # OpenAI standard interface path
                headers=headers,
                json=data,
                timeout=TIMEOUT,
                # Optional: Add proxy (configure for access within China)
                # proxies={"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
            )
            response.raise_for_status()  # Raise HTTP error (4xx/5xx)
            result = response.json()
            
            # 4. Extract result (completely consistent with original logic)
            if result.get("choices") and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                raise RuntimeError(f"GPT-5.2 returned empty content: {json.dumps(result, ensure_ascii=False)}")
                
        except Exception as e:
            retry_count += 1
            error_detail = f"{str(e)}"
            # Capture response content (compatible with original exception logic)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail += f" | Response content: {e.response.text[:500]}"
                except:
                    pass
            
            # Raise exception if the last retry fails
            if retry_count >= MAX_RETRIES:
                raise RuntimeError(f"API call failed: {error_detail}") from e
            
            # Wait before retrying (exponential backoff optimization)
            time.sleep(RETRY_DELAY * retry_count)

def call_modelscope_analysis(prompt_content):
    """
    GPT-5.2-adapted semantic analysis function (retains original function name and parameters).
    General analysis call used for semantic verification.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    messages = [
        {
            "role": "system",
            "content": "You are a rigorous SQL code audit expert. Your task is to compare the user's natural language requirements with the generated SQL statements to determine if the SQL completely implements the requirements. Please analyze objectively and logically; do not fabricate reasons. Preferably return analysis results in JSON format, containing is_pass (boolean) and fail_reason (string) fields."
        },
        {
            "role": "user",
            "content": prompt_content
        }
    ]
    
    data = {
        "model": MODEL_NAME,  # GPT-5.2 Model Name
        "messages": messages,
        "temperature": 0.1,  # Low randomness ensures analysis accuracy
        "max_tokens": 1000,  # Reduced token requirement for analysis tasks
        "stream": False
    }
    
    try:
        response = requests.post(
            url=f"{API_BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=TIMEOUT,
            # Optional: Proxy configuration
            # proxies={"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get("choices") and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"].strip()
        else:
            print(f"⚠️ GPT-5.2 analysis interface returned empty content: {json.dumps(result, ensure_ascii=False)}")
            return None
            
    except Exception as e:
        error_detail = f"{str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail += f" | Response content: {e.response.text[:500]}"
            except:
                pass
        print(f"⚠️ Analysis API call failed: {error_detail}")
        return None