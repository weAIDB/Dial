# main.py
import traceback
import sys
from config import OUTPUT_DIR, JSON_OUTPUT_PATH, MODEL_NAME, SQL_EXECUTION_TIMEOUT, SUPPORTED_DBS, RESULT_JSON_PATH, \
    RULES_ROOT_DIR
from utils import ensure_dir_exists, load_db_rule_file, get_retrieval_items, parse_sql_result, get_final_sql, \
    select_target_db
from api_client import call_modelscope_api_single
from db_operations import get_db_connection, test_sql_execution
from rag_retrieval import secondary_rag_retrieval
from result_saver import save_json_results, save_text_results, save_final_report
from prompt_builder import build_prompt, build_logic_fix_prompt
from semantic_checker import verify_sql_logic, save_semantic_failure
from magic_adapter import MagicAdapter
from process_logger import ProcessLogger
# [新增] 引入纠错模块
from schema_corrector import correct_sql_schema


# =============================================================================
# [辅助函数]
# =============================================================================
def clean_sql_for_execution(sql: str) -> str:
    if not sql: return ""
    cleaned = sql.strip()
    while cleaned.endswith(';') or cleaned.endswith('/'):
        cleaned = cleaned[:-1].strip()
    return cleaned


def switch_oracle_schema(connection, db_id):
    if not db_id: return
    try:
        cursor = connection.cursor()
        cursor.execute(f"ALTER SESSION SET CURRENT_SCHEMA = {db_id}")
        print(f"   🔄 [Oracle] Schema 已切换至: {db_id}")
        cursor.close()
    except Exception as e:
        print(f"   ⚠️ [Oracle] 切换 Schema 失败: {str(e)[:100]}")


# =============================================================================
# 主程序
# =============================================================================
def main():
    try:
        ensure_dir_exists(OUTPUT_DIR)
        process_logger = ProcessLogger(OUTPUT_DIR)
        print("=== NL2SQL批量生成+执行验证工具（Schema增强版）===")

        global_target_db_type = select_target_db()
        print(f"\n正在加载 {global_target_db_type} 完整规则文件...")
        db_rule_content = load_db_rule_file(global_target_db_type)

        print("\n正在加载输入数据...")
        retrieval_items = get_retrieval_items()

        final_results = []
        total_items = len(retrieval_items)

        for idx, item in enumerate(retrieval_items):
            item_index = item.get("index", idx)
            question = item["question"]
            nl2_rewrite = item["nl2_rewrite"]
            db_id = item.get("db_id")
            question_id = item.get("question_id")

            # 获取真实 Schema 信息
            true_tc_str = item.get("true_tables_columns")

            target_db_type = global_target_db_type

            print(f"\n{'=' * 60}")
            print(f"处理项目 {idx + 1}/{total_items} (ID: {question_id}) | DB: {db_id}")
            print(f"{'=' * 60}")

            process_logger.start_question(item_index, question_id, db_id, question, nl2_rewrite)
            process_logger.log_knowledge_retrieval(item.get("retrieval_results", {}), target_db_type)

            current_db_connection = None
            magic_adapter = None

            if db_id:
                current_db_connection = get_db_connection(target_db_type, specific_db_name=db_id)
                if current_db_connection:
                    if "oracle" in target_db_type.lower():
                        switch_oracle_schema(current_db_connection, db_id)
                    magic_adapter = MagicAdapter(current_db_connection)
                else:
                    print(f"❌ 无法连接到数据库 '{db_id}'")
            else:
                print(f"⚠️ 缺少 db_id")

            item_result = {
                "index": item_index, "question": question, "nl2_rewrite": nl2_rewrite,
                "question_id": question_id, "difficulty": item.get("difficulty"),
                "db_id": db_id, "target_db_type": target_db_type,
                "first_generated_sql": "", "first_execution_status": "pending", "first_error_msg": None,
                "second_generated_sql": None, "second_execution_status": None, "second_error_msg": None,
                "magic_generated_sql": None, "magic_execution_status": None,
                "final_execution_status": "pending", "execution_timeout": False
            }

            current_best_sql = ""
            current_execution_status = "failed"

            try:
                # === Round 1 ===
                print(f"\n>>> Round 1: 首次生成")
                process_logger.log_phase("Round 1: Initial Generation")

                prompt_first = build_prompt(item, target_db_type, db_rule_content)
                process_logger.log_prompt("Round 1 Prompt", prompt_first)

                sql_res_1 = call_modelscope_api_single(prompt_first, target_db_type)
                process_logger.log_llm_response(sql_res_1)

                parsed_1 = parse_sql_result(sql_res_1, target_db_type)
                sql_1 = parsed_1.get(target_db_type, "")

                if not sql_1:
                    print(f"❌ 生成失败")
                    item_result["first_generated_sql"] = "Generation Failed"
                    item_result["final_execution_status"] = "skip"
                else:
                    # [核心] 1. Schema 自动纠错
                    if true_tc_str:
                        sql_1 = correct_sql_schema(sql_1, true_tc_str)

                    item_result["first_generated_sql"] = sql_1
                    print(f"📝 SQL: {sql_1[:100]}...")

                    if current_db_connection:
                        print(f"🚀 执行验证...")
                        # 2. 清洗分号
                        sql_run_1 = clean_sql_for_execution(sql_1)
                        exec_1 = test_sql_execution(sql_run_1, target_db_type, current_db_connection)

                        item_result["first_execution_status"] = exec_1["status"]
                        item_result["first_error_msg"] = exec_1["error"]
                        process_logger.log_sql_execution(sql_1, exec_1["status"], exec_1["error"])

                        if exec_1["status"] == "success":
                            print(f"✅ 成功")
                            current_best_sql = sql_1
                            current_execution_status = "success"
                            item_result["final_execution_status"] = "success"
                        else:
                            print(f"❌ 失败: {exec_1['error'][:100]}")
                            item_result["final_execution_status"] = "failed"
                            if exec_1["error"] and "time" in str(exec_1["error"]).lower():
                                item_result["execution_timeout"] = True
                    else:
                        item_result["final_execution_status"] = "skip"

                # === Round 2 ===
                if current_execution_status != "success" and item_result["final_execution_status"] != "skip":
                    print(f"\n>>> Round 2: 语法修正")
                    process_logger.log_phase("Round 2: Syntax Correction")

                    rag_content = secondary_rag_retrieval(question, item_result["first_error_msg"], target_db_type)
                    item_result["secondary_rag_content"] = rag_content

                    prompt_2 = build_prompt(item, target_db_type, secondary_rag_content=rag_content,
                                            error_msg=item_result["first_error_msg"],
                                            first_sql=item_result["first_generated_sql"])
                    process_logger.log_prompt("Round 2 Prompt", prompt_2)

                    sql_res_2 = call_modelscope_api_single(prompt_2, target_db_type)
                    process_logger.log_llm_response(sql_res_2)

                    parsed_2 = parse_sql_result(sql_res_2, target_db_type)
                    sql_2 = parsed_2.get(target_db_type, "")

                    if sql_2:
                        # [核心] Schema 自动纠错
                        if true_tc_str:
                            sql_2 = correct_sql_schema(sql_2, true_tc_str)

                        item_result["second_generated_sql"] = sql_2
                        print(f"📝 SQL: {sql_2[:100]}...")
                        process_logger.log_syntax_refinement(item_result["first_error_msg"], rag_content, sql_2)

                        if current_db_connection:
                            print(f"🚀 执行验证...")
                            sql_run_2 = clean_sql_for_execution(sql_2)
                            exec_2 = test_sql_execution(sql_run_2, target_db_type, current_db_connection)

                            item_result["second_execution_status"] = exec_2["status"]
                            item_result["second_error_msg"] = exec_2["error"]
                            item_result["final_execution_status"] = exec_2["status"]
                            process_logger.log_sql_execution(sql_2, exec_2["status"], exec_2["error"])

                            if exec_2["status"] == "success":
                                print(f"✅ 成功")
                                current_best_sql = sql_2
                                current_execution_status = "success"
                            else:
                                print(f"❌ 失败: {exec_2['error'][:100]}")

                # === Round 3: Magic ===
                if current_execution_status != "success" and item_result["final_execution_status"] != "skip":
                    if magic_adapter and item_result["second_generated_sql"]:
                        print(f"\n>>> Magic Module")
                        process_logger.log_phase("Magic Module Intervention")
                        magic_status, magic_sql = magic_adapter.run_magic_fix(
                            question=question, nl2_rewrite=nl2_rewrite,
                            incorrect_sql=item_result["second_generated_sql"],
                            error_msg=item_result["second_error_msg"],
                            dialect=target_db_type, logger=process_logger
                        )
                        # Magic 模块内部如果生成了 SQL，建议也通过 correct_sql_schema 跑一下，但通常Magic比较准
                        item_result["magic_generated_sql"] = magic_sql
                        item_result["magic_execution_status"] = magic_status
                        if magic_status == "success":
                            print(f"✨ 修复成功")
                            current_best_sql = magic_sql
                            current_execution_status = "success"
                            item_result["final_execution_status"] = "success"

                # === Round 4: Semantic ===
                if current_execution_status == "success" and current_best_sql:
                    print(f"\n>>> Round 3: 语义验证")
                    process_logger.log_phase("Round 3: Semantic Verification")
                    is_pass, fail_reason = verify_sql_logic(question, nl2_rewrite, current_best_sql, target_db_type)
                    process_logger.log_semantic_check(is_pass, fail_reason)

                    if is_pass:
                        print(f"✅ 通过")
                    else:
                        print(f"⚠️ 失败: {fail_reason}")
                        print(f"🔄 逻辑修正...")
                        prompt_fix = build_logic_fix_prompt(
                            question=question, nl2_rewrite=nl2_rewrite,
                            wrong_sql=current_best_sql, analysis_reason=fail_reason,
                            target_db_type=target_db_type,
                            true_tables_columns=true_tc_str  # 传入Schema
                        )
                        process_logger.log_prompt("Round 3 Prompt", prompt_fix)

                        try:
                            sql_res_fix = call_modelscope_api_single(prompt_fix, target_db_type)
                            parsed_fix = parse_sql_result(sql_res_fix, target_db_type)
                            fixed_sql = parsed_fix.get(target_db_type, "")

                            if fixed_sql:
                                # [核心] Schema 自动纠错
                                if true_tc_str:
                                    fixed_sql = correct_sql_schema(fixed_sql, true_tc_str)

                                process_logger.log_logic_refinement(fail_reason, fixed_sql)
                                sql_run_fix = clean_sql_for_execution(fixed_sql)

                                if current_db_connection:
                                    exec_fix = test_sql_execution(sql_run_fix, target_db_type, current_db_connection)
                                    process_logger.log_sql_execution(fixed_sql, exec_fix["status"], exec_fix["error"])
                                    if exec_fix["status"] == "success":
                                        print(f"✅ 修正成功")
                                        item_result["final_execution_status"] = "success"
                                        current_best_sql = fixed_sql
                                        save_semantic_failure(item_index, question, nl2_rewrite, current_best_sql,
                                                              fail_reason, fixed_sql)
                                    else:
                                        print(f"❌ 修正失败")
                        except Exception as e:
                            print(f"❌ 异常: {e}")

                final_results.append(item_result)

            except Exception as e:
                print(f"❌ 处理异常: {e}")
                traceback.print_exc()
                item_result["final_execution_status"] = "error"
                final_results.append(item_result)
            finally:
                if current_db_connection:
                    try:
                        current_db_connection.close()
                    except:
                        pass
                process_logger.end_question(item_result["final_execution_status"])

        # 保存结果
        print(f"\n{'=' * 60}\n处理完成，正在保存...")
        all_json_results = []
        for r in final_results:
            final_sql = get_final_sql(r, r["target_db_type"])
            all_json_results.append({
                "question": r["question"],
                "nl2_rewrite": r["nl2_rewrite"],
                "question_id": r.get("question_id"),
                "db_id": r.get("db_id"),
                "final_execution_status": r["final_execution_status"],
                "difficulty": r.get("difficulty"),
                r["target_db_type"]: final_sql
            })

        save_json_results(all_json_results, JSON_OUTPUT_PATH, global_target_db_type)
        save_text_results(all_json_results, OUTPUT_DIR, global_target_db_type)
        save_final_report(final_results)
        print(f"🎉 完成！")

    except Exception as e:
        print(f"\n❌ 致命错误: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()