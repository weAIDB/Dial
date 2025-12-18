import json


def filter_json_data(json1_path, json2_path, output_path):
    # 1. 加载数据
    with open(json1_path, 'r', encoding='utf-8') as f1, \
            open(json2_path, 'r', encoding='utf-8') as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)

    # 2. 提取 json1 中 data 为空的 question_id
    # 使用 set (集合) 提高后续查找效率
    invalid_ids = {
        item['question_id']
        for item in data1
        if not item.get('result', {}).get('data')
    }

    # 3. 保留 json2 中 question_id 不在 invalid_ids 里的项
    filtered_data = [
        item for item in data2
        if item.get('question_id') not in invalid_ids
    ]

    # 4. 输出到新文件
    with open(output_path, 'w', encoding='utf-8') as f_out:
        json.dump(filtered_data, f_out, indent=4, ensure_ascii=False)

    print(f"处理完成！已过滤掉 {len(invalid_ids)} 个 ID，结果已保存至 {output_path}")

# 使用示例
filter_json_data('true_result_all.json', 'dataset.json', 'dataset_no_empty.json')