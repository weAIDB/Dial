###pip install vanna[chromadb,mysql] dashscope
###pip install "posthog>=2.4.0,<6.0.0"
###pip install nbformat

from vanna.base import VannaBase
from vanna.chromadb import ChromaDB_VectorStore
from dashscope import Generation  #用于调Qwen
import random
import json

DERUG_INFO = None# 将大模型的输入输出记录在DERUG_INFO里


##自定义LLM
class QwenLLM(VannaBase):
    def __init__(self, config=None):
        self.model = config['model']
        self.api_key = config['api_key']

    def system_message(self, message: str):
        return {"role": "system", "content": message}

    def user_message(self, message: str):
        return {"role": "user", "content": message}

    def assistant_message(self, message: str):
        return {"role": "assistant", "content": message}

    def submit_prompt(self, prompt, **kwargs):
        resp = Generation.call(
            model=self.model,
            messages=prompt,
            seed=random.randint(1, 10000),
            result_format='message',
            api_key=self.api_key)
        answer = resp.output.choices[0].message.content
        global DEBUG_INFO
        DEBUG_INFO = (prompt, answer)
        return answer

##定义vanna
class MyVanna(ChromaDB_VectorStore, QwenLLM):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        QwenLLM.__init__(self, config=config)




##训练vanna，导入ddl和documentation
def train_ddls_from_json(json_file_path):
    """从JSON文件读取DDL并训练到vn"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            database_structure = json.load(f)

        print(f"成功加载JSON文件: {json_file_path}")
        print(
            f"数据库 '{database_structure['metadata']['database']}' 包含 {database_structure['metadata']['table_count']} 张表")

        trained_tables = 0
        for table_name, table_meta in database_structure['tables'].items():
            ddl = table_meta['ddl']

            print(f"\n正在训练表: {table_name}")

            try:
                vn.train(ddl=ddl)
                trained_tables += 1
                print(f"成功训练表: {table_name}")
            except Exception as e:
                print(f"训练表 {table_name} 时出错: {str(e)}")
                continue

        print(f"\n训练完成! 共成功训练 {trained_tables}/{database_structure['metadata']['table_count']} 张表")

    except Exception as e:
        print(f"处理DDL训练时出错: {str(e)}")


def train_documentation_from_json(json_file_path):
    """从JSON文件读取evidence字段并训练到vn"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            question_data = json.load(f)

        print(f"成功加载JSON文件: {json_file_path}")
        print(f"共找到 {len(question_data)} 条问题数据")

        trained_evidences = 0
        for item in question_data:
            question_id = item.get('question_id', '未知ID')
            evidence = item.get('evidence', '')

            if not evidence:
                print(f"\n问题ID {question_id} 没有evidence字段，跳过")
                continue

            print(f"\n正在训练问题ID: {question_id}")

            try:
                vn.train(documentation=evidence)
                trained_evidences += 1
                print(f"成功训练问题ID: {question_id}")
            except Exception as e:
                print(f"训练问题ID {question_id} 时出错: {str(e)}")
                continue

        print(f"\n训练完成! 共成功训练 {trained_evidences}/{len(question_data)} 条证据")

    except Exception as e:
        print(f"处理文档训练时出错: {str(e)}")


if __name__ == "__main__":

    vn = MyVanna({'api_key': '', 'model': 'qwen-max'})
    vn.connect_to_mysql(host='localhost', dbname='bird', user='root', password='123456', port=3306)

    # 训练DDL和文档
    train_ddls_from_json("database_structure.json")
    train_documentation_from_json("mini_dev_mysql.json")

    # 检查所有入库知识
    print("\n当前训练数据:")
    print(vn.get_training_data())
