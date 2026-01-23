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
            "1. 【保留字灾难】Schema中若包含 `date`, `order`, `number`, `group`, `level` 等保留字列名，SQL中**必须**使用双引号包裹（例如 `t.\"date\"`），否则必报 ORA-01747！",
            "2. 【严禁使用 LIMIT】Oracle 不支持 `LIMIT`！必须使用 `FETCH FIRST n ROWS ONLY` (12c+) 或 `ROWNUM`。",
            "3. 【严禁表别名加 AS】`FROM table t` 是正确的，`FROM table AS t` 是错误的。",
            "4. 【日期处理】日期字面量必须用 `DATE 'YYYY-MM-DD'` 或 `TO_DATE`，严禁字符串直接比较。",
            "5. 【字符串连接】必须使用 `||`，严禁使用 `CONCAT` (仅限两参) 或 `+`。",
            "6. 【LISTAGG限制】使用 `LISTAGG` 时，若内容过长可能报错，但在本任务中优先保证逻辑正确即可。"
        ]
    elif "sql server" in db_type_lower:
        warnings = [
            "1. 【保留字】若列名为 `date` 或 `user` 等，请使用方括号包裹，如 `[date]`。",
            "2. 【严禁使用 LIMIT】必须使用 `SELECT TOP n ...`。",
            "3. 【字符串连接】必须使用 `+`。"
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
    构造 Prompt
    核心优化：
    1. 直接注入原始 true_tables_columns (不经过 Python 格式化)。
    2. 引入“混合约束机制”：普通属性严格查表（解决ID=3幻觉），Join键允许推断（解决ID=6缺失）。
    3. 增加“通用命名映射”提示。
    """
    is_secondary = bool(secondary_rag_content and error_msg and first_sql)
    dialect_warnings = get_dialect_specific_warnings(target_db_type)

    # [核心] 获取真实的表结构信息 (Raw String)
    # 直接透传，不进行任何 Python 侧的格式化处理
    true_tc_str = retrieval_item.get("true_tables_columns", "")
    
    if true_tc_str:
        schema_display = f"""
        #######################################################################
        ### 【CRITICAL】DATABASE SCHEMA KNOWLEDGE (参考标准)
        #######################################################################
        **这是检索到的已知表列清单。数据格式**：`表名.列名, ...`
        
        [SCHEMA START]
        {true_tc_str}
        [SCHEMA END]
        
        **列名决策逻辑（必须执行）**：
        
        1. **普通属性列（严格匹配 & 通用名优先）**：
           - **解决幻觉**：如果 SQL 需要 "Company Name"，但 Schema 中 `companies` 表只有 `name` 列，**必须使用 `name`**，绝对不要编造 `company_name`。
           - **规则**：优先在 Schema 中寻找 `name`, `title`, `description`, `value` 等通用列名。
           
        2. **关联键（允许智能推断）**：
           - **解决缺失**：如果在进行表连接（JOIN）时，发现列表中缺失了显而易见的主键或外键（例如 `users` 表漏了 `user_id`），**允许**根据 SQL 标准命名规范推断主键名称（如 `user_id` 或 `id`），不要为了强行匹配白名单而使用错误的列（如用 `user_name` 去 Join）。
        #######################################################################
        """
    else:
        schema_display = f"""
        #### Schema: 未提供详细列名
        **注意**：由于未提供 Schema，请根据 SQL 通用命名规范进行推断。
        - 猜测列名时，优先尝试最通用的名称（如 `name` 而非 `company_name`）。
        - 注意 Oracle 数据库对保留字敏感。
        """

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
        f"2. **列名策略**：\n   - **属性列**：严格查表。若找不到 `xxx_name`，请检查是否就是 `name`。\n   - **Join键**：若 Schema 缺失 ID 列，允许合理推断。",
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
        #### 【Schema 参考 (Whitelist)】
        [SCHEMA_START]
        {true_tables_columns}
        [SCHEMA_END]
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
        1. **列名修正**：
           - 仔细检查报错的列名（如 `company_name`）。
           - 对照 [SCHEMA]：如果表中只有 `name`，请立即替换为 `name`。
           - 只有在 [SCHEMA] 中完全找不到对应列，且该列是 JOIN 必须的主键时，才允许推断 `id` 字段。
        2. **逻辑修正**：根据失败原因调整 WHERE 条件或聚合逻辑。
        3. {dialect_warnings}

        **输出格式**：
        ### {target_db_type}
        ```sql
        SELECT ... ;
        ```
        """)


def build_semantic_check_prompt(question, nl2_rewrite, sql, db_type):
    """
    构造语义验证Prompt (无需修改)
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