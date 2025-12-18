import json
from typing import List, Dict, Tuple, Set
from pathlib import Path

import numpy as np
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import sys

# 适配新的rag_whole.py路径
rag_dir = Path(r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\Model4.0_rag")
sys.path.append(str(rag_dir))
from rag_whole import chain, retriever  # 从新路径导入RAG链和检索器


# 1. 加载评估数据集
def load_evaluation_dataset(file_path: str) -> List[Dict]:
    """加载JSON格式的评估数据集（英文版本）"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# 2. 定义评估指标计算函数（适配英文内容，严格遵循新指标定义）
class RAGEvaluator:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self._init_prompts()  # 初始化所有指标的英文提示词模板

    def _init_prompts(self):
        """初始化各指标的评估提示词（英文版本，保持原逻辑）"""
        # 2.1 提取理想答案的关键信息（用于上下文召回率和答案正确性）
        self.extract_ideal_keyinfo_prompt = PromptTemplate(
            template="""Extract all key information from the following ideal answer and return it as a list.
Key information definition: Core facts, data, or logic that support the correctness of the answer and cannot be omitted.
Ideal answer: {ideal_answer}
Output format: JSON list, e.g., ["Key info 1", "Key info 2"]
Return only JSON: {{"key_infos": [...]}}""",
            input_variables=["ideal_answer"]
        )

        # 2.2 上下文召回率评估（覆盖关键信息比例）
        self.context_recall_prompt = PromptTemplate(
            template="""Determine if the retrieved context covers the following key information and return the indices of covered key information.
Key information list (index starts from 0): {key_infos}
Retrieved context: {context}
Coverage definition: The context explicitly contains the complete statement of the key information or it can be directly inferred.
Output format: JSON list, e.g., [0, 2] means covering key information at indices 0 and 2
Return only JSON: {{"covered_indices": [...]}}""",
            input_variables=["key_infos", "context"]
        )

        # 2.3 上下文相关性评估（相关片段比例）
        self.context_relevance_prompt = PromptTemplate(
            template="""Split the following context into semantically complete fragments (by natural paragraphs or logical units) and mark the indices of fragments relevant to the query.
Query: {query}
Context: {context}
Fragment splitting requirement: Each fragment is a complete semantic unit (e.g., a sentence or a group of short sentences)
Relevance definition: The fragment content directly answers the query or is related to the core intent of the query
Output format: JSON, e.g., {{"total_fragments": 3, "relevant_indices": [0, 2]}}
Return only JSON: {{"total_fragments": int, "relevant_indices": [...]}}""",
            input_variables=["query", "context"]
        )

        # 2.4 答案忠实度评估（基于上下文的事实比例）
        self.faithfulness_prompt = PromptTemplate(
            template="""Disassemble all facts from the answer and determine if each fact can be inferred from the context.
Answer: {answer}
Context: {context}
Fact definition: Specific information stated in the answer (e.g., "MySQL uses LIMIT for pagination")
Inferable definition: The context explicitly contains the fact or it can be directly derived from the context information
Output format: JSON, e.g., {{"total_facts": 3, "faithful_indices": [0, 1]}}
Return only JSON: {{"total_facts": int, "faithful_indices": [...]}}""",
            input_variables=["answer", "context"]
        )

        # 2.5 答案相关性评估（相关模拟问题比例）
        self.answer_relevance_prompt = PromptTemplate(
            template="""Derive all possible simulated questions from the answer and mark the indices of simulated questions relevant to the original query.
Original query: {query}
Answer: {answer}
Simulated question definition: Questions that the answer can directly answer (e.g., the answer "MySQL uses LIMIT for pagination" can derive "How does MySQL implement pagination?")
Relevance definition: The simulated question is consistent with the core intent of the original query (e.g., if the original query asks about "pagination syntax", the simulated question "How to paginate?" is relevant)
Output format: JSON, e.g., {{"total_sim_questions": 3, "relevant_indices": [0, 2]}}
Return only JSON: {{"total_sim_questions": int, "relevant_indices": [...]}}""",
            input_variables=["query", "answer"]
        )

        # 2.6 答案正确性评估（覆盖理想关键信息比例）
        self.answer_correctness_prompt = PromptTemplate(
            template="""Determine if the generated answer covers the following key information and return the indices of covered key information.
Key information list (index starts from 0): {key_infos}
Generated answer: {generated_answer}
Coverage definition: The answer explicitly contains the complete statement of the key information or it can be directly inferred.
Output format: JSON list, e.g., [0, 2] means covering key information at indices 0 and 2
Return only JSON: {{"covered_indices": [...]}}""",
            input_variables=["key_infos", "generated_answer"]
        )

        # 通用JSON解析器
        self.json_parser = JsonOutputParser()

    def extract_key_infos(self, ideal_answer: str) -> List[str]:
        """从英文理想答案中提取关键信息（用于上下文召回率和答案正确性）"""
        chain = self.extract_ideal_keyinfo_prompt | self.llm | self.json_parser
        result = chain.invoke({"ideal_answer": ideal_answer})
        return result.get("key_infos", [])

    def evaluate_context_recall(self, context_docs: List[Dict], key_infos: List[str]) -> float:
        """
        Context recall = Number of key information covered by context / Total number of key information in ideal answer
        Value range: 0-1
        """
        if not key_infos:
            return 1.0  # Default 100% coverage when no key info
        context_text = "\n\n".join([doc.page_content for doc in context_docs]) if context_docs else ""
        
        chain = self.context_recall_prompt | self.llm | self.json_parser
        result = chain.invoke({"key_infos": key_infos, "context": context_text})
        covered_count = len(result.get("covered_indices", []))
        return covered_count / len(key_infos)

    def evaluate_context_relevance(self, query: str, context_docs: List[Dict]) -> float:
        """
        Context relevance = Number of context fragments relevant to the question / Total number of context fragments
        Value range: 0-1
        """
        if not context_docs:
            return 0.0  # Relevance is 0 when no context
        context_text = "\n\n".join([doc.page_content for doc in context_docs])
        
        chain = self.context_relevance_prompt | self.llm | self.json_parser
        result = chain.invoke({"query": query, "context": context_text})
        total = result.get("total_fragments", 0)
        relevant_count = len(result.get("relevant_indices", []))
        
        return relevant_count / total if total > 0 else 0.0

    def evaluate_faithfulness(self, context_docs: List[Dict], answer: str) -> float:
        """
        Answer faithfulness = Number of facts inferable from context / Total number of facts disassembled from answer
        Value range: 0-1
        """
        if not answer.strip():
            return 0.0  # Faithfulness is 0 when no answer
        context_text = "\n\n".join([doc.page_content for doc in context_docs]) if context_docs else ""
        
        chain = self.faithfulness_prompt | self.llm | self.json_parser
        result = chain.invoke({"answer": answer, "context": context_text})
        total_facts = result.get("total_facts", 0)
        faithful_count = len(result.get("faithful_indices", []))
        
        return faithful_count / total_facts if total_facts > 0 else 0.0

    def evaluate_answer_relevance(self, query: str, answer: str) -> float:
        """
        Answer relevance = Number of simulated questions relevant to the actual query / Total number of simulated questions derived from the actual answer
        Value range: 0-1
        """
        if not answer.strip():
            return 0.0  # Relevance is 0 when no answer
        
        chain = self.answer_relevance_prompt | self.llm | self.json_parser
        result = chain.invoke({"query": query, "answer": answer})
        total_sim = result.get("total_sim_questions", 0)
        relevant_sim_count = len(result.get("relevant_indices", []))
        
        return relevant_sim_count / total_sim if total_sim > 0 else 0.0

    def evaluate_answer_correctness(self, key_infos: List[str], generated_answer: str) -> float:
        """
        Answer correctness = Number of key information covered by actual answer / Total number of key information in reference answer
        Value range: 0-1
        """
        if not key_infos:
            return 1.0  # Default 100% correctness when no key info
        
        chain = self.answer_correctness_prompt | self.llm | self.json_parser
        result = chain.invoke({"key_infos": key_infos, "generated_answer": generated_answer})
        covered_count = len(result.get("covered_indices", []))
        return covered_count / len(key_infos)


# 3. 执行评估（适配英文内容）
def run_evaluation(dataset: List[Dict], evaluator: RAGEvaluator) -> Tuple[Dict, List[Dict]]:
    # 初始化指标存储
    metrics = {
        "context_recall": [],          # 上下文召回率
        "context_relevance": [],       # 上下文相关性
        "faithfulness": [],            # 答案忠实度
        "answer_relevance": [],        # 答案相关性
        "answer_correctness": []       # 答案正确性
    }
    detailed_results = []

    for idx, sample in enumerate(dataset):
        print(f"Evaluating sample {idx + 1}/{len(dataset)}: {sample['query']}")
        
        # 1. 运行RAG系统获取结果（适配英文知识库）
        query = sample["query"]
        retrieved_docs = retriever.invoke(query)  # 检索英文知识库上下文
        generated_answer = chain.invoke(query)    # 生成英文答案
        ideal_answer = sample["ideal_answer"]     # 英文理想答案

        # 2. 提取理想答案的关键信息（英文）
        key_infos = evaluator.extract_key_infos(ideal_answer)
        print(f"  Number of extracted key information: {len(key_infos)}")

        # 3. 计算各指标（严格按原定义，适配英文内容）
        context_recall = evaluator.evaluate_context_recall(retrieved_docs, key_infos)
        context_relevance = evaluator.evaluate_context_relevance(query, retrieved_docs)
        faithfulness = evaluator.evaluate_faithfulness(retrieved_docs, generated_answer)
        answer_relevance = evaluator.evaluate_answer_relevance(query, generated_answer)
        answer_correctness = evaluator.evaluate_answer_correctness(key_infos, generated_answer)

        # 4. 保存单样本结果
        metrics["context_recall"].append(context_recall)
        metrics["context_relevance"].append(context_relevance)
        metrics["faithfulness"].append(faithfulness)
        metrics["answer_relevance"].append(answer_relevance)
        metrics["answer_correctness"].append(answer_correctness)

        detailed_results.append({
            "query": query,
            "key_infos": key_infos,  # 保存提取的英文关键信息
            "context_recall": context_recall,
            "context_relevance": context_relevance,
            "faithfulness": faithfulness,
            "answer_relevance": answer_relevance,
            "answer_correctness": answer_correctness,
            "generated_answer": generated_answer
        })

    # 计算总体指标（平均值）
    overall = {
        "avg_context_recall": np.mean(metrics["context_recall"]),
        "avg_context_relevance": np.mean(metrics["context_relevance"]),
        "avg_faithfulness": np.mean(metrics["faithfulness"]),
        "avg_answer_relevance": np.mean(metrics["answer_relevance"]),
        "avg_answer_correctness": np.mean(metrics["answer_correctness"])
    }
    return overall, detailed_results


# 4. 主函数（使用DeepSeek模型评估英文内容）
if __name__ == "__main__":
    # 配置评估参数（适配英文版本文件）
    EVAL_DATASET_PATH = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\Model4.0_rag\access\access.json"  # 英文评估数据集
    DEEPSEEK_API_KEY = "sk-578f63b08e74438692e3ebdb42b49934"  # DeepSeek API密钥

    # 初始化DeepSeek评估模型（兼容OpenAI API，处理英文内容）
    eval_llm = ChatOpenAI(
        model_name="deepseek-chat",
        temperature=0,  # 固定温度确保评估稳定性
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com/v1"
    )

    # 加载英文数据集和评估器
    dataset = load_evaluation_dataset(EVAL_DATASET_PATH)
    evaluator = RAGEvaluator(eval_llm)

    # 执行评估（适配英文RAG系统）
    overall_metrics, detailed_results = run_evaluation(dataset, evaluator)

    # 输出总体指标
    print("\n===== Overall Evaluation Metrics (0-1, higher is better) =====")
    for metric, score in overall_metrics.items():
        print(f"{metric}: {score:.4f}")

    # 保存详细结果（英文内容）
    with open("evaluation_results_english.json", "w", encoding="utf-8") as f:
        json.dump({
            "overall_metrics": overall_metrics,
            "detailed_results": detailed_results
        }, f, ensure_ascii=False, indent=2)
    print("\nDetailed results saved to evaluation_results_english.json")