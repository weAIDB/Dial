import json
import os

# -------------------------- 配置路径 --------------------------
# 输入JSON文件路径（原始数据）
input_file_path = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\translator4.0\输出结果\第三次测试结果\nl2_rewrite98.json"
# 输出目录路径
output_dir = r"C:\Users\xuhm3\OneDrive\Desktop\NL2SQL\rag方言判断\translator4.0\nl2rag"
# 输出文件名
output_file_name = "nl2.0.json"
output_file_path = os.path.join(output_dir, output_file_name)

# -------------------------- 核心逻辑 --------------------------
def extract_and_save_data():
    # 1. 确保输出目录存在（不存在则创建）
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建输出目录：{output_dir}")

    # 2. 读取输入JSON文件
    try:
        with open(input_file_path, "r", encoding="utf-8") as f:
            input_data = json.load(f)
        print(f"成功读取输入文件，共{len(input_data)}条数据")
    except FileNotFoundError:
        print(f"错误：未找到输入文件 {input_file_path}")
        return
    except json.JSONDecodeError:
        print(f"错误：输入文件 {input_file_path} 不是合法的JSON格式")
        return

    # 3. 提取目标字段并整理格式
    output_data = []
    for idx, item in enumerate(input_data):
        try:
            # 提取核心字段（严格匹配你要求的字段名和层级）
            extracted_item = {
                "question": item.get("question", ""),  # 原始question字段
                "nl2_rewrite": item["nl2_rewrite"].get("Question2", ""),  # nl2_rewrite下的Question2
                "teps Count Total": item["nl2_rewrite"]["Steps Count"].get("total", 0),  # Steps Count下的total，重命名为teps Count Total
                "question_id": item.get("question_id", ""),  # 原始question_id
                "difficulty": item.get("difficulty", "")  # 原始difficulty
            }
            output_data.append(extracted_item)
        except KeyError as e:
            print(f"警告：第{idx+1}条数据缺失字段 {e}，已跳过该条")
            continue

    # 4. 将整理后的数据写入输出JSON文件
    try:
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"成功生成输出文件：{output_file_path}")
        print(f"共提取并保存{len(output_data)}条有效数据")
    except Exception as e:
        print(f"错误：写入输出文件失败，原因：{e}")

# -------------------------- 执行脚本 --------------------------
if __name__ == "__main__":
    extract_and_save_data()