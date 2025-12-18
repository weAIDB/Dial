# # main.py
# import traceback
# from config import OUTPUT_DIR, JSON_OUTPUT_PATH, MODEL_NAME, SQL_EXECUTION_TIMEOUT, SUPPORTED_DBS, RESULT_JSON_PATH, RULES_ROOT_DIR
# from utils import ensure_dir_exists, load_db_rule_file, get_retrieval_items, parse_sql_result, get_final_sql, select_target_db
# from api_client import call_modelscope_api_single
# from db_operations import get_db_connection, test_sql_execution
# from rag_retrieval import secondary_rag_retrieval
# from result_saver import save_json_results, save_text_results, save_final_report
# # 新增导入
# from prompt_builder import build_prompt, build_logic_fix_prompt 
# from semantic_checker import verify_sql_logic, save_semantic_failure

# def main():
#     """主流程：生成→执行→失败修正(语法)→成功后验证逻辑→逻辑修正→保存结果"""
#     try:
#         # 初始化目录
#         ensure_dir_exists(OUTPUT_DIR)
        
#         # 打印程序信息
#         print("=== NL2SQL批量生成+执行验证工具（多库检索优化版+语义审计）===")
#         print(f"使用模型: {MODEL_NAME}")
#         print(f"支持数据库: {', '.join(SUPPORTED_DBS)}")
#         print(f"多库检索结果路径: {RESULT_JSON_PATH}")
#         print(f"SQL执行超时时间: {SQL_EXECUTION_TIMEOUT}秒")
        
#         # 步骤1：选择目标数据库
#         target_db_type = select_target_db()
        
#         # 步骤2：加载规则文件
#         print(f"\n正在加载{target_db_type}完整规则文件...")
#         db_rule_content = load_db_rule_file(target_db_type)
        
#         # 步骤3：初始化数据库连接
#         print(f"\n正在初始化{target_db_type}数据库连接...")
#         db_connection = get_db_connection(target_db_type)
#         if not db_connection:
#             print(f"⚠️ 数据库连接初始化失败，将跳过执行验证环节")
        
#         # 步骤4：获取多库检索结果项
#         print("\n正在加载多库检索结果项...")
#         retrieval_items = get_retrieval_items()
        
#         # 步骤5：逐个处理
#         final_results = []
#         total_items = len(retrieval_items)
        
#         for idx, item in enumerate(retrieval_items):
#             item_index = item["index"]
#             question = item["question"]
#             nl2_rewrite = item["nl2_rewrite"]
            
#             print(f"\n==================================================")
#             print(f"正在处理第 {item_index}/{total_items} 个项目")
#             print(f"问题：{question[:100]}...")
#             print(f"目标数据库：{target_db_type}")
#             print(f"==================================================")
            
#             # 初始化项目结果
#             item_result = {
#                 "index": item_index,
#                 "question": question,
#                 "nl2_rewrite": nl2_rewrite,
#                 "question_id": item.get("question_id", None),
#                 "difficulty": item.get("difficulty", None),
#                 "first_generated_sql": "",
#                 "first_execution_status": "",
#                 "first_error_msg": None,
#                 "second_generated_sql": None,
#                 "second_execution_status": None,
#                 "second_error_msg": None,
#                 "final_execution_status": "",
#                 "secondary_rag_content": None,
#                 "execution_timeout": False,
#                 "target_db_type": target_db_type
#             }
            
#             # 用于追踪当前最好的SQL（无论是否通过语义检查，至少是能执行的）
#             current_best_sql = ""
#             current_execution_status = "failed"
            
#             try:
#                 # ================= 1. 首次生成 & 执行 =================
#                 print(f"\n1. 首次生成SQL...")
#                 prompt_first = build_prompt(
#                     retrieval_item=item,
#                     target_db_type=target_db_type,
#                     db_rule_content=db_rule_content
#                 )
#                 sql_result_first = call_modelscope_api_single(prompt_first, target_db_type)
#                 parsed_sql_first = parse_sql_result(sql_result_first, target_db_type)
#                 first_sql = parsed_sql_first[target_db_type]
                
#                 if not first_sql:
#                     print(f"❌ 首次生成失败：未获取到有效SQL")
#                     item_result["first_generated_sql"] = "生成失败"
#                     item_result["final_execution_status"] = "skip"
#                 else:
#                     item_result["first_generated_sql"] = first_sql
#                     print(f"首次生成SQL：{first_sql[:100]}...")
                    
#                     # 第一次执行验证
#                     if not db_connection:
#                         item_result["first_execution_status"] = "skip"
#                         item_result["final_execution_status"] = "skip"
#                     else:
#                         print(f"\n2. 执行首次生成的SQL...")
#                         exec_result_first = test_sql_execution(first_sql, target_db_type, db_connection)
                        
#                         item_result["first_execution_status"] = exec_result_first["status"]
#                         item_result["first_error_msg"] = exec_result_first["error"]
                        
#                         # 检测超时
#                         if exec_result_first["error"] and ("死循环" in exec_result_first["error"] or "超时" in exec_result_first["error"]):
#                             item_result["execution_timeout"] = True
                        
#                         if exec_result_first["status"] == "success":
#                             print(f"✅ 首次执行成功")
#                             current_best_sql = first_sql
#                             current_execution_status = "success"
#                             item_result["final_execution_status"] = "success"
#                         else:
#                             print(f"❌ 首次执行失败：{exec_result_first['error'][:100]}...")

#                 # ================= 2. 语法错误修正 (如果首次执行失败) =================
#                 # 如果首次执行失败，且没有跳过数据库连接
#                 if current_execution_status != "success" and item_result["final_execution_status"] != "skip":
#                     print(f"\n3. 启动语法错误修正流程...")
                    
#                     # 3.1 二次RAG检索 (针对语法/执行错误)
#                     print(f"3.1 执行错误RAG检索...")
#                     secondary_rag_content = secondary_rag_retrieval(
#                         question=question,
#                         error_msg=item_result["first_error_msg"],
#                         db_type=target_db_type
#                     )
#                     item_result["secondary_rag_content"] = secondary_rag_content
                    
#                     # 3.2 构造修正Prompt
#                     prompt_second = build_prompt(
#                         retrieval_item=item,
#                         target_db_type=target_db_type,
#                         secondary_rag_content=secondary_rag_content,
#                         error_msg=item_result["first_error_msg"],
#                         first_sql=item_result["first_generated_sql"]
#                     )
                    
#                     # 3.3 第二次生成SQL
#                     sql_result_second = call_modelscope_api_single(prompt_second, target_db_type)
#                     parsed_sql_second = parse_sql_result(sql_result_second, target_db_type)
#                     second_sql = parsed_sql_second[target_db_type]
                    
#                     if second_sql:
#                         item_result["second_generated_sql"] = second_sql
#                         print(f"二次生成SQL：{second_sql[:100]}...")
                        
#                         # 3.4 第二次执行验证
#                         print(f"3.4 执行二次生成的SQL...")
#                         exec_result_second = test_sql_execution(second_sql, target_db_type, db_connection)
                        
#                         item_result["second_execution_status"] = exec_result_second["status"]
#                         item_result["second_error_msg"] = exec_result_second["error"]
#                         item_result["final_execution_status"] = exec_result_second["status"]
                        
#                         if exec_result_second["status"] == "success":
#                             print(f"✅ 二次执行成功")
#                             current_best_sql = second_sql
#                             current_execution_status = "success"
#                         else:
#                             print(f"❌ 二次执行失败：{exec_result_second['error'][:100]}...")
#                     else:
#                         print(f"❌ 二次生成失败：未获取到有效SQL")

#                 # ================= 3. [新增] 语义一致性验证 & 逻辑修正 =================
#                 # 只有当 SQL 能够成功执行时，才进行语义检查
#                 if current_execution_status == "success" and current_best_sql:
#                     print(f"\n4. 正在进行语义一致性验证...")
                    
#                     # 使用 semantic_checker 模块进行验证
#                     is_pass, fail_reason = verify_sql_logic(
#                         question, nl2_rewrite, current_best_sql, target_db_type
#                     )
                    
#                     if is_pass:
#                         print(f"✅ 语义验证通过：SQL逻辑符合需求")
#                         # 如果没有进行过语法修正（即第一次就成功且通过验证），确保 second 字段为空或逻辑一致
#                         pass 
#                     else:
#                         print(f"⚠️ 语义验证不通过：{fail_reason}")
#                         print(f"   -> 尝试进行逻辑修正 (第3轮生成)...")
                        
#                         # 3.1 构造逻辑修正 Prompt
#                         prompt_logic_fix = build_logic_fix_prompt(
#                             question=question,
#                             nl2_rewrite=nl2_rewrite,
#                             wrong_sql=current_best_sql,
#                             analysis_reason=fail_reason,
#                             target_db_type=target_db_type
#                         )
                        
#                         # 3.2 调用模型修正
#                         try:
#                             sql_result_fix = call_modelscope_api_single(prompt_logic_fix, target_db_type)
#                             parsed_sql_fix = parse_sql_result(sql_result_fix, target_db_type)
#                             fixed_sql = parsed_sql_fix[target_db_type]
                            
#                             if fixed_sql:
#                                 print(f"   逻辑修正SQL: {fixed_sql[:100]}...")
                                
#                                 # 3.3 执行修正后的SQL
#                                 exec_result_fix = test_sql_execution(fixed_sql, target_db_type, db_connection)
                                
#                                 if exec_result_fix["status"] == "success":
#                                     print(f"✅ 逻辑修正后执行成功")
#                                     # 将修正后的 SQL 保存为最终结果 (借用 second_generated_sql 字段，优先作为最终SQL)
#                                     item_result["second_generated_sql"] = fixed_sql 
#                                     item_result["second_execution_status"] = "success"
#                                     item_result["final_execution_status"] = "success"
#                                     # 清空可能的旧报错信息，表明最终是成功的
#                                     item_result["second_error_msg"] = None 
                                    
#                                     # 记录日志：记录之前的失败原因和修正结果
#                                     save_semantic_failure(item_index, question, nl2_rewrite, current_best_sql, fail_reason, fixed_sql)
#                                 else:
#                                     print(f"❌ 逻辑修正后执行失败（语法错误）：{exec_result_fix['error'][:100]}...")
#                                     # 修正后反而报错了，虽然记录为失败，但日志中保留尝试记录
#                                     save_semantic_failure(
#                                         item_index, question, nl2_rewrite, current_best_sql, 
#                                         f"{fail_reason} | 尝试修正但引入了执行错误: {exec_result_fix['error']}", 
#                                         fixed_sql
#                                     )
#                             else:
#                                 print(f"❌ 逻辑修正生成失败：未获取到有效SQL")
                                
#                         except Exception as e:
#                             print(f"❌ 逻辑修正过程异常: {str(e)}")
#                             save_semantic_failure(item_index, question, nl2_rewrite, current_best_sql, f"{fail_reason} | 修正过程API异常: {str(e)}")
#                 else:
#                     # 连执行都失败了，自然没有语义验证
#                     pass

#                 # 添加到最终结果列表
#                 final_results.append(item_result)
                
#             except Exception as e:
#                 error_detail = str(e)[:100]
#                 print(f"\n❌ 项目处理异常：{error_detail}...")
#                 item_result.update({
#                     "first_execution_status": "error",
#                     "final_execution_status": "error",
#                     "error_msg": error_detail
#                 })
#                 final_results.append(item_result)
#                 continue
        
#         # 步骤6：保存结果
#         print(f"\n==================================================")
#         print(f"所有项目处理完成，正在保存结果...")
#         print(f"==================================================")
        
#         # 构造精简的输出结果
#         all_json_results = []
#         for r in final_results:
#             final_sql = get_final_sql(r, target_db_type)
#             all_json_results.append({
#                 "question": r["question"],
#                 "nl2_rewrite": r["nl2_rewrite"],
#                 "question_id": r.get("question_id"),
#                 "final_execution_status": r["final_execution_status"],
#                 "difficulty": r.get("difficulty"),
#                 target_db_type: final_sql
#             })
        
#         # 保存精简的SQL生成结果
#         save_json_results(
#             all_json_results=all_json_results,
#             output_path=JSON_OUTPUT_PATH,
#             target_db_type=target_db_type
#         )
        
#         # 保存文本格式结果
#         save_text_results(all_json_results, OUTPUT_DIR, target_db_type)
        
#         # 保存完整执行报告
#         save_final_report(final_results)
        
#         # 关闭数据库连接
#         if db_connection:
#             try:
#                 if target_db_type == "MySQL" and db_connection.is_connected():
#                     db_connection.close()
#                 elif target_db_type == "PostgreSQL" and not db_connection.closed:
#                     db_connection.close()
#                 else:
#                     db_connection.close()
#                 print(f"\n✅ {target_db_type} 数据库连接已关闭")
#             except Exception as e:
#                 print(f"\n⚠️ 关闭数据库连接时警告：{str(e)}")
        
#         print(f"\n🎉 流程全部完成！")
        
#     except Exception as e:
#         print(f"\n❌ 程序执行出错：{str(e)}")
#         traceback.print_exc()
#         exit(1)

# if __name__ == "__main__":
#     main()


##gpt5.2

import traceback
from config import OUTPUT_DIR, JSON_OUTPUT_PATH, MODEL_NAME, SQL_EXECUTION_TIMEOUT, SUPPORTED_DBS, RESULT_JSON_PATH, RULES_ROOT_DIR
from utils import ensure_dir_exists, load_db_rule_file, get_retrieval_items, parse_sql_result, get_final_sql, select_target_db
# ========== 修改点1：替换API调用函数导入 ==========
# 原：from api_client import call_modelscope_api_single
from api_client import call_gpt_api_single  # 改为GPT 5.2的API调用函数
from db_operations import get_db_connection, test_sql_execution
from rag_retrieval import secondary_rag_retrieval
from result_saver import save_json_results, save_text_results, save_final_report
# 新增导入
from prompt_builder import build_prompt, build_logic_fix_prompt 
from semantic_checker import verify_sql_logic, save_semantic_failure

def main():
    """主流程：生成→执行→失败修正(语法)→成功后验证逻辑→逻辑修正→保存结果"""
    try:
        # 初始化目录
        ensure_dir_exists(OUTPUT_DIR)
        
        # 打印程序信息
        print("=== NL2SQL批量生成+执行验证工具（多库检索优化版+语义审计）===")
        print(f"使用模型: {MODEL_NAME}")
        print(f"支持数据库: {', '.join(SUPPORTED_DBS)}")
        print(f"多库检索结果路径: {RESULT_JSON_PATH}")
        print(f"SQL执行超时时间: {SQL_EXECUTION_TIMEOUT}秒")
        
        # 步骤1：选择目标数据库
        target_db_type = select_target_db()
        
        # 步骤2：加载规则文件
        print(f"\n正在加载{target_db_type}完整规则文件...")
        db_rule_content = load_db_rule_file(target_db_type)
        
        # 步骤3：初始化数据库连接
        print(f"\n正在初始化{target_db_type}数据库连接...")
        db_connection = get_db_connection(target_db_type)
        if not db_connection:
            print(f"⚠️ 数据库连接初始化失败，将跳过执行验证环节")
        
        # 步骤4：获取多库检索结果项
        print("\n正在加载多库检索结果项...")
        retrieval_items = get_retrieval_items()
        
        # 步骤5：逐个处理
        final_results = []
        total_items = len(retrieval_items)
        
        for idx, item in enumerate(retrieval_items):
            item_index = item["index"]
            question = item["question"]
            nl2_rewrite = item["nl2_rewrite"]
            
            print(f"\n==================================================")
            print(f"正在处理第 {item_index}/{total_items} 个项目")
            print(f"问题：{question[:100]}...")
            print(f"目标数据库：{target_db_type}")
            print(f"==================================================")
            
            # 初始化项目结果
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
            
            # 用于追踪当前最好的SQL（无论是否通过语义检查，至少是能执行的）
            current_best_sql = ""
            current_execution_status = "failed"
            
            try:
                # ================= 1. 首次生成 & 执行 =================
                print(f"\n1. 首次生成SQL...")
                prompt_first = build_prompt(
                    retrieval_item=item,
                    target_db_type=target_db_type,
                    db_rule_content=db_rule_content
                )
                # ========== 修改点2：替换首次生成的API调用 ==========
                # 原：sql_result_first = call_modelscope_api_single(prompt_first, target_db_type)
                sql_result_first = call_gpt_api_single(prompt_first, target_db_type)
                parsed_sql_first = parse_sql_result(sql_result_first, target_db_type)
                first_sql = parsed_sql_first[target_db_type]
                
                if not first_sql:
                    print(f"❌ 首次生成失败：未获取到有效SQL")
                    item_result["first_generated_sql"] = "生成失败"
                    item_result["final_execution_status"] = "skip"
                else:
                    item_result["first_generated_sql"] = first_sql
                    print(f"首次生成SQL：{first_sql[:100]}...")
                    
                    # 第一次执行验证
                    if not db_connection:
                        item_result["first_execution_status"] = "skip"
                        item_result["final_execution_status"] = "skip"
                    else:
                        print(f"\n2. 执行首次生成的SQL...")
                        exec_result_first = test_sql_execution(first_sql, target_db_type, db_connection)
                        
                        item_result["first_execution_status"] = exec_result_first["status"]
                        item_result["first_error_msg"] = exec_result_first["error"]
                        
                        # 检测超时
                        if exec_result_first["error"] and ("死循环" in exec_result_first["error"] or "超时" in exec_result_first["error"]):
                            item_result["execution_timeout"] = True
                        
                        if exec_result_first["status"] == "success":
                            print(f"✅ 首次执行成功")
                            current_best_sql = first_sql
                            current_execution_status = "success"
                            item_result["final_execution_status"] = "success"
                        else:
                            print(f"❌ 首次执行失败：{exec_result_first['error'][:100]}...")

                # ================= 2. 语法错误修正 (如果首次执行失败) =================
                # 如果首次执行失败，且没有跳过数据库连接
                if current_execution_status != "success" and item_result["final_execution_status"] != "skip":
                    print(f"\n3. 启动语法错误修正流程...")
                    
                    # 3.1 二次RAG检索 (针对语法/执行错误)
                    print(f"3.1 执行错误RAG检索...")
                    secondary_rag_content = secondary_rag_retrieval(
                        question=question,
                        error_msg=item_result["first_error_msg"],
                        db_type=target_db_type
                    )
                    item_result["secondary_rag_content"] = secondary_rag_content
                    
                    # 3.2 构造修正Prompt
                    prompt_second = build_prompt(
                        retrieval_item=item,
                        target_db_type=target_db_type,
                        secondary_rag_content=secondary_rag_content,
                        error_msg=item_result["first_error_msg"],
                        first_sql=item_result["first_generated_sql"]
                    )
                    
                    # 3.3 第二次生成SQL
                    # ========== 修改点3：替换二次生成的API调用 ==========
                    # 原：sql_result_second = call_modelscope_api_single(prompt_second, target_db_type)
                    sql_result_second = call_gpt_api_single(prompt_second, target_db_type)
                    parsed_sql_second = parse_sql_result(sql_result_second, target_db_type)
                    second_sql = parsed_sql_second[target_db_type]
                    
                    if second_sql:
                        item_result["second_generated_sql"] = second_sql
                        print(f"二次生成SQL：{second_sql[:100]}...")
                        
                        # 3.4 第二次执行验证
                        print(f"3.4 执行二次生成的SQL...")
                        exec_result_second = test_sql_execution(second_sql, target_db_type, db_connection)
                        
                        item_result["second_execution_status"] = exec_result_second["status"]
                        item_result["second_error_msg"] = exec_result_second["error"]
                        item_result["final_execution_status"] = exec_result_second["status"]
                        
                        if exec_result_second["status"] == "success":
                            print(f"✅ 二次执行成功")
                            current_best_sql = second_sql
                            current_execution_status = "success"
                        else:
                            print(f"❌ 二次执行失败：{exec_result_second['error'][:100]}...")
                    else:
                        print(f"❌ 二次生成失败：未获取到有效SQL")

                # ================= 3. [新增] 语义一致性验证 & 逻辑修正 =================
                # 只有当 SQL 能够成功执行时，才进行语义检查
                if current_execution_status == "success" and current_best_sql:
                    print(f"\n4. 正在进行语义一致性验证...")
                    
                    # 使用 semantic_checker 模块进行验证
                    is_pass, fail_reason = verify_sql_logic(
                        question, nl2_rewrite, current_best_sql, target_db_type
                    )
                    
                    if is_pass:
                        print(f"✅ 语义验证通过：SQL逻辑符合需求")
                        # 如果没有进行过语法修正（即第一次就成功且通过验证），确保 second 字段为空或逻辑一致
                        pass 
                    else:
                        print(f"⚠️ 语义验证不通过：{fail_reason}")
                        print(f"   -> 尝试进行逻辑修正 (第3轮生成)...")
                        
                        # 3.1 构造逻辑修正 Prompt
                        prompt_logic_fix = build_logic_fix_prompt(
                            question=question,
                            nl2_rewrite=nl2_rewrite,
                            wrong_sql=current_best_sql,
                            analysis_reason=fail_reason,
                            target_db_type=target_db_type
                        )
                        
                        # 3.2 调用模型修正
                        try:
                            # ========== 修改点4：替换逻辑修正的API调用 ==========
                            # 原：sql_result_fix = call_modelscope_api_single(prompt_logic_fix, target_db_type)
                            sql_result_fix = call_gpt_api_single(prompt_logic_fix, target_db_type)
                            parsed_sql_fix = parse_sql_result(sql_result_fix, target_db_type)
                            fixed_sql = parsed_sql_fix[target_db_type]
                            
                            if fixed_sql:
                                print(f"   逻辑修正SQL: {fixed_sql[:100]}...")
                                
                                # 3.3 执行修正后的SQL
                                exec_result_fix = test_sql_execution(fixed_sql, target_db_type, db_connection)
                                
                                if exec_result_fix["status"] == "success":
                                    print(f"✅ 逻辑修正后执行成功")
                                    # 将修正后的 SQL 保存为最终结果 (借用 second_generated_sql 字段，优先作为最终SQL)
                                    item_result["second_generated_sql"] = fixed_sql 
                                    item_result["second_execution_status"] = "success"
                                    item_result["final_execution_status"] = "success"
                                    # 清空可能的旧报错信息，表明最终是成功的
                                    item_result["second_error_msg"] = None 
                                    
                                    # 记录日志：记录之前的失败原因和修正结果
                                    save_semantic_failure(item_index, question, nl2_rewrite, current_best_sql, fail_reason, fixed_sql)
                                else:
                                    print(f"❌ 逻辑修正后执行失败（语法错误）：{exec_result_fix['error'][:100]}...")
                                    # 修正后反而报错了，虽然记录为失败，但日志中保留尝试记录
                                    save_semantic_failure(
                                        item_index, question, nl2_rewrite, current_best_sql, 
                                        f"{fail_reason} | 尝试修正但引入了执行错误: {exec_result_fix['error']}", 
                                        fixed_sql
                                    )
                            else:
                                print(f"❌ 逻辑修正生成失败：未获取到有效SQL")
                                
                        except Exception as e:
                            print(f"❌ 逻辑修正过程异常: {str(e)}")
                            save_semantic_failure(item_index, question, nl2_rewrite, current_best_sql, f"{fail_reason} | 修正过程API异常: {str(e)}")
                else:
                    # 连执行都失败了，自然没有语义验证
                    pass

                # 添加到最终结果列表
                final_results.append(item_result)
                
            except Exception as e:
                error_detail = str(e)[:100]
                print(f"\n❌ 项目处理异常：{error_detail}...")
                item_result.update({
                    "first_execution_status": "error",
                    "final_execution_status": "error",
                    "error_msg": error_detail
                })
                final_results.append(item_result)
                continue
        
        # 步骤6：保存结果
        print(f"\n==================================================")
        print(f"所有项目处理完成，正在保存结果...")
        print(f"==================================================")
        
        # 构造精简的输出结果
        all_json_results = []
        for r in final_results:
            final_sql = get_final_sql(r, target_db_type)
            all_json_results.append({
                "question": r["question"],
                "nl2_rewrite": r["nl2_rewrite"],
                "question_id": r.get("question_id"),
                "final_execution_status": r["final_execution_status"],
                "difficulty": r.get("difficulty"),
                target_db_type: final_sql
            })
        
        # 保存精简的SQL生成结果
        save_json_results(
            all_json_results=all_json_results,
            output_path=JSON_OUTPUT_PATH,
            target_db_type=target_db_type
        )
        
        # 保存文本格式结果
        save_text_results(all_json_results, OUTPUT_DIR, target_db_type)
        
        # 保存完整执行报告
        save_final_report(final_results)
        
        # 关闭数据库连接
        if db_connection:
            try:
                if target_db_type == "MySQL" and db_connection.is_connected():
                    db_connection.close()
                elif target_db_type == "PostgreSQL" and not db_connection.closed:
                    db_connection.close()
                else:
                    db_connection.close()
                print(f"\n✅ {target_db_type} 数据库连接已关闭")
            except Exception as e:
                print(f"\n⚠️ 关闭数据库连接时警告：{str(e)}")
        
        print(f"\n🎉 流程全部完成！")
        
    except Exception as e:
        print(f"\n❌ 程序执行出错：{str(e)}")
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()