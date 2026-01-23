# result_saver.py
import json
import os
from datetime import datetime
from config import JSON_OUTPUT_PATH, FINAL_REPORT_PATH

def save_json_results(all_json_results, output_path, target_db_type):
    """保存精简的SQL生成结果"""
    try:
        if os.path.exists(output_path):
            backup_path = output_path.replace('.json', f'_backup_{target_db_type}.json')
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            print(f"已备份原有JSON文件到: {backup_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_json_results, f, ensure_ascii=False, indent=2, separators=(',', ': '))
        
        print(f"JSON结果文件已保存到: {output_path}")
        print(f"共包含 {len(all_json_results)} 条结果（仅保留指定字段）")
        
        return output_path
        
    except Exception as e:
        raise RuntimeError(f"保存JSON文件失败: {str(e)}") from e

def save_text_results(all_results, output_dir, target_db_type):
    """保存文本格式结果"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"all_sql_results_{target_db_type}_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"SQL生成结果汇总（{target_db_type}）\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"使用模型: {os.getenv('MODEL_NAME', 'unknown')}\n")
        f.write(f"SQL执行超时时间: {os.getenv('SQL_EXECUTION_TIMEOUT', 'unknown')}秒\n")
        f.write(f"总处理项数: {len(all_results)}\n")
        f.write("="*80 + "\n\n")
        
        for idx, result in enumerate(all_results, 1):
            f.write(f"=== 结果项 {idx}/{len(all_results)} ===\n")
            f.write(f"原始问题: {result['question']}\n")
            f.write(f"{target_db_type}: {result[target_db_type]}\n")
            f.write("\n" + "-"*80 + "\n\n")
    
    print(f"文本结果文件已保存到: {filepath}")
    return filepath

def save_final_report(final_results):
    """保存最终执行报告（包含完整流程信息）"""
    try:
        # 备份原有报告
        if os.path.exists(FINAL_REPORT_PATH):
            backup_path = FINAL_REPORT_PATH.replace('.json', f'_backup_{datetime.now().strftime("%Y%m%d%H%M%S")}.json')
            with open(FINAL_REPORT_PATH, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            print(f"已备份原有报告到：{backup_path}")
        
        # 写入新报告
        with open(FINAL_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 最终执行报告已保存到：{FINAL_REPORT_PATH}")
        
        # 统计结果
        total = len(final_results)
        success_first = len([r for r in final_results if r["first_execution_status"] == "success"])
        success_second = len([r for r in final_results if r["final_execution_status"] == "success"])
        failed = len([r for r in final_results if r["final_execution_status"] == "failed"])
        skipped = len([r for r in final_results if r["final_execution_status"] == "skip"])
        error = len([r for r in final_results if r["final_execution_status"] == "error"])
        dead_loop_count = len([r for r in final_results if 
                             (r["first_error_msg"] and ("死循环" in r["first_error_msg"] or "超时" in r["first_error_msg"])) or
                             (r["second_error_msg"] and ("死循环" in r["second_error_msg"] or "超时" in r["second_error_msg"]))])
        
        print(f"\n统计汇总：")
        print(f"总处理项数：{total}")
        print(f"首次执行成功：{success_first}")
        print(f"最终执行成功（含二次修正）：{success_second}")
        print(f"最终执行失败：{failed}")
        print(f"跳过项：{skipped}")
        print(f"处理异常：{error}")
        print(f"死循环/超时案例数：{dead_loop_count}")
        
        return FINAL_REPORT_PATH
    except Exception as e:
        raise RuntimeError(f"保存最终报告失败：{str(e)}") from e