# prompt_builder.py
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
        """)