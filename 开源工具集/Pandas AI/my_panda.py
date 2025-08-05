import os
import pandasai as pai
from pandasai_litellm import LiteLLM
from pandasai.agent import Agent
import ast
import re
os.environ["DEEPSEEK_API_KEY"]="sk-578f63b08e74438692e3ebdb42b49934"
llm = LiteLLM(
    model="deepseek/deepseek-chat",
    stream=False
)

pai.config.set({"llm":llm})
# 创建示例DataFrame
        
df = pai.DataFrame({
    "country": ["United States", "United Kingdom", "France", "Germany", "Italy", "Spain", "Canada", "Australia", "Japan", "China"],
    "revenue": [5000, 3200, 2900, 4100, 2300, 2100, 2500, 2600, 4500, 7000]
})

# 使用pandasai的DataFrame包装原始DataFrame

agent = Agent([df])

# 定义问题
question = "Plot the histogram of countries showing for each one the gd. Use different colors for each bar"

# 生成代码并获取提示
code = agent.generate_code(question)

# 获取最新使用的提示
prompt = agent._state.last_prompt_used

# 打印提示内容
# print(prompt.render())
# 提问
print('hello\n')
response = df.chat(
    "Plot the histogram of countries showing for each one the gd. Use different colors for each bar",
)
# print(response)



########
if not isinstance(response, str):
    response = str(response)

# 处理反斜杠
response = re.sub(r'\\', r'\\\\', response)

# 定义提取SQL查询的函数
def _extract_sql_queries_from_code(code) -> list[str]:
    """
    Extract SQL query strings from Python code

    Args:
        code (str): Python code as a string.

    Returns:
        list: List of SQL query strings found in the code.
    """
    sql_queries = []

    class SQLQueryExtractor(ast.NodeVisitor):
        def visit_Assign(self, node):
            # Look for assignments where SQL queries might be defined
            if (
                isinstance(node.value, (ast.Str, ast.Constant))
                and isinstance(node.value.s, str)
                and any(
                    keyword in node.value.s.upper()
                    for keyword in ["SELECT", "WITH"]
                )
            ):
                sql_queries.append(node.value.s)
            self.generic_visit(node)

        def visit_Call(self, node):
            # Look for function calls where SQL queries might be passed
            for arg in node.args:
                if (
                    isinstance(arg, (ast.Str, ast.Constant))
                    and isinstance(arg.s, str)
                    and any(
                        keyword in arg.s.upper() for keyword in ["SELECT", "WITH"]
                    )
                ):
                    sql_queries.append(arg.s)
            self.generic_visit(node)

    # Parse the code into an AST and visit all nodes
    tree = ast.parse(code)
    SQLQueryExtractor().visit(tree)

    return sql_queries

# 从响应中提取SQL查询
sql_queries = _extract_sql_queries_from_code(response)

# 打印提取的SQL查询
for query in sql_queries:
    print(query)