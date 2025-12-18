# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm  # 进度条支持
import os

# ========== 路径配置 ==========
# RAG模块所在目录（修正重复导入问题）
RAG_DIR = Path(r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\rag\Model4.0_rag")
# 输入JSON文件路径（更新为新的源文件路径）
INPUT_JSON_PATH = Path(r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\translator4.0\nl2rag\nl2.0.json")
# 输出JSON文件路径（适配多库检索结果的新文件名）
OUTPUT_JSON_PATH = Path(r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\translator4.0\输出结果\第三次测试结果\nl2rag_multi_db_result.json")

# ========== 添加RAG目录到Python路径 ==========
sys.path.append(str(RAG_DIR.resolve()))

# ========== 导入RAG模块（适配新的MultiDBDocumentRetriever） ==========
try:
    from rag_fixed_chunk import (
        MultiDBDocumentRetriever,
        load_input_data as rag_load_data,  # 兼容rag模块的加载函数
        batch_retrieve_from_json as rag_batch_retrieve
    )
    print("[OK] 成功导入rag_fixed_chunk模块（多数据库检索器）")
except ImportError as e:
    print(f"[ERROR] 导入RAG模块失败: {e}")
    sys.exit(1)
except AttributeError as e:
    print(f"[ERROR] rag_fixed_chunk模块中找不到指定对象: {e}")
    sys.exit(1)

# ========== 核心函数（适配多库检索逻辑） ==========
def load_input_data(file_path: Path) -> List[Dict]:
    """加载输入JSON数据（保留原验证逻辑，对齐新提示风格）"""
    if not file_path.exists():
        raise FileNotFoundError(f"输入文件不存在: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 验证数据格式（保留核心字段验证，新增字段兼容）
    if not isinstance(data, list):
        raise ValueError("输入JSON必须是数组格式")
    
    valid_data = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            print(f"⚠️  第{idx}条数据不是字典，跳过")
            continue
        # 核心字段必须存在
        if "question" not in item or "nl2_rewrite" not in item:
            print(f"⚠️  第{idx}条数据缺少question或nl2_rewrite字段，跳过")
            continue
        # 可选字段提醒（对齐新提示风格）
        if "question_id" not in item:
            print(f"⚠️  第{idx}条数据缺少question_id字段，将设为None")
        if "difficulty" not in item:
            print(f"⚠️  第{idx}条数据缺少difficulty字段，将设为None")
        valid_data.append(item)
    
    print(f"✅ 加载并验证输入数据完成，有效条目数: {len(valid_data)}/{len(data)}")
    return valid_data

def process_multi_db_rag_queries(input_data: List[Dict]) -> List[Dict]:
    """处理多数据库RAG检索请求（适配新的MultiDBDocumentRetriever）"""
    # 初始化多数据库检索器（自动加载各库向量库）
    print("\n🔄 初始化多数据库向量库...")
    try:
        multi_db_retriever = MultiDBDocumentRetriever()
    except Exception as e:
        print(f"[ERROR] 初始化多数据库检索器失败: {e}")
        sys.exit(1)
    
    # 执行批量多库检索（复用rag模块的批量处理逻辑，保留进度条）
    results = []
    print("\n开始执行多数据库RAG检索...")
    for item in tqdm(input_data, desc="处理进度"):
        try:
            # 提取输入字段（保留原字段兼容）
            question = item["question"]
            nl2_rewrite = item["nl2_rewrite"]
            teps_count_total = item.get("teps Count Total", 0)
            question_id = item.get("question_id", None)
            difficulty = item.get("difficulty", None)
            
            # 核心：调用多数据库检索器
            db_retrieval_results = multi_db_retriever.retrieve_from_all_dbs(nl2_rewrite)
            
            # 构建结果条目（适配多库结果字段名：retrieval_results）
            result_item = {
                "question": question,
                "nl2_rewrite": nl2_rewrite,
                "teps Count Total": teps_count_total,
                "question_id": question_id,
                "difficulty": difficulty,
                "retrieval_results": db_retrieval_results  # 多库结果字典（key=数据库类型）
            }
            results.append(result_item)
            
        except Exception as e:
            print(f"\n❌ 处理问题失败: {question[:50]}... 错误: {e}")
            # 错误结果适配多库格式（每个数据库返回错误信息）
            error_msg = f"Error: {str(e)[:200]}"
            db_types = ["MySQL", "Oracle", "PostgreSQL", "SQL Server", "SQLite"]
            results.append({
                "question": item["question"],
                "nl2_rewrite": item["nl2_rewrite"],
                "teps Count Total": item.get("teps Count Total", 0),
                "question_id": item.get("question_id", None),
                "difficulty": item.get("difficulty", None),
                "retrieval_results": {db_type: error_msg for db_type in db_types}
            })
    
    return results

def save_results(results: List[Dict], output_path: Path) -> None:
    """保存多库检索结果（保留权限容错，对齐新提示风格）"""
    try:
        # 确保输出目录存在（处理OneDrive权限）
        output_dir = output_path.parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ 创建输出目录: {output_dir}")
        
        # 处理文件已存在的情况（备份原有文件）
        if output_path.exists():
            backup_path = output_path.with_suffix('.bak.json')
            output_path.rename(backup_path)
            print(f"📁 原有结果文件已备份为: {backup_path}")
        
        # 写入文件（使用更宽松的权限）
        with open(output_path, 'w', encoding='utf-8', errors='ignore') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 多库检索结果已保存到: {output_path}")
        print(f"📊 共处理 {len(results)} 条记录")
        
    except PermissionError:
        # 权限失败时的备选方案：保存到桌面
        desktop_path = Path(os.path.expanduser("~/Desktop/nl2rag_multi_db_result.json"))
        with open(desktop_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n⚠️  OneDrive目录权限不足，结果已保存到桌面: {desktop_path}")
    except Exception as e:
        raise Exception(f"保存文件失败: {e}")

# ========== 主程序 ==========
def main():
    try:
        # 1. 加载输入数据（保留原验证逻辑）
        input_data = load_input_data(INPUT_JSON_PATH)
        
        if not input_data:
            print("❌ 没有有效输入数据，程序终止")
            return
        
        # 2. 执行多数据库RAG检索
        results = process_multi_db_rag_queries(input_data)
        
        # 3. 保存结果
        save_results(results, OUTPUT_JSON_PATH)
        
        # 4. 可选：测试单个查询（验证功能）
        print("\n📝 测试单个查询检索（前500字符预览）...")
        test_query = "统计各联赛的比赛数量并找出最多的联赛"
        multi_db_retriever = MultiDBDocumentRetriever()
        test_results = multi_db_retriever.retrieve_from_all_dbs(test_query)
        for db_type, result in test_results.items():
            print(f"\n========== {db_type} 检索结果预览 ==========")
            print(result[:500] + "..." if len(result) > 500 else result)
        
        print("\n🎉 程序执行完成！")
        
    except Exception as e:
        print(f"\n[ERROR] 程序执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()