# rag_retrieval.py
import re
from config import RULES_ROOT_DIR, FUNCTIONAL_ROOT_DIR, DB_TYPE_TO_RULE_FILE, MAGIC_SIMILARITY_THRESHOLD # <--- 导入阈值
import os
import numpy as np
# 导入RAG相关组件
try:
    from rag_fixed_chunk import (
        embedding_model,
        HomyMarkerSplitter,
        Chroma,
        format_retrieval_result
    )
    from langchain_core.output_parsers import StrOutputParser
    from langchain_community.document_loaders import TextLoader
    from operator import itemgetter
    from langchain_core.runnables import RunnablePassthrough
except ImportError as e:
    raise RuntimeError(f"无法导入rag_fixed_chunk.py中的组件，请检查路径") from e

def secondary_rag_retrieval(question, error_msg, db_type):
    """
    二次RAG检索（返回1个最相关chunk）  # 注释修改：2→1
    适配rag_fixed_chunk.py的实际实现：单文件加载+临时向量库+固定分割器
    """
    try:
        # 1. 构建检索查询（融合问题+错误信息，提升相关性）
        retrieval_query = f"问题：{question} | SQL执行错误：{error_msg} | 关键词：死循环、超时、查询优化、避免笛卡尔积、递归查询限制、索引优化、查询性能"
        print(f"二次检索查询：{retrieval_query[:100]}...")
        
        # 2. 获取目标数据库的规则文件路径
        rule_filename = DB_TYPE_TO_RULE_FILE[db_type]
        rule_file_path = os.path.join(RULES_ROOT_DIR, rule_filename)
        if not os.path.exists(rule_file_path):
            print(f"⚠️ 规则文件不存在：{rule_file_path}")
            return "无相关语法参考"
        
        # 3. 加载单个规则文件
        loader = TextLoader(rule_file_path, encoding='utf-8')
        docs = loader.load()
        if not docs:
            print(f"⚠️ 规则文件{rule_file_path}加载后无内容")
            return "无相关语法参考"
        
        # 4. 用HomyMarkerSplitter分割文档
        text_splitter = HomyMarkerSplitter()
        split_docs = text_splitter.split_documents(docs)
        print(f"规则文件分割为 {len(split_docs)} 个文档块")
        
        # 校验文档块数量：从2→1
        if len(split_docs) < 1:
            print(f"⚠️ 文档块数量不足1个，仅获取{len(split_docs)}个")
        
        # 5. 创建临时向量库
        temp_vector_store = Chroma(
            embedding_function=embedding_model,
            persist_directory=None  # 临时向量库，退出即销毁
        )
        temp_vector_store.add_documents(split_docs)
        
        # 6. 构建检索器（强制返回1个最相关chunk）  # 核心修改：k=1
        temp_retriever = temp_vector_store.as_retriever(
            search_kwargs={"k": 2}
        )
        
        # 7. 构建检索链
        temp_chain = (
            {"question": RunnablePassthrough()}
            | RunnablePassthrough.assign(context=itemgetter("question") | temp_retriever)
            | format_retrieval_result
            | StrOutputParser()
        )
        
        # 8. 执行检索
        retrieval_result = temp_chain.invoke(retrieval_query)
        
        # 9. 处理检索结果
        if "No relevant content retrieved" in retrieval_result:
            # 返回格式调整：仅保留1个参考块
            return "=== 相关语法参考 1 ===\n无相关语法参考"
        
        # 解析检索结果中的chunk
        chunk_pattern = r'=== Relevant Chunk (\d+): (.*?) ===\n([\s\S]*?)(?=\n=== |$)'
        matches = re.findall(chunk_pattern, retrieval_result, re.DOTALL)
        
        # 格式化前1个chunk  # 修改：[:2]→[:1]
        formatted_chunks = []
        for i, (chunk_idx, title, content) in enumerate(matches[:1], 1):
            truncated_content = content[:10000] + "..." if len(content) > 10000 else content
            formatted_chunks.append(
                f"=== 相关语法参考 {i}（{title}）===\n{truncated_content.strip()}"
            )
        
        # 不足1个时补充空chunk  # 修改：补到1个而非2个
        while len(formatted_chunks) < 1:
            formatted_chunks.append(f"=== 相关语法参考 {len(formatted_chunks)+1} ===\n无更多相关语法参考")
        
        final_retrieval = "\n\n".join(formatted_chunks)
        print(f"二次检索结果（前200字符）：{final_retrieval[:20000]}...")
        return final_retrieval
    
    except Exception as e:
        error_detail = str(e)[:200]
        print(f"⚠️ 二次RAG检索失败：{error_detail}...")
        # 异常返回格式调整：仅1个参考块
        return (
            f"=== 相关语法参考 1 ===\n检索失败：{error_detail}（无相关语法参考）"
        )
        
def calculate_cosine_similarity(text1, text2):
    """计算两段文本的余弦相似度"""
    try:
        # 使用 embedding_model (来自 rag_fixed_chunk)
        vec1 = embedding_model.embed_query(text1)
        vec2 = embedding_model.embed_query(text2)
        
        # 计算余弦相似度
        dot_product = np.dot(vec1, vec2)
        norm_a = np.linalg.norm(vec1)
        norm_b = np.linalg.norm(vec2)
        return dot_product / (norm_a * norm_b)
    except Exception as e:
        print(f"⚠️ 相似度计算失败: {e}")
        return 0.0

def save_magic_guideline(guideline_text, nl2_rewrite, db_type):
    """
    根据相似度判断并保存 Magic 生成的 Guideline
    """
    if not guideline_text:
        return

    # 1. 计算 Guideline 内容与 nl2_rewrite 的相似度
    # Guideline通常包含 "Reason: ..." 或具体的规则描述，我们提取主要部分
    similarity = calculate_cosine_similarity(guideline_text, nl2_rewrite)
    
    print(f"🔍 Guideline 与 需求(nl2_rewrite) 相似度: {similarity:.4f}")

    # 2. 决定保存路径
    if similarity >= MAGIC_SIMILARITY_THRESHOLD:
        # 高相似度 -> 存入 Functional_dialect
        target_dir = FUNCTIONAL_ROOT_DIR
        print(f"   -> 判定为【功能类】知识 (Sim >= {MAGIC_SIMILARITY_THRESHOLD:})")
    else:
        # 低相似度 -> 存入 Rule_based_dialect
        target_dir = RULES_ROOT_DIR
        print(f"   -> 判定为【规则类】知识 (Sim < {MAGIC_SIMILARITY_THRESHOLD:})")

    # 3. 构造保存路径
    filename = DB_TYPE_TO_RULE_FILE.get(db_type, f"{db_type}.txt")
    file_path = os.path.join(target_dir, filename)

    # 4. 追加写入
    try:
        # 确保目录存在
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write("\n\n" + guideline_text)
        print(f"✅ Guideline 已追加保存至: {file_path}")
    except Exception as e:
        print(f"❌ 保存 Guideline 失败: {e}")