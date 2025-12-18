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

def build_semantic_check_prompt(question, nl2_rewrite, sql, db_type):
    """
    构造语义验证Prompt (增强版)
    针对结构化的 nl2_rewrite 进行分块验证
    """
    return textwrap.dedent(f"""\
        ### 任务：SQL语义一致性审计
        
        你是一名严苛的数据库代码审计员。请对比“核心需求说明书(nl2_rewrite)”与“待验证SQL”，判断SQL是否**完全、准确**地实现了需求。
        
        #### 1. 核心需求说明书 (nl2_rewrite) - 验收标准
        注意：该内容包含具体的结构化分节（Source & Joins, Filters, Aggregation, Return），这是生成的唯一依据。
        --------------------------------------------------
        {nl2_rewrite}
        --------------------------------------------------
        
        #### 2. 原始问题 (参考背景)
        {question}
        
        #### 3. 待验证的 SQL ({db_type})
        {sql}
        
        #### 4. 审计步骤 (必须严格执行)
        请对照 `nl2_rewrite` 的各个分节逐一检查：
        1. **Check Filters (关键)**：SQL的 `WHERE` 子句是否包含 `--- Filters` 中列出的**所有**条件？(注意比较符号 > < = 及具体数值/字符串是否一致)。
        2. **Check Aggregation**：SQL的聚合方式（COUNT/SUM/AVG/DISTINCT）是否与 `--- Aggregation & Computation` 描述完全一致？
        3. **Check Return**：SQL的 `SELECT` 返回列是否与 `--- Return` 中要求的字段一致？(列名不要弄错)。
        4. **Check Joins**：SQL的表关联逻辑是否符合 `--- Source & Joins` 中的描述？
        
        #### 5. 输出格式
        请仅返回一个纯 JSON 对象，**严禁**包含 Markdown 格式符（如 ```json ... ```）：
        {{
            "status": "PASS" 或 "FAIL",
            "reason": "如果为FAIL，请指明是哪个分节(Filters/Return/Aggregation)未实现。例如：'Filters部分缺失：未过滤client.gender=F' 或 'Aggregation错误：缺少DISTINCT关键字'。如果为PASS，请保持为空字符串"
        }}
        """)

def build_logic_fix_prompt(question, nl2_rewrite, wrong_sql, analysis_reason, target_db_type):
    """
    构造逻辑修正Prompt (增强版)
    基于结构化需求和审计意见进行修复
    """
    return textwrap.dedent(f"""\
        ### 任务：修复 SQL 逻辑缺陷
        
        上一轮生成的 SQL 虽然语法正确，但在业务逻辑上未通过审计。请基于审计意见，严格按照 `nl2_rewrite` 的结构化要求重写 SQL。
        
        #### 1. 核心需求说明书 (标准答案)
        请仔细阅读以下分节，这是修复的根本依据：
        --------------------------------------------------
        {nl2_rewrite}
        --------------------------------------------------
        
        #### 2. 存在逻辑缺陷的 SQL
        {wrong_sql}
        
        #### 3. 审计意见 (缺陷分析)
        {analysis_reason}
        
        #### 4. 修复要求
        1. **精准定位**：根据审计意见，修改 SQL 中不符合 `nl2_rewrite` 对应分节的部分（通常是 WHERE 条件遗漏、SELECT 字段错误或聚合函数误用）。
        2. **保留正确部分**：不要重写已经在 `nl2_rewrite` 中定义正确且 SQL 中也实现正确的 Join 逻辑，除非它们是错误的根源。
        3. **语法合规**：必须生成严格符合 {target_db_type} 语法规范的 SQL，结尾加分号。
        4. **格式输出**：只返回 SQL 语句，格式如下：
        
        ### {target_db_type}
        [{target_db_type} SQL语句]
        """)