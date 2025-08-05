import pymysql
import json
from datetime import datetime


def export_tables_to_json(host, user, password, database, output_file=None):
    """
    导出MySQL数据库中所有表的结构为JSON格式

    :param host: MySQL主机地址
    :param user: 用户名
    :param password: 密码
    :param database: 数据库名
    :param output_file: 输出JSON文件路径，如果不指定则打印到控制台
    """
    try:
        # 连接MySQL数据库
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        print(f"成功连接到数据库: {database}")

        with connection.cursor() as cursor:
            # 获取所有表名
            cursor.execute("SHOW TABLES")
            tables = [table[f"Tables_in_{database}"] for table in cursor.fetchall()]

            database_meta = {
                "metadata": {
                    "host": host,
                    "database": database,
                    "export_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "table_count": len(tables)
                },
                "tables": {}
            }

            # 为每个表获取结构信息
            for table in tables:
                # 获取建表语句
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                create_table_stmt = cursor.fetchone()[f"Create Table"]

                # 构建表结构数据
                table_meta = {
                    "ddl": create_table_stmt
                }

                database_meta["tables"][table] = table_meta

            # 转换为JSON格式
            json_output = json.dumps(database_meta, indent=2, ensure_ascii=False)

            # 输出结果
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(json_output)
                print(f"成功导出JSON到文件: {output_file}")
            else:
                print(json_output)

    except pymysql.Error as e:
        print(f"数据库错误: {e}")
    except json.JSONEncodeError as e:
        print(f"JSON编码错误: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
            print("数据库连接已关闭")


# 使用示例
if __name__ == "__main__":
    # 配置数据库连接信息
    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "123456",
        "database": "bird"
    }

    # 调用函数导出JSON（可以指定输出文件路径，如不指定则打印到控制台）
    export_tables_to_json(**db_config, output_file="database_structure.json")