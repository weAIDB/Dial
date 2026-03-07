# result_saver.py
import json
import os
from datetime import datetime
from .config import JSON_OUTPUT_PATH, FINAL_REPORT_PATH

def save_json_results(all_json_results, output_path, target_db_type):
    """Save simplified SQL generation results"""
    try:
        if os.path.exists(output_path):
            backup_path = output_path.replace('.json', f'_backup_{target_db_type}.json')
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            print(f"Original JSON file backed up to: {backup_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_json_results, f, ensure_ascii=False, indent=2, separators=(',', ': '))
        
        print(f"JSON result file saved to: {output_path}")
        print(f"Contains {len(all_json_results)} results (keeping only specified fields)")
        
        return output_path
        
    except Exception as e:
        raise RuntimeError(f"Failed to save JSON file: {str(e)}") from e

def save_text_results(all_results, output_dir, target_db_type):
    """Save results in text format"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"all_sql_results_{target_db_type}_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"SQL Generation Results Summary ({target_db_type})\n")
        f.write(f"Generation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Model Used: {os.getenv('MODEL_NAME', 'unknown')}\n")
        f.write(f"SQL Execution Timeout: {os.getenv('SQL_EXECUTION_TIMEOUT', 'unknown')} seconds\n")
        f.write(f"Total Items Processed: {len(all_results)}\n")
        f.write("="*80 + "\n\n")
        
        for idx, result in enumerate(all_results, 1):
            f.write(f"=== Result Item {idx}/{len(all_results)} ===\n")
            f.write(f"Original Question: {result['question']}\n")
            f.write(f"{target_db_type}: {result[target_db_type]}\n")
            f.write("\n" + "-"*80 + "\n\n")
    
    print(f"Text result file saved to: {filepath}")
    return filepath

def save_final_report(final_results):
    """Save final execution report (including complete process information)"""
    try:
        # Backup original report
        if os.path.exists(FINAL_REPORT_PATH):
            backup_path = FINAL_REPORT_PATH.replace('.json', f'_backup_{datetime.now().strftime("%Y%m%d%H%M%S")}.json')
            with open(FINAL_REPORT_PATH, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            print(f"Original report backed up to: {backup_path}")
        
        # Write new report
        with open(FINAL_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 Final execution report saved to: {FINAL_REPORT_PATH}")
        
        # Statistics
        total = len(final_results)
        success_first = len([r for r in final_results if r["first_execution_status"] == "success"])
        success_second = len([r for r in final_results if r["final_execution_status"] == "success"])
        failed = len([r for r in final_results if r["final_execution_status"] == "failed"])
        skipped = len([r for r in final_results if r["final_execution_status"] == "skip"])
        error = len([r for r in final_results if r["final_execution_status"] == "error"])
        dead_loop_count = len([r for r in final_results if 
                             (r["first_error_msg"] and ("infinite loop" in str(r["first_error_msg"]).lower() or "timeout" in str(r["first_error_msg"]).lower())) or
                             (r["second_error_msg"] and ("infinite loop" in str(r["second_error_msg"]).lower() or "timeout" in str(r["second_error_msg"]).lower()))])
        
        print(f"\nStatistics Summary:")
        print(f"Total Items Processed: {total}")
        print(f"First Execution Success: {success_first}")
        print(f"Final Execution Success (including correction): {success_second}")
        print(f"Final Execution Failed: {failed}")
        print(f"Items Skipped: {skipped}")
        print(f"Processing Errors: {error}")
        print(f"Infinite Loop/Timeout Cases: {dead_loop_count}")
        
        return FINAL_REPORT_PATH
    except Exception as e:
        raise RuntimeError(f"Failed to save final report: {str(e)}") from e