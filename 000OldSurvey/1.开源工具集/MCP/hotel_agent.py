# import asyncio

# from google import genai
# from google.genai.types import (
#     Content,
#     FunctionDeclaration,
#     GenerateContentConfig,
#     Part,
#     Tool,
# )

# from toolbox_core import ToolboxClient

# prompt = """
#   You're a helpful hotel assistant. You handle hotel searching, booking and
#   cancellations. When the user searches for a hotel, mention it's name, id,
#   location and price tier. Always mention hotel id while performing any
#   searches. This is very important for any operations. For any bookings or
#   cancellations, please provide the appropriate confirmation. Be sure to
#   update checkin or checkout dates if mentioned by the user.
#   Don't ask for confirmations from the user.
# """

# queries = [
#     "Find hotels in Basel with Basel in it's name.",
#     "Please book the hotel Hilton Basel for me.",
#     "This is too expensive. Please cancel it.",
#     "Please book Hyatt Regency for me",
#     "My check in dates for my booking would be from April 10, 2024 to April 19, 2024.",
# ]

# async def run_application():
#     async with ToolboxClient("http://127.0.0.1:5000") as toolbox_client:

#         # The toolbox_tools list contains Python callables (functions/methods) designed for LLM tool-use
#         # integration. While this example uses Google's genai client, these callables can be adapted for
#         # various function-calling or agent frameworks. For easier integration with supported frameworks
#         # (https://github.com/googleapis/mcp-toolbox-python-sdk/tree/main/packages), use the
#         # provided wrapper packages, which handle framework-specific boilerplate.
#         toolbox_tools = await toolbox_client.load_toolset("my-toolset")
#         genai_client = genai.Client(
#             vertexai=True, project="hotel-465803", location="us-central1"
#         )

#         genai_tools = [
#             Tool(
#                 function_declarations=[
#                     FunctionDeclaration.from_callable_with_api_option(callable=tool)
#                 ]
#             )
#             for tool in toolbox_tools
#         ]
#         history = []
#         for query in queries:
#             user_prompt_content = Content(
#                 role="user",
#                 parts=[Part.from_text(text=query)],
#             )
#             history.append(user_prompt_content)

#             response = genai_client.models.generate_content(
#                 model="gemini-2.0-flash-001",
#                 contents=history,
#                 config=GenerateContentConfig(
#                     system_instruction=prompt,
#                     tools=genai_tools,
#                 ),
#             )
#             history.append(response.candidates[0].content)
#             function_response_parts = []
#             for function_call in response.function_calls:
#                 fn_name = function_call.name
#                 # The tools are sorted alphabetically
#                 if fn_name == "search-hotels-by-name":
#                     function_result = await toolbox_tools[3](**function_call.args)
#                 elif fn_name == "search-hotels-by-location":
#                     function_result = await toolbox_tools[2](**function_call.args)
#                 elif fn_name == "book-hotel":
#                     function_result = await toolbox_tools[0](**function_call.args)
#                 elif fn_name == "update-hotel":
#                     function_result = await toolbox_tools[4](**function_call.args)
#                 elif fn_name == "cancel-hotel":
#                     function_result = await toolbox_tools[1](**function_call.args)
#                 else:
#                     raise ValueError("Function name not present.")
#                 function_response = {"result": function_result}
#                 function_response_part = Part.from_function_response(
#                     name=function_call.name,
#                     response=function_response,
#                 )
#                 function_response_parts.append(function_response_part)

#             if function_response_parts:
#                 tool_response_content = Content(role="tool", parts=function_response_parts)
#                 history.append(tool_response_content)

#             response2 = genai_client.models.generate_content(
#                 model="gemini-2.0-flash-001",
#                 contents=history,
#                 config=GenerateContentConfig(
#                     tools=genai_tools,
#                 ),
#             )
#             final_model_response_content = response2.candidates[0].content
#             history.append(final_model_response_content)
#             print(response2.text)

# asyncio.run(run_application())





# import asyncio
# import requests  # 替代 Google SDK，直接发 HTTP 请求
# from typing import Optional, List

# # ================ 1. 定义 DeepSeek API 调用函数 ================
# class DeepSeekAPI:
#     def __init__(self, api_key: str, model: str = "deepseek-chat"):
#         self.api_key = api_key
#         self.model = model
#         self.api_url = "https://api.deepseek.com/v1/chat/completions"  # DeepSeek 官方 API

#     def generate(self, prompt: str, max_tokens: int = 1024) -> str:
#         """
#         同步调用 DeepSeek API 生成文本
#         """
#         headers = {
#             "Authorization": f"Bearer {self.api_key}",
#             "Content-Type": "application/json"
#         }
#         payload = {
#             "model": self.model,
#             "messages": [{"role": "user", "content": prompt}],
#             "max_tokens": max_tokens,
#             "temperature": 0.7  # 控制生成随机性
#         }
#         try:
#             response = requests.post(self.api_url, headers=headers, json=payload)
#             response.raise_for_status()  # 检查 HTTP 错误
#             result = response.json()
#             return result["choices"][0]["message"]["content"]
#         except Exception as e:
#             print(f"DeepSeek API 调用失败: {e}")
#             return "（生成失败，请检查 API Key 和网络）"
        

# # ================ 2. 定义酒店助手逻辑 ================
# prompt_template = """
# You're a helpful hotel assistant. You handle hotel searching, booking and cancellations...
# Always mention hotel IDs while performing any searches...
# Don't ask for confirmations from the user.

# User query: {query}
# """

# queries = [
#     "Find hotels in Basel with Basel in it's name.",
#     "Can you book the Hilton Basel for me?",
#     "Oh wait, this is too expensive. Please cancel it and book the Hyatt Regency instead.",
#     "My check in dates would be from April 10, 2024 to April 19, 2024.",
#     "Which is the best hotel?"
# ]

# # ================ 3. 主逻辑（纯同步/异步调用 API） ================
# def run_hotel_assistant():
#     # 初始化 DeepSeek API（替换为你的实际 Key）
#     deepseek = DeepSeekAPI(api_key="sk-578f63b08e74438692e3ebdb42b49934")  

#     for query in queries:
#         # 拼接完整 Prompt
#         full_prompt = prompt_template.format(query=query)
#         # 调用 API 生成回复
#         response = deepseek.generate(full_prompt)
#         print(f"用户提问: {query}")
#         print(f"AI 回复: {response}\n")


# if __name__ == "__main__":

#     run_hotel_assistant()


import asyncio
import requests  
from typing import Optional, List


class DeepSeekAPI:
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.deepseek.com/v1/chat/completions"  # DeepSeek 官方 API

    def generate(self, prompt: str, max_tokens: int = 1024) -> str:
 
        print(f"传给 DeepSeek 的完整 Prompt:\n{prompt}\n")  

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7  
        }
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()  
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"DeepSeek API 调用失败: {e}")
            return "（生成失败，请检查 API Key 和网络）"


prompt_template = """
You're a helpful hotel assistant. You handle hotel searching, booking and cancellations...
Always mention hotel IDs while performing any searches...
Don't ask for confirmations from the user.

User query: {query}
"""

queries = [
    "Find hotels in Basel with Basel in it's name.",
    "Can you book the Hilton Basel for me?",
    "Oh wait, this is too expensive. Please cancel it and book the Hyatt Regency instead.",
    "My check in dates would be from April 10, 2024 to April 19, 2024.",
    "Which is the best hotel?"
]


def run_hotel_assistant():

    deepseek = DeepSeekAPI(api_key="sk-578f63b08e74438692e3ebdb42b49934")  

    for query in queries:
     
        full_prompt = prompt_template.format(query=query)
     
        response = deepseek.generate(full_prompt)
        print(f"用户提问: {query}")
        print(f"AI 回复: {response}\n")


if __name__ == "__main__":

    run_hotel_assistant()