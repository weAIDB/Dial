# prompt_builder.py
import textwrap
from typing import Dict, Any, Optional
from utils import truncate_content
from config import SUPPORTED_DBS


def get_dialect_specific_warnings(db_type: str) -> str:
    """
    获取特定数据库的负面约束警告（防坑指南）
    """
    db_type_lower = db_type.lower()
    warnings = []

    if "oracle" in db_type_lower:
        warnings = [
            "1. 【严禁使用 LIMIT】Oracle 不支持 `LIMIT`！必须使用 `FETCH FIRST n ROWS ONLY` (12c+) 或 `ROWNUM`。",
            "2. 【严禁表别名加 AS】`FROM table t` 是正确的，`FROM table AS t` 是错误的。",
            "3. 【字符串连接】必须使用 `||`，严禁使用 `CONCAT` (仅限两参) 或 `+`。",
            "4. 【日期处理】日期字面量必须用 `DATE 'YYYY-MM-DD'` 或 `TO_DATE`，严禁字符串直接比较。",
            "5. 【标识符】除非表名原本区分大小写，否则严禁给表名/列名加双引号。"
        ]
    elif "sql server" in db_type_lower:
        warnings = [
            "1. 【严禁使用 LIMIT】必须使用 `SELECT TOP n ...`。",
            "2. 【字符串连接】必须使用 `+`。",
            "3. 【日期提取】使用 `YEAR()`, `MONTH()` 等函数。"
        ]
    elif "sqlite" in db_type_lower:
        warnings = [
            "1. 【连接限制】只支持 `LEFT JOIN`，严禁 `RIGHT/FULL JOIN`。",
            "2. 【日期】使用 `strftime` 处理字符串日期。"
        ]
    elif "postgresql" in db_type_lower:
        warnings = [
            "1. 【引号】字符串用单引号 `'`，标识符用双引号 `\"`。",
            "2. 【模糊匹配】不区分大小写使用 `ILIKE`。"
        ]
    elif "mysql" in db_type_lower:
        warnings = [
            "1. 【标识符】使用反引号 `` ` ``。",
            "2. 【连接】使用 `CONCAT()`。"
        ]

    if warnings:
        return "\n   ".join(warnings)
    return "遵循标准SQL语法。"


def build_prompt(
        retrieval_item: Dict[str, Any],
        target_db_type: str,
        db_rule_content: Optional[str] = None,
        secondary_rag_content: Optional[str] = None,
        error_msg: Optional[str] = None,
        first_sql: Optional[str] = None
) -> str:
    """
    构造 Prompt，核心优化：强制绑定 true_tables_columns
    """
    is_secondary = bool(secondary_rag_content and error_msg and first_sql)
    dialect_warnings = get_dialect_specific_warnings(target_db_type)

    # [核心] 获取并格式化真实的表结构信息
    true_tc_str = retrieval_item.get("true_tables_columns", "")
    if true_tc_str:
        schema_display = f"""
        #### 【绝对真理】数据库 Schema 白名单 (Tables & Columns)
        **这是数据库中实际存在的列，你必须严格从中选择，严禁使用任何不在此列表中的列名！**
        **格式为 `表名.列名`：**
        --------------------------------------------------
        {true_tables_columns_formatter(true_tc_str)}
        --------------------------------------------------
        **常见错误警告**：
        - 不要猜测列名（例如：若白名单只有 `name`，绝对不要写 `director_name` 或 `company_name`）。
        - 注意 `id` 字段通常是 `xxx_id` 还是仅 `id`。
        """
    else:
        schema_display = "#### Schema: 未提供，请根据改写逻辑推断。"

    # --- 1. 语法参考 ---
    if not is_secondary:
        retrieval_results = retrieval_item.get("retrieval_results", {})
        target_grammar = retrieval_results.get(target_db_type, "无特定语法参考").strip()
        grammar_section = textwrap.dedent(f"""\
            ### 1. {target_db_type} 语法参考
            {target_grammar}
            """)
    else:
        grammar_section = textwrap.dedent(f"""\
            ### 1. 修正上下文 ({target_db_type})
            **上轮错误SQL**: 
            {first_sql}
            **报错信息**: 
            {error_msg}
            """)

    # --- 2. 规则/修正参考 ---
    if is_secondary:
        rule_section = textwrap.dedent(f"""\
            ### 2. 修正参考资料
            {secondary_rag_content if secondary_rag_content else "无"}
            """)
    else:
        rule_section = textwrap.dedent(f"""\
            ### 2. 完整语法规则
            {db_rule_content if db_rule_content else "无"}
            """)

    # --- 3. 需求与Schema (注入 Schema) ---
    requirement_section = textwrap.dedent(f"""\
        ### 3. 核心需求与数据定义
        #### 用户问题：
        {retrieval_item.get("question", "")}

        #### 逻辑改写 (NL2SQL Logic):
        {retrieval_item.get("nl2_rewrite", "")}

        {schema_display}
        """)

    # --- 4. 生成指令 ---
    dialect_instruction = f"【{target_db_type} 禁忌】：\n   {dialect_warnings}"

    generate_rules = [
        f"1. **方言严格**：生成符合 **{target_db_type}** 的SQL。",
        f"2. **列名准确性**：必须对照上述【Schema 白名单】，**逐字核对**表名和列名。如果白名单里是 `name`，你写了 `director_name`，会导致任务失败。",
        "3. **逻辑完整**：实现 NL2SQL Logic 中的所有过滤和聚合。",
        f"{dialect_instruction}",
        f"5. **输出格式**：\n### {target_db_type}\n[{target_db_type} SQL语句]"
    ]

    requirement_section += "### 4. 最终指令\n" + "\n".join(generate_rules)

    full_prompt = grammar_section + rule_section + requirement_section
    return truncate_content(full_prompt, max_length=200000).strip()


def build_logic_fix_prompt(question, nl2_rewrite, wrong_sql, analysis_reason, target_db_type, true_tables_columns=None):
    """
    逻辑修正 Prompt
    """
    dialect_warnings = get_dialect_specific_warnings(target_db_type)

    schema_info = ""
    if true_tables_columns:
        schema_info = textwrap.dedent(f"""\
        #### 【Schema 白名单】请修正列名错误
        --------------------------------------------------
        {true_tables_columns_formatter(true_tables_columns)}
        --------------------------------------------------
        """)

    return textwrap.dedent(f"""\
        ### 任务：修复 SQL 逻辑缺陷 ({target_db_type})

        #### 1. 核心需求
        {nl2_rewrite}

        {schema_info}

        #### 2. 错误 SQL
        {wrong_sql}

        #### 3. 失败原因
        {analysis_reason}

        #### 4. 修复指令
        1. 优先检查 SQL 中的**列名**是否在【Schema 白名单】中。如果不在，请替换为白名单中最相似的列（例如将 `director_name` 改为 `name`）。
        2. 修正逻辑问题（Filters, Aggregation 等）。
        3. {dialect_warnings}

        **输出格式**：
        ### {target_db_type}
        ```sql
        SELECT ... ;
        ```
        """)


def build_semantic_check_prompt(question, nl2_rewrite, sql, db_type):
    """
    构造语义验证Prompt
    """
    return textwrap.dedent(f"""\
        ### 任务：SQL 语义一致性严格审计

        你是一名代码审计专家。你的任务是验证生成的 **{db_type} SQL** 是否严格遵循需求定义。

        #### 1. 核心需求说明书 (标准)
        --------------------------------------------------
        {nl2_rewrite}
        --------------------------------------------------

        #### 2. 待验证的 SQL (Target: {db_type})
        {sql}

        #### 3. 审计规则
        1. **Source & Joins**: 检查表名、连接是否正确。
        2. **Filters**: 检查 WHERE 条件是否完全一致（不多不少）。
        3. **Aggregation**: 检查计算逻辑。
        4. **Return**: 检查 SELECT 列是否对应。

        #### 4. 输出格式
        仅返回 JSON 对象：
        {{
            "status": "PASS" 或 "FAIL",
            "reason": "失败原因（如：Filters错误：遗漏了日期筛选...）"
        }}
        """)





def true_tables_columns_formatter(raw_str):
    """辅助函数：将逗号分隔的 strings 格式化为易读列表"""
    if not raw_str: return ""
    # 假设格式是 "table.col,table.col"
    try:
        items = raw_str.split(',')
        # 简单按表分组
        tables = {}
        for item in items:
            if '.' in item:
                t, c = item.split('.', 1)
                tables.setdefault(t.strip(), []).append(c.strip())

        output = []
        for t, cols in tables.items():
            output.append(f"- 表 `{t}`: [{', '.join(cols)}]")
        return "\n".join(output)
    except:
        return raw_str