# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
import os

# ========== 路径配置 ==========
# RAG模块所在目录
RAG_DIR = Path(r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\rag\Model4.0_rag")

# 输入JSON文件路径
INPUT_JSON_PATH = Path(
    r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\正在测试数据集\2206条数据\全量数据\nl2(1).json")

# 输出JSON文件路径
OUTPUT_JSON_PATH = Path(
    r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\正在测试数据集\2206条数据\全量数据\result")

# ========== 添加RAG目录到Python路径 ==========
sys.path.append(str(RAG_DIR.resolve()))

# ========== 导入RAG模块 ==========
try:
    from rag_fixed_chunk import (
        MultiDBDocumentRetriever,
        load_input_data as rag_load_data,
        batch_retrieve_from_json as rag_batch_retrieve
    )

    print("[OK] 成功导入rag_fixed_chunk模块")
except ImportError as e:
    print(f"[ERROR] 导入RAG模块失败: {e}")
    sys.exit(1)
except AttributeError as e:
    print(f"[ERROR] rag_fixed_chunk模块中找不到指定对象: {e}")
    sys.exit(1)


# ========== 核心函数 ==========

def load_input_data(file_path: Path) -> List[Dict]:
    """加载输入JSON数据并进行预验证"""
    if not file_path.exists():
        raise FileNotFoundError(f"输入文件不存在: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("输入JSON必须是数组格式")

    valid_data = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        # 验证必须存在的字段，确保有检索源
        final_nl = item.get("final_NL_oracle")
        if not final_nl or not isinstance(final_nl, dict) or "Question_final" not in final_nl:
            print(f"⚠️  第{idx}条数据缺少 final_NL_oracle['Question_final'] 字段，跳过")
            continue

        valid_data.append(item)

    print(f"✅ 加载并验证输入数据完成，有效条目数: {len(valid_data)}/{len(data)}")
    return valid_data


def process_multi_db_rag_queries(input_data: List[Dict]) -> List[Dict]:
    """处理多数据库RAG检索请求并按指定格式输出"""

    # 初始化多数据库检索器
    print("\n🔄 初始化多数据库向量库...")
    try:
        multi_db_retriever = MultiDBDocumentRetriever()
    except Exception as e:
        print(f"[ERROR] 初始化多数据库检索器失败: {e}")
        sys.exit(1)

    results = []
    print("\n开始执行多数据库RAG检索...")

    for item in tqdm(input_data, desc="处理进度"):
        try:
            # 1. 提取基础信息
            question = item.get("question", "")
            question_id = item.get("question_id", None)
            true_tables_columns=item.get("true_tables_columns", [])
            # 2. 提取检索文本 (Question_final) 并将其作为输出的 nl2_rewrite
            final_nl_obj = item.get("final_NL_oracle", {})
            nl2_rewrite_text = final_nl_obj.get("Question_final", "")
            if not isinstance(nl2_rewrite_text, str):
                nl2_rewrite_text = str(nl2_rewrite_text)

            # 3. 处理 db_id
            db_id = item.get("db_id")
            db_id = "bird" if (db_id is None or str(db_id).strip() == "") else db_id

            # 4. 执行检索
            if nl2_rewrite_text.strip():
                # 使用提取出的长文本进行检索
                db_retrieval_results = multi_db_retriever.retrieve_from_all_dbs(nl2_rewrite_text)
            else:
                db_retrieval_results = {db: "Error: Empty Query" for db in
                                        ["MySQL", "Oracle", "PostgreSQL", "SQL Server", "SQLite"]}

            # 5. 构建符合目标格式的结果字典
            result_item = {
                "question": question,
                "nl2_rewrite": nl2_rewrite_text,  # 将检索用的 Question_final 放入 nl2_rewrite
                "teps Count Total": item.get("teps Count Total", 0),  # 默认为0
                "question_id": question_id,
                "difficulty": item.get("difficulty", item.get("hardness", "")),  # 兼容 difficulty 或 hardness 字段
                "retrieval_results": db_retrieval_results,  # 包含5个库的检索结果
                "db_id": db_id,
                "true_tables_columns": true_tables_columns
            }
            results.append(result_item)

        except Exception as e:
            print(f"\n❌ 处理问题失败 ID: {item.get('question_id')}... 错误: {e}")

            # 错误处理结构也保持对齐
            error_db_id = item.get("db_id", "bird")
            error_msg = f"Error: {str(e)[:200]}"
            db_types = ["MySQL", "Oracle", "PostgreSQL", "SQL Server", "SQLite"]

            results.append({
                "question": item.get("question", ""),
                "nl2_rewrite": item.get("final_NL_oracle", {}).get("Question_final", ""),
                "teps Count Total": 0,
                "question_id": item.get("question_id"),
                "difficulty": "",
                "retrieval_results": {db_type: error_msg for db_type in db_types},
                "db_id": error_db_id,
                "true_tables_columns":item.get("true_tables_columns", [])
            })

    return results


def save_results(results: List[Dict], output_path: Path) -> None:
    """保存结果"""
    try:
        output_dir = output_path.parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        # 备份逻辑
        if output_path.exists():
            import time
            timestamp = int(time.time())
            backup_path = output_path.with_name(f"{output_path.stem}_{timestamp}.bak.json")
            try:
                output_path.rename(backup_path)
                print(f"📁 原有结果文件已备份为: {backup_path.name}")
            except OSError:
                print("⚠️ 无法重命名旧文件，将直接覆盖")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 结果已保存到: {output_path}")
        print(f"📊 共处理 {len(results)} 条记录")

    except Exception as e:
        desktop_path = Path(os.path.expanduser(f"~/Desktop/{output_path.name}"))
        print(f"\n❌ 保存失败: {e}")
        try:
            with open(desktop_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"⚠️ 已紧急保存到桌面: {desktop_path}")
        except:
            print("❌ 无法保存文件")


def main():
    try:
        # 1. 加载数据
        print(f"正在加载数据: {INPUT_JSON_PATH}")
        input_data = load_input_data(INPUT_JSON_PATH)

        if not input_data:
            print("❌ 没有有效输入数据，程序终止")
            return

        # 2. 执行检索
        results = process_multi_db_rag_queries(input_data)

        # 3. 保存
        save_results(results, OUTPUT_JSON_PATH)

        print("\n🎉 程序执行完成！")

    except Exception as e:
        print(f"\n[ERROR] 程序执行崩溃: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()