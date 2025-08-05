from train_vanna import MyVanna
import json
from datetime import datetime



def generate_sql_from_questions(input_json_path, output_json_path):
    """从JSON文件读取问题，生成SQL并保存到新JSON文件"""
    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            question_data = json.load(f)

        print(f"成功加载JSON文件: {input_json_path}")
        print(f"共找到 {len(question_data)} 条问题数据")

        output_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "source_file": input_json_path,
                "total_questions": len(question_data)
            },
            "results": []
        }

        processed_count = 0
        success_count = 0

        for item in question_data:
            question_id = item.get('question_id', 'unknown')
            db_id = item.get('db_id', 'unknown')
            question = item.get('question', '')
            original_sql = item.get('SQL', '')
            difficulty = item.get('difficulty', 'unknown')

            if not question:
                print(f"\n问题ID {question_id} 没有question字段，跳过")
                continue

            processed_count += 1
            print(f"\n处理问题ID: {question_id}")
            print(f"数据库: {db_id}")
            print(f"问题: {question}")

            result_entry = {
                "question_id": question_id,
                "db_id": db_id,
                "question": question,
                "original_sql": original_sql,
                "difficulty": difficulty,
                "generated_sql": "",
                "status": "failed",
                "error": ""
            }

            try:
                generated_sql = vn.generate_sql(question=question)
                result_entry["generated_sql"] = generated_sql
                result_entry["status"] = "success"
                success_count += 1
                print(f"成功生成SQL: {generated_sql}")
            except Exception as e:
                error_msg = str(e)
                result_entry["error"] = error_msg
                print(f"生成SQL时出错: {error_msg}")

            output_data["results"].append(result_entry)

        output_data["metadata"]["processed_count"] = processed_count
        output_data["metadata"]["success_count"] = success_count
        output_data["metadata"][
            "success_rate"] = f"{(success_count / processed_count) * 100:.2f}%" if processed_count > 0 else "0%"

        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n处理完成! 结果已保存到: {output_json_path}")
        print(f"成功率: {output_data['metadata']['success_rate']}")

    except Exception as e:
        print(f"处理生成SQL时出错: {str(e)}")


if __name__ == "__main__":

    # 初始化Vanna实例 (使用与训练相同的配置)
    vn = MyVanna({'api_key': '', 'model': 'qwen-max'})

    generate_sql_from_questions(
        input_json_path="mini_dev_mysql.json",
        output_json_path="generated_sql_results.json"
    )