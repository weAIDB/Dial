# main.py
import traceback
import sys
from .config import OUTPUT_DIR, JSON_OUTPUT_PATH, MODEL_NAME, SQL_EXECUTION_TIMEOUT, SUPPORTED_DBS, RESULT_JSON_PATH, RULES_ROOT_DIR
from .utils import ensure_dir_exists, load_db_rule_file, get_retrieval_items, parse_sql_result, get_final_sql, select_target_db
from .api_client import call_modelscope_api_single
from .db_operations import get_db_connection, test_sql_execution
from .result_saver import save_json_results, save_text_results, save_final_report
from .prompt_builder import build_prompt, build_logic_fix_prompt
from .magic_adapter import MagicAdapter
from .process_logger import ProcessLogger
from .schema_corrector import correct_sql_schema
from .sql_error_analyzer import get_error_analyzer
from .rag_retrieval import secondary_rag_retrieval
try:
    from .semantic_checker import verify_sql_logic, save_semantic_failure
except ImportError:
    print("⚠️ Warning: 'semantic_verifier.py' not found, semantic verification function will be unavailable.")
    # Define placeholder functions to prevent errors
    def verify_sql_logic(*args, **kwargs): return True, ""
    def save_semantic_failure(*args, **kwargs): pass

# Helper Functions
def clean_sql_for_execution(sql: str) -> str:
    if not sql: return ""
    cleaned = sql.strip()
    # Remove Markdown code block markers
    cleaned = cleaned.replace("```sql", "").replace("```", "")
    while cleaned.endswith(';') or cleaned.endswith('/'):
        cleaned = cleaned[:-1].strip()
    return cleaned

def switch_oracle_schema(connection, db_id):
    if not db_id: return
    try:
        cursor = connection.cursor()
        cursor.execute(f"ALTER SESSION SET CURRENT_SCHEMA = {db_id}")
        print(f"   🔄 [Oracle] Schema switched to: {db_id}")
        cursor.close()
    except Exception as e:
        print(f"   ⚠️ [Oracle] Failed to switch Schema: {str(e)[:100]}")

def main():
    try:
        ensure_dir_exists(OUTPUT_DIR)
        process_logger = ProcessLogger(OUTPUT_DIR)
        print("=== NL2SQL Batch Generation + Execution Verification Tool (Intelligent Enhanced Version) ===")

        global_target_db_type = select_target_db()
        print(f"\nLoading complete rule file for {global_target_db_type}...")
        db_rule_content = load_db_rule_file(global_target_db_type)

        # [Initialization] Intelligent Error Analyzer
        print("🛠️  Initializing Intelligent Error Analyzer...")
        error_analyzer = get_error_analyzer(global_target_db_type)

        print("\n📥 Loading input data...")
        retrieval_items = get_retrieval_items(global_target_db_type)

        final_results = []
        total_items = len(retrieval_items)

        for idx, item in enumerate(retrieval_items):
            item_index = item.get("index", idx)
            question = item["question"]
            nl2_rewrite = item["nl2_rewrite"]
            db_id = item.get("db_id")
            question_id = item.get("question_id")
            true_tc_str = item.get("true_tables_columns") # Key: Schema Info
            target_db_type = global_target_db_type

            print(f"\n{'=' * 60}")
            print(f"Processing Item {idx + 1}/{total_items} (ID: {question_id}) | DB: {db_id}")
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
                    print(f"❌ Failed to connect to database '{db_id}'")

            item_result = {
                "index": item_index, "question": question, "nl2_rewrite": nl2_rewrite,
                "question_id": question_id, "db_id": db_id, "target_db_type": target_db_type,
                "first_generated_sql": "", "first_execution_status": "pending", "first_error_msg": None,
                "second_generated_sql": None, "second_execution_status": None, "second_error_msg": None,
                "magic_generated_sql": None, "magic_execution_status": None,
                "semantic_generated_sql": None, "semantic_execution_status": None, # [New]
                "final_execution_status": "pending", "true_tables_columns": true_tc_str,
                "error_analysis": None
            }

            current_best_sql = ""
            current_execution_status = "failed"

            try:
                # === Round 1: Initial Generation ===
                print(f"\n>>> Round 1: Initial Generation")
                process_logger.log_phase("Round 1: Initial Generation")

                prompt_first = build_prompt(item, target_db_type, db_rule_content)
                process_logger.log_prompt("Round 1 Prompt", prompt_first)

                sql_res_1 = call_modelscope_api_single(prompt_first, target_db_type)
                process_logger.log_llm_response(sql_res_1)

                parsed_1 = parse_sql_result(sql_res_1, target_db_type)
                sql_1 = parsed_1.get(target_db_type, "")

                if not sql_1:
                    print(f"❌ Generation Failed")
                    item_result["first_generated_sql"] = "Generation Failed"
                    item_result["final_execution_status"] = "skip"
                else:
                    if true_tc_str: sql_1 = correct_sql_schema(sql_1, true_tc_str)
                    item_result["first_generated_sql"] = sql_1
                    print(f"📝 SQL: {sql_1[:100]}...")

                    if current_db_connection:
                        print(f"🚀 Verifying Execution...")
                        sql_run_1 = clean_sql_for_execution(sql_1)
                        exec_1 = test_sql_execution(sql_run_1, target_db_type, current_db_connection)

                        item_result["first_execution_status"] = exec_1["status"]
                        item_result["first_error_msg"] = exec_1["error"]
                        process_logger.log_sql_execution(sql_1, exec_1["status"], exec_1["error"])

                        if exec_1["status"] == "success":
                            print(f"✅ Success")
                            current_best_sql = sql_1
                            current_execution_status = "success"
                            item_result["final_execution_status"] = "success"
                        else:
                            print(f"❌ Failed: {exec_1['error'][:100]}")
                            item_result["final_execution_status"] = "failed"
                    else:
                        item_result["final_execution_status"] = "skip"

                # === Round 2: Syntax Correction (Including Intelligent Diagnosis) ===
                if current_execution_status != "success" and item_result["final_execution_status"] != "skip":
                    print(f"\n>>> Round 2: Syntax Correction")
                    process_logger.log_phase("Round 2: Syntax Correction")

                    # 1. Intelligent Analysis
                    print(f"🔍 Starting Intelligent Error Diagnosis...")
                    error_analysis = error_analyzer.analyze_error(
                        sql=item_result["first_generated_sql"],
                        error_msg=item_result["first_error_msg"],
                        true_tc_str=true_tc_str,
                        nl2_rewrite=nl2_rewrite,
                        question=question
                    )
                    item_result["error_analysis"] = error_analysis
                    
                    # Print log
                    reason_preview = error_analysis.get('inferred_reason', '')[:100]
                    print(f"   🧠 Diagnosis Result: {reason_preview}...")
                    print(f"   🗝️ Suggested Keywords: {error_analysis.get('suggested_keywords')}")

                    # 2. Enhanced Retrieval (Core: Will not crash anymore)
                    rag_content = secondary_rag_retrieval(
                        question=question,
                        error_msg=item_result["first_error_msg"],
                        db_type=target_db_type,
                        error_analysis=error_analysis
                    )
                    item_result["secondary_rag_content"] = rag_content

                    # 3. Generate Prompt
                    prompt_2 = build_prompt(
                        item, 
                        target_db_type, 
                        secondary_rag_content=rag_content,
                        error_msg=item_result["first_error_msg"],
                        first_sql=item_result["first_generated_sql"]
                    )
                    process_logger.log_prompt("Round 2 Prompt", prompt_2)

                    sql_res_2 = call_modelscope_api_single(prompt_2, target_db_type)
                    process_logger.log_llm_response(sql_res_2)
                    
                    parsed_2 = parse_sql_result(sql_res_2, target_db_type)
                    sql_2 = parsed_2.get(target_db_type, "")

                    if sql_2:
                        if true_tc_str: sql_2 = correct_sql_schema(sql_2, true_tc_str)
                        item_result["second_generated_sql"] = sql_2
                        print(f"📝 SQL: {sql_2[:100]}...")
                        process_logger.log_syntax_refinement(item_result["first_error_msg"], rag_content, sql_2)

                        if current_db_connection:
                            print(f"🚀 Verifying Execution...")
                            sql_run_2 = clean_sql_for_execution(sql_2)
                            exec_2 = test_sql_execution(sql_run_2, target_db_type, current_db_connection)

                            item_result["second_execution_status"] = exec_2["status"]
                            item_result["second_error_msg"] = exec_2["error"]
                            item_result["final_execution_status"] = exec_2["status"]
                            process_logger.log_sql_execution(sql_2, exec_2["status"], exec_2["error"])

                            if exec_2["status"] == "success":
                                print(f"✅ Success")
                                current_best_sql = sql_2
                                current_execution_status = "success"
                            else:
                                print(f"❌ Failed: {exec_2['error'][:100]}")

                # === Round 3: Magic ===
                if current_execution_status != "success" and item_result["final_execution_status"] != "skip":
                    if magic_adapter and item_result["second_generated_sql"]:
                        print(f"\n>>> Magic Module (Multi-turn Enabled)")
                        process_logger.log_phase("Magic Module Intervention")

                        magic_status, magic_sql = magic_adapter.run_magic_fix(
                            question=question,
                            nl2_rewrite=nl2_rewrite,
                            incorrect_sql=item_result["second_generated_sql"],
                            error_msg=item_result["second_error_msg"],
                            dialect=target_db_type,
                            true_tc_str=true_tc_str,
                            logger=process_logger,
                            max_retries=2
                        )
                        item_result["magic_generated_sql"] = magic_sql
                        item_result["magic_execution_status"] = magic_status
                        if magic_status == "success":
                            print(f"✨ Magic Final Fix Successful")
                            current_best_sql = magic_sql
                            current_execution_status = "success"
                            item_result["final_execution_status"] = "success"

                # === Round 4: Semantic (New Module) ===
                # Perform semantic verification only if SQL can be executed successfully
                if current_execution_status == "success" and current_best_sql:
                    print(f"\n>>> Round 4: Semantic Verification")
                    process_logger.log_phase("Round 4: Semantic Verification")
                    
                    try:
                        is_pass, fail_reason = verify_sql_logic(question, nl2_rewrite, current_best_sql, target_db_type)
                        # Note: If log_semantic_check is not defined in ProcessLogger, comment this out or implement it yourself
                        if hasattr(process_logger, 'log_semantic_check'):
                            process_logger.log_semantic_check(is_pass, fail_reason)

                        if is_pass:
                            print(f"✅ Semantic Check Passed")
                        else:
                            print(f"⚠️ Semantic Check Failed: {fail_reason}")
                            print(f"🔄 Starting Logic Correction...")
                            
                            prompt_fix = build_logic_fix_prompt(
                                question=question, nl2_rewrite=nl2_rewrite,
                                wrong_sql=current_best_sql, analysis_reason=fail_reason,
                                target_db_type=target_db_type,
                                true_tables_columns=true_tc_str  # Pass Schema
                            )
                            process_logger.log_prompt("Round 4 Prompt", prompt_fix)

                            try:
                                sql_res_fix = call_modelscope_api_single(prompt_fix, target_db_type)
                                parsed_fix = parse_sql_result(sql_res_fix, target_db_type)
                                fixed_sql = parsed_fix.get(target_db_type, "")

                                if fixed_sql:
                                    # [Core] Schema Auto-Correction
                                    if true_tc_str:
                                        fixed_sql = correct_sql_schema(fixed_sql, true_tc_str)

                                    if hasattr(process_logger, 'log_logic_refinement'):
                                        process_logger.log_logic_refinement(fail_reason, fixed_sql)
                                    
                                    sql_run_fix = clean_sql_for_execution(fixed_sql)

                                    if current_db_connection:
                                        print(f"🚀 Verifying execution of corrected SQL...")
                                        exec_fix = test_sql_execution(sql_run_fix, target_db_type, current_db_connection)
                                        process_logger.log_sql_execution(fixed_sql, exec_fix["status"], exec_fix["error"])
                                        
                                        # Record to item_result
                                        item_result["semantic_generated_sql"] = fixed_sql
                                        item_result["semantic_execution_status"] = exec_fix["status"]

                                        if exec_fix["status"] == "success":
                                            print(f"✅ Semantic correction executed successfully")
                                            item_result["final_execution_status"] = "success"
                                            current_best_sql = fixed_sql # Update best SQL
                                            
                                            # Save failed case for later analysis
                                            save_semantic_failure(item_index, question, nl2_rewrite, item_result["magic_generated_sql"] or item_result["second_generated_sql"] or item_result["first_generated_sql"],
                                                                  fail_reason, fixed_sql)
                                        else:
                                            print(f"❌ Execution failed after semantic correction: {exec_fix['error'][:100]}")
                                    else:
                                         # Assume success and save when no connection
                                         item_result["semantic_generated_sql"] = fixed_sql
                                         current_best_sql = fixed_sql
                                         print(f"⚠️ No database connection, only saving semantically corrected SQL")
                            except Exception as e:
                                print(f"❌ Exception in semantic correction process: {e}")
                                traceback.print_exc()
                    except Exception as e:
                        print(f"❌ Exception in semantic verification module: {e}")

                final_results.append(item_result)

            except Exception as e:
                print(f"❌ Processing Exception: {e}")
                traceback.print_exc()
                item_result["final_execution_status"] = "error"
                final_results.append(item_result)
            finally:
                if current_db_connection:
                    try: current_db_connection.close()
                    except: pass
                process_logger.end_question(item_result["final_execution_status"])

        # Save results
        print(f"\n{'=' * 60}\nProcessing completed, saving...")
        all_json_results = []
        for r in final_results:
            # [Logic Modification] Prioritize semantically corrected and successful SQL, otherwise fallback to normal logic
            if r.get("semantic_generated_sql") and r.get("semantic_execution_status") == "success":
                final_sql = r["semantic_generated_sql"]
            else:
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
        print("Done.")

    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()