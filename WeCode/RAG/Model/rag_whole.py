from operator import itemgetter
from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import TextSplitter


# 1. 自定义分割器：按@homy@标记分割，同时提取标题作为元数据
class HomyMarkerSplitter(TextSplitter):
    """基于@homy@标记的分割器，支持提取多级标题作为元数据"""
    def split_text(self, text: str) -> List[str]:
        # 处理单文本分割，复用split_documents逻辑
        doc = Document(page_content=text, metadata={})
        split_docs = self.split_documents([doc])
        return [d.page_content for d in split_docs]

    def split_documents(self, documents: List[Document]) -> List[Document]:
        split_docs = []
        for doc in documents:
            # 按@homy@分割文本，过滤空块
            chunks = [chunk.strip() for chunk in doc.page_content.split("@homy@") if chunk.strip()]
            
            for chunk in chunks:
                # 提取标题（取块中第一行非空内容作为标题）
                lines = [line.strip() for line in chunk.splitlines() if line.strip()]
                title = lines[0] if lines else "No Title"
                
                # 构建包含标题元数据的文档块
                split_docs.append(Document(
                    page_content=chunk,
                    metadata={
                        **doc.metadata,  # 继承原文档元数据（如文件路径）
                        "title": title,  # 新增标题元数据
                        "source": doc.metadata.get("source", "Unknown Source")  
                    }
                ))
        return split_docs


# 2. 初始化模型和向量库（修改嵌入模型路径并优化加载配置）
embedding_model = HuggingFaceEmbeddings(
    model_name=r"C:\Users\17376\Desktop\方言提取器\model4.0\BAAI\bge-large-en-v1___5",
    model_kwargs={
        "device": "cuda" if __import__("torch").cuda.is_available() else "cpu",  # 自动选择GPU/CPU
        "trust_remote_code": True  # 兼容模型自定义配置
    },
    encode_kwargs={
        "normalize_embeddings": True  # BGE模型建议开启，提升检索精度
    }
)

file_dir = Path('knowledge')
text_splitter = HomyMarkerSplitter()

# 初始化向量库（指定持久化路径）
vector_store = Chroma(
    embedding_function=embedding_model,
    persist_directory="./chroma_E2"
)
retriever = vector_store.as_retriever(
    search_kwargs={"k": 4}  # 返回最相关的4个结果
)


# 3. 构建检索链：优化输出格式，显示标题和内容
def format_retrieval_result(result: dict) -> str:
    """格式化检索结果，显示标题和内容"""
    context_docs = result.get("context", [])
    if not context_docs:
        return "No relevant content retrieved"
    
    formatted = []
    for i, doc in enumerate(context_docs, 1):
        title = doc.metadata.get("title", "No Title")
        content = doc.page_content
        # 截断过长内容，保留可读性
        truncated_content = content[:12700] + "..." if len(content) > 12700 else content
        formatted.append(f"=== Relevant Chunk {i}: {title} ===\n{truncated_content}")
    
    return "\n\n".join(formatted)


chain = (
    {"question": RunnablePassthrough()}
    | RunnablePassthrough.assign(context=itemgetter("question") | retriever)
    | format_retrieval_result  # 使用自定义格式化函数
    | StrOutputParser()
)


# 4. 初始化知识库并测试
if __name__ == '__main__':
    # # 首次运行请取消注释，加载文档到向量库（仅需执行一次）
    # docs = DirectoryLoader(
    #     str(file_dir),
    #     loader_cls=TextLoader,
    #     loader_kwargs={"encoding": "utf-8"}
    # ).load()
    # split_docs = text_splitter.split_documents(docs)
    # vector_store.add_documents(split_docs)
    # print("Knowledge base initialized, number of document chunks loaded:", len(split_docs))
    
    # 测试检索：适配英文知识库的查询
    query = "Among the records in the schools and satscores tables where schools.CDSCode matches satscores.cds:\n\nFilter the records where:\n- schools.OpenDate is between '1980-01-01' and '1980-12-31' (i.e., the year of schools.OpenDate is 1980).\n- schools.City is 'Fresno'.\n\nCompute:\n- total_test_takers = SUM of satscores.NumTstTakr for the filtered records.\n- total_schools = COUNT of DISTINCT schools.CDSCode for the filtered records.\n- average_test_takers = total_test_takers / total_schools.\n\nReturn:\n- average_test_takers."
    print(f"Retrieval Query: {query}\n")
    print(chain.invoke(query))