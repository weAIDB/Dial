# main.py
import traceback
from config import OUTPUT_DIR, JSON_OUTPUT_PATH, MODEL_NAME, SQL_EXECUTION_TIMEOUT, SUPPORTED_DBS, RESULT_JSON_PATH, RULES_ROOT_DIR
from utils import ensure_dir_exists, load_db_rule_file, get_retrieval_items, parse_sql_result, get_final_sql, select_target_db
from api_client import call_modelscope_api_single
from db_operations import get_db_connection, test_sql_execution
from rag_retrieval import secondary_rag_retrieval
from result_saver import save_json_results, save_text_results, save_final_report
from prompt_builder import build_prompt, build_logic_fix_prompt 
from semantic_checker import verify_sql_logic, save_semantic_failure
from magic_adapter import MagicAdapter
# [导入 Logger]
from process_logger import ProcessLogger 

def main():
    """主流程：生成→执行→失败修正(语法)→成功后验证逻辑→逻辑修正→保存结果"""
    try:
        # 初始化目录
        ensure_dir_exists(OUTPUT_DIR)
        
        # [修改点 1] 初始化 Logger，传入 config.py 定义的绝对路径
        # OUTPUT_DIR = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\方言匹配\输出结果"
        process_logger = ProcessLogger(OUTPUT_DIR)
        
        print("=== NL2SQL批量生成+执行验证工具（多库动态连接版）===")
        # ... (打印信息保持不变) ...
        
        target_db_type = select_target_db()
        print(f"\n正在加载{target_db_type}完整规则文件...")
        db_rule_content = load_db_rule_file(target_db_type)
        
        print("\n正在加载多库检索结果项...")
        retrieval_items = get_retrieval_items()
        
        final_results = []
        total_items = len(retrieval_items)
        
        for idx, item in enumerate(retrieval_items):
            item_index = item["index"]
            question = item["question"]
            nl2_rewrite = item["nl2_rewrite"]
            db_id = item.get("db_id")
            print(f"\n==================================================")
            print(f"正在处理第 {item_index}/{total_items} 个项目")
            # ...
            
            # [修改点 2] 日志：开始记录问题
            process_logger.start_question(item_index, item.get("question_id"), db_id, question, nl2_rewrite)

            # [修改点 3] 日志：记录第一轮检索到的知识片段 (Functional & Rule-based)
            # retrieval_results 字典中包含了从知识库检索到的内容
            process_logger.log_knowledge_retrieval(
                retrieval_results=item.get("retrieval_results", {}),
                target_db_type=target_db_type
            )
            
            # --- 数据库连接逻辑 ---
            current_db_connection = None
            magic_adapter = None
            if db_id:
                current_db_connection = get_db_connection(target_db_type, specific_db_name=db_id)
                if current_db_connection:
                    magic_adapter = MagicAdapter(current_db_connection)
                else:
                    print(f"⚠️ 无法连接到数据库 '{db_id}'")
            else:
                print(f"⚠️ 缺少 db_id")

            # 初始化 item_result (保持不变)
            item_result = {
                "index": item_index,
                "question": question,
                "nl2_rewrite": nl2_rewrite,
                "question_id": item.get("question_id", None),
                "difficulty": item.get("difficulty", None),
                "first_generated_sql": "",
                "first_execution_status": "",
                "first_error_msg": None,
                "second_generated_sql": None,
                "second_execution_status": None,
                "second_error_msg": None,
                "final_execution_status": "",
                "secondary_rag_content": None,
                "execution_timeout": False,
                "target_db_type": target_db_type
            }
            # 手动添加一些需要的键以防 KeyError
            item_result.update({
                "question": question, "nl2_rewrite": nl2_rewrite, "db_id": db_id,
                "first_generated_sql": "", "first_execution_status": "", "first_error_msg": None,
                "second_generated_sql": None, "second_execution_status": None, "second_error_msg": None,
                "magic_generated_sql": None, "magic_execution_status": None
            })
            
            current_best_sql = ""
            current_execution_status = "failed"
            
            try:
                # ================= 1. 首次生成 & 执行 =================
                print(f"\n1. 首次生成SQL...")
                process_logger.log_phase("Round 1: Initial Generation")

                prompt_first = build_prompt(item, target_db_type, db_rule_content)
                process_logger.log_prompt("Round 1 Prompt", prompt_first)

                sql_result_first = call_modelscope_api_single(prompt_first, target_db_type)
                process_logger.log_llm_response(sql_result_first)

                parsed_sql_first = parse_sql_result(sql_result_first, target_db_type)
                first_sql = parsed_sql_first[target_db_type]
                
                if not first_sql:
                    # ... 失败处理 ...
                    print(f"❌ 首次生成失败：未获取到有效SQL")                   
                    item_result["first_generated_sql"] = "生成失败"
                    item_result["final_execution_status"] = "skip"
                else:
                    item_result["first_generated_sql"] = first_sql
                    print(f"首次生成SQL：{first_sql[:100]}...")
                                        
                    if not current_db_connection:
                        item_result["first_execution_status"] = "skip"
                        item_result["final_execution_status"] = "skip"
                    else:
                        print(f"\n2. 执行首次生成的SQL...")
                        exec_result_first = test_sql_execution(first_sql, target_db_type, current_db_connection)
                        
                        item_result["first_execution_status"] = exec_result_first["status"]
                        item_result["first_error_msg"] = exec_result_first["error"]
                        

                        # 检测超时
                        if exec_result_first["error"] and ("死循环" in exec_result_first["error"] or "超时" in exec_result_first["error"]):
                            item_result["execution_timeout"] = True

                        # 日志记录执行情况
                        process_logger.log_sql_execution(first_sql, exec_result_first["status"], exec_result_first["error"])
                                                
                        if exec_result_first["status"] == "success":
                            print(f"✅ 首次执行成功")
                            current_best_sql = first_sql
                            current_execution_status = "success"
                            item_result["final_execution_status"] = "success"
                        else:
                            print(f"❌ 首次执行失败：{exec_result_first['error'][:100]}...")

                # ================= 2. 语法错误修正 (Round 2) =================
                if current_execution_status != "success" and item_result["final_execution_status"] != "skip":
                    print(f"\n3. 启动语法错误修正流程...")
                    process_logger.log_phase("Round 2: Syntax Correction")
                    
                    # 检索针对报错的语法片段
                    secondary_rag_content = secondary_rag_retrieval(question, item_result["first_error_msg"], target_db_type)
                    item_result["secondary_rag_content"] = secondary_rag_content
                    
                    prompt_second = build_prompt(
                        retrieval_item=item,
                        target_db_type=target_db_type,
                        secondary_rag_content=secondary_rag_content,
                        error_msg=item_result["first_error_msg"],
                        first_sql=item_result["first_generated_sql"]
                    )
                    process_logger.log_prompt("Round 2 Prompt", prompt_second)
                    
                    sql_result_second = call_modelscope_api_single(prompt_second, target_db_type)
                    process_logger.log_llm_response(sql_result_second)

                    parsed_sql_second = parse_sql_result(sql_result_second, target_db_type)
                    second_sql = parsed_sql_second[target_db_type]
                    
                    if second_sql:
                        item_result["second_generated_sql"] = second_sql
                        print(f"二次生成SQL：{second_sql[:100]}...")
                                                
                        # [修改点 4] 日志：记录第二轮的语法片段和修正SQL
                        process_logger.log_syntax_refinement(
                            error_msg=item_result["first_error_msg"],
                            retrieved_guidance=secondary_rag_content, # 这里记录了检索出的知识片段
                            new_sql=second_sql
                        )

                        # 3.4 第二次执行验证
                        print(f"3.4 执行二次生成的SQL...")
                        exec_result_second = test_sql_execution(second_sql, target_db_type, current_db_connection)
                        item_result["second_execution_status"] = exec_result_second["status"]
                        item_result["second_error_msg"] = exec_result_second["error"]
                        item_result["final_execution_status"] = exec_result_second["status"]
                        
                        process_logger.log_sql_execution(second_sql, exec_result_second["status"], exec_result_second["error"])

                        if exec_result_second["status"] == "success":
                            print(f"✅ 二次执行成功")
                            current_best_sql = second_sql
                            current_execution_status = "success"
                        else:
                            print(f"❌ 二次执行失败：{exec_result_second['error'][:100]}...")
                    else:
                        print(f"❌ 二次生成失败：未获取到有效SQL")

                # ================= 3. Magic 模块调用 =================
                if current_execution_status != "success" and item_result["final_execution_status"] != "skip":
                    if magic_adapter and item_result["second_generated_sql"]:
                        print(f"\n--------------------------------------------------")
                        print(f"⚠️ Standard RAG 修正失败，激活 Magic Module...")
                        print(f"--------------------------------------------------")
                        process_logger.log_phase("Magic Module Intervention")
                        # 传入 logger，Magic 模块内部会调用 log_magic_fix
                        magic_status, magic_sql = magic_adapter.run_magic_fix(
                            question=item["question"],
                            nl2_rewrite=item["nl2_rewrite"],
                            incorrect_sql=item_result["second_generated_sql"],
                            error_msg=item_result["second_error_msg"],
                            dialect=target_db_type,
                            logger=process_logger # [修改点 5]
                        )
                        # ... (状态更新代码保持不变)
                        item_result["magic_generated_sql"] = magic_sql
                        item_result["magic_execution_status"] = magic_status
                        if magic_status == "success":
                            current_best_sql = magic_sql
                            current_execution_status = "success"
                            item_result["final_execution_status"] = "success"
                    else:
                        print("⚠️ 无法激活 Magic 模块 (数据库连接缺失或无前序SQL)")

                # ================= 4. 语义一致性验证 & 逻辑修正 (Round 3) =================
                if current_execution_status == "success" and current_best_sql:
                    print(f"\n4. 正在进行语义一致性验证...")
                    process_logger.log_phase("Round 3: Semantic & Logic Verification")
                    
                    is_pass, fail_reason = verify_sql_logic(question, nl2_rewrite, current_best_sql, target_db_type)
                    process_logger.log_semantic_check(is_pass, fail_reason)

                    if is_pass:
                        print(f"✅ 语义验证通过：SQL逻辑符合需求")
                        pass 
                    else:
                        print(f"⚠️ 语义验证不通过：{fail_reason}")
                        print(f"   -> 尝试进行逻辑修正 (第3轮生成)...")
                        
                        prompt_logic_fix = build_logic_fix_prompt(
                            question=item["question"],
                            nl2_rewrite=item["nl2_rewrite"],
                            wrong_sql=current_best_sql,
                            analysis_reason=fail_reason,
                            target_db_type=target_db_type
                        )
                        process_logger.log_prompt("Round 3 Prompt (Logic Fix)", prompt_logic_fix)
                        
                        try:
                            sql_result_fix = call_modelscope_api_single(prompt_logic_fix, target_db_type)
                            process_logger.log_llm_response(sql_result_fix)
                            
                            parsed_sql_fix = parse_sql_result(sql_result_fix, target_db_type)
                            fixed_sql = parsed_sql_fix.get(target_db_type, "")
                            
                            if fixed_sql:
                                # [修改点 6] 日志：记录第三轮生成的片段（Prompt中的Instruction）和修正SQL
                                process_logger.log_logic_refinement(
                                    fail_reason=fail_reason,
                                    logic_fix_sql=fixed_sql
                                )
                                
                                exec_result_fix = test_sql_execution(fixed_sql, target_db_type, current_db_connection)
                                process_logger.log_sql_execution(fixed_sql, exec_result_fix["status"], exec_result_fix["error"])
                                
                                if exec_result_fix["status"] == "success":
                                    print(f"✅ 逻辑修正后执行成功")
                                    item_result["second_generated_sql"] = fixed_sql
                                    item_result["second_execution_status"] = "success"
                                    item_result["final_execution_status"] = "success"
                                    item_result["second_error_msg"] = None 
                                    save_semantic_failure(item_index, question, nl2_rewrite, current_best_sql, fail_reason, fixed_sql)
                                else:
                                    print(f"❌ 逻辑修正后执行失败（语法错误）：{exec_result_fix['error'][:100]}...")
                                    save_semantic_failure(
                                            item_index, question, nl2_rewrite, current_best_sql, 
                                            f"{fail_reason} | 尝试修正但引入了执行错误: {exec_result_fix['error']}", 
                                            fixed_sql
                                    )
                            else:
                                print(f"❌ 逻辑修正生成失败：未获取到有效SQL")                        
                        
                        except Exception as e:
                            print(f"❌ 逻辑修正异常: {e}")
                            process_logger._write(f"Exception during logic fix: {e}")
                else:
                    pass
                final_results.append(item_result)
            
            except Exception as e:
                error_detail = str(e)[:200]
                print(f"❌ 异常: {error_detail}")
                process_logger._write(f"\n❌ **EXCEPTION:** {error_detail}")
                item_result["final_execution_status"] = "error"
                final_results.append(item_result)
            
            finally:
                if current_db_connection:
                    try: current_db_connection.close()
                    except Exception as e:
                        print(f"⚠️ 关闭连接异常: {e}")
                # 结束本题日志
                process_logger.end_question(item_result["final_execution_status"])
        
        # 步骤6：保存结果
        print(f"\n==================================================")
        print(f"所有项目处理完成，正在保存结果...")
        
        all_json_results = []
        for r in final_results:
            final_sql = get_final_sql(r, target_db_type)
            all_json_results.append({
                "question": r["question"],
                "nl2_rewrite": r["nl2_rewrite"],
                "question_id": r.get("question_id"),
                "db_id": r.get("db_id"), 
                "final_execution_status": r["final_execution_status"],
                "difficulty": r.get("difficulty"),
                target_db_type: final_sql
            })
        
        save_json_results(
            all_json_results=all_json_results,
            output_path=JSON_OUTPUT_PATH,
            target_db_type=target_db_type
        )
        
        save_text_results(all_json_results, OUTPUT_DIR, target_db_type)
        save_final_report(final_results)
        
        print(f"\n🎉 流程全部完成！")
        
    except Exception as e:
        print(f"\n❌ 程序执行出错：{str(e)}")
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()