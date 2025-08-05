#  写目录
# import os

# # 定义根目录的绝对路径 - 这里应该是包含所有要遍历文件夹的上级目录
# base_dir = r"C:\copy\code\minidev\MINIDEV"

# # 定义要遍历的子目录（对应示例图里的顶级逻辑，可根据实际调整）
# root_dirs = [
#     "mysql",
#     "pg",
#     "sqlite",
#     "sqlite_pgsql_result"
# ]

# # 拼接完整路径
# full_dirs = [os.path.join(base_dir, dir_name) for dir_name in root_dirs]

# # 用于存储 Markdown 内容，调整标题为更贴近示例的结构
# md_content = "# 项目文件目录结构\n\n"

# def traverse_directory(current_dir, indent=""):
#     """
#     递归遍历目录，生成类似示例图的树形结构目录内容，支持标记“(可选)”文件夹
#     :param current_dir: 当前要遍历的目录路径
#     :param indent: 用于缩进的字符串，控制层级显示
#     :return: None，直接将内容追加到 md_content 变量中
#     """
#     global md_content
#     try:
#         # 列出当前目录下的所有条目（文件和文件夹），按名称排序，让输出更规整
#         entries = sorted(os.listdir(current_dir))  
#         for entry in entries:
#             entry_path = os.path.join(current_dir, entry)
#             # 处理文件夹
#             if os.path.isdir(entry_path):
#                 # 检查是否是“可选”文件夹，这里简单通过名称包含“(可选)”判断，可根据实际规则调整
#                 optional_mark = " (可选)" if "(可选)" in entry else ""
#                 md_content += f"{indent}└── {entry}{optional_mark}\n"
#                 # 递归遍历子文件夹，缩进增加“│   ”或“    ”来模拟树形结构，这里简化处理用四个空格
#                 traverse_directory(entry_path, indent + "    ")
#             # 处理文件
#             else:
#                 md_content += f"{indent}│   └── {entry}\n"
#     except Exception as e:
#         md_content += f"{indent}⚠️ 无法访问目录: {os.path.basename(current_dir)} ({str(e)})\n"

# if __name__ == "__main__":
#     # 检查基础目录是否存在
#     if not os.path.exists(base_dir):
#         print(f"错误: 基础目录不存在 - {base_dir}")
#     else:
#         for dir_path in full_dirs:
#             # 只处理存在的目录
#             if os.path.exists(dir_path) and os.path.isdir(dir_path):
#                 # 添加顶级目录标题，类似示例图里的顶级节点展示
#                 dir_name = os.path.basename(dir_path)
#                 md_content += f"└── {dir_name}\n"
#                 traverse_directory(dir_path, "    ")
#                 md_content += "\n"
#             else:
#                 md_content += f"## ⚠️ 缺失目录: {os.path.basename(dir_path)}\n\n"
    
#     # 定义要保存的文件路径
#     save_path = os.path.join(base_dir, "directory.md")
#     try:
#         with open(save_path, "w", encoding="utf-8") as f:
#             f.write(md_content)
#         print(f"目录结构已保存到 {save_path}")
#     except Exception as e:
#         print(f"保存文件时出错: {str(e)}")

#写readme
import os

def generate_readme():
    # 定义要保存的文件路径
    save_path = os.path.join(r"C:\copy\code\minidev\MINIDEV", "README.md")
    
    # 目录结构数据
    directory_structure = {
        "mysql": {
            "initial_code": [
                "mini_dev_mysql.json",
                "mysql1.json"
            ],
            "sql": [
                "mini_dev_mysql_gold.sql",
                "mysql1.sql"
            ],
            "脚本": [
                "mysql1.py"
            ]
        },
        "pg": {
            "initial_code": [
                "mini_dev_postgresql.json",
                "pg.json"
            ],
            "pg_mysql_result": {
                "conclude": [
                    "pg_mysql_conclusion.json",
                    "postgres_mysql_difference.json",
                    "radio.json",
                    "radio2.json",
                    "语法问题比例统计（排序后）.png"
                ],
                "run_result": [
                    "do.json",
                    "do.json.bak",
                    "undo.json"
                ]
            },
            "sql": [
                "mini_dev_postgresql_gold.sql",
                "pg.sql",
                "pg2mysql.sql",
                "pg_mysql_do.sql",
                "pg_mysql_undo.sql"
            ],
            "脚本": [
                "pg.py",
                "pg_mysql.py"
            ]
        },
        "sqlite": {
            "initial_code": [
                "dev_tables.json",
                "mini_dev_sqlite.json",
                "sqlite.json"
            ],
            "sql": [
                "mini_dev_sqlite_gold.sql",
                "sqlite.sql"
            ],
            "sqlite_mysql_result": {
                "conclude": [
                    "sqlite_mysql_difference.json"
                ],
                "run_result": [
                    "do.json",
                    "do.json.bak",
                    "undo.json",
                    "undo.json.backup"
                ],
                "脚本": [
                    "sqlite_mysql.py"
                ]
            },
            "sqlite_pgsql_result": {
                "conclude": [
                    "sqlite_pgsql_difference(1).json",
                    "sqlite_pgsql_difference.json"
                ],
                "run_result": [
                    "do.json",
                    "do.json.bak",
                    "undo.json"
                ],
                "脚本": [
                    "sqlite_pgsql.py"
                ]
            }
        }
    }
    
    # 构建README内容
    readme_content = []
    
    # 顶部锚点
    readme_content.append('<a name="readme-top"></a>\n')
    
    # 标题和徽章区域
    readme_content.append('<div align="center">')
    readme_content.append('\t<a href="#" target="_blank"><img src="https://img.shields.io/badge/project-Database%20Tools-brightgreen.svg" alt="Project"></a>')
    readme_content.append('\t<a href="https://www.python.org/downloads/" target="_blank"><img src="https://img.shields.io/badge/python-3.8%2B-brightgreen.svg" alt="Python supported"></a>')
    readme_content.append('\t<img alt="License" src="https://img.shields.io/badge/license-MIT-blue.svg">')
    readme_content.append('\n  <br />\n  <br />\n')
    readme_content.append('  <h1>多数据库交互工具</h1>')
    readme_content.append('  <p align="center">')
    readme_content.append('    <br />')
    readme_content.append('    <a href="#project-overview">项目概述</a>')
    readme_content.append('    ·')
    readme_content.append('    <a href="#directory-structure">目录结构</a>')
    readme_content.append('    ·')
    readme_content.append('    <a href="#core-functionality">核心功能</a>')
    readme_content.append('  </p>')
    readme_content.append('</div>\n')
    
    # 分隔线
    readme_content.append('----------------------------------------\n')
    
    # 项目概述
    readme_content.append('# <a name="project-overview"></a>项目概述\n')
    readme_content.append('本项目提供了MySQL、PostgreSQL和SQLite数据库之间的交互工具，包括数据库初始化配置、SQL脚本和Python交互脚本。\n')
    readme_content.append('通过这些工具，可以实现不同数据库之间的数据同步、差异分析和语法转换等功能。\n\n')
    
    # 目录结构
    readme_content.append('# <a name="directory-structure"></a>目录结构\n')
    readme_content.append('```\n.')
    
    # 递归函数：生成目录结构文本
    def add_directory_structure(data, prefix=""):
        for name, content in data.items():
            if isinstance(content, dict):
                readme_content.append(f'{prefix}└── {name}')
                new_prefix = prefix + "    "
                add_directory_structure(content, new_prefix)
            elif isinstance(content, list):
                readme_content.append(f'{prefix}└── {name}')
                new_prefix = prefix + "    "
                for item in content:
                    readme_content.append(f'{new_prefix}└── {item}')
    
    add_directory_structure(directory_structure)
    readme_content.append('```\n')
    
    # 核心功能说明
    readme_content.append('# <a name="core-functionality"></a>核心功能说明\n')
    
    # MySQL部分
    readme_content.append('## MySQL 模块\n')
    readme_content.append('- **initial_code**: 包含MySQL数据库的初始化配置文件\n')
    readme_content.append('  - `mini_dev_mysql.json`: 基础环境配置\n')
    readme_content.append('  - `mysql1.json`: 特定业务场景配置\n')
    readme_content.append('- **sql**: 包含MySQL数据库的SQL脚本\n')
    readme_content.append('  - `mini_dev_mysql_gold.sql`: 核心业务逻辑SQL\n')
    readme_content.append('  - `mysql1.sql`: 功能模块SQL\n')
    readme_content.append('- **脚本**: 包含MySQL交互的Python脚本\n')
    readme_content.append('  - `mysql1.py`: MySQL功能实现脚本\n\n')
    
    # PostgreSQL部分
    readme_content.append('## PostgreSQL 模块\n')
    readme_content.append('- **initial_code**: 包含PostgreSQL数据库的初始化配置文件\n')
    readme_content.append('  - `mini_dev_postgresql.json`: 基础环境配置\n')
    readme_content.append('  - `pg.json`: 特定业务场景配置\n')
    readme_content.append('- **pg_mysql_result**: 包含PostgreSQL与MySQL交互的结果数据\n')
    readme_content.append('  - `conclude`: 差异分析结论和统计数据\n')
    readme_content.append('  - `run_result`: 操作执行和回滚的结果记录\n')
    readme_content.append('- **sql**: 包含PostgreSQL数据库的SQL脚本\n')
    readme_content.append('  - `mini_dev_postgresql_gold.sql`: 核心业务逻辑SQL\n')
    readme_content.append('  - `pg.sql`: 基础功能SQL\n')
    readme_content.append('  - `pg2mysql.sql`: PostgreSQL转MySQL语法适配脚本\n')
    readme_content.append('  - `pg_mysql_do.sql`/`pg_mysql_undo.sql`: 正向/回滚交互SQL\n')
    readme_content.append('- **脚本**: 包含PostgreSQL交互的Python脚本\n\n')
    
    # SQLite部分
    readme_content.append('## SQLite 模块\n')
    readme_content.append('- **initial_code**: 包含SQLite数据库的初始化配置文件\n')
    readme_content.append('- **sql**: 包含SQLite数据库的SQL脚本\n')
    readme_content.append('- **sqlite_mysql_result**: 包含SQLite与MySQL交互的结果数据\n')
    readme_content.append('- **sqlite_pgsql_result**: 包含SQLite与PostgreSQL交互的结果数据\n\n')
    
    # 贡献部分
    readme_content.append('## 🤝 贡献\n')
    readme_content.append('欢迎参与本项目的开发和改进。如有任何建议或问题，请提交issue或pull request。\n\n')
    
    # 支持部分
    readme_content.append('## 🤍 支持\n')
    readme_content.append('如果发现任何bug，请在GitHub上提交issue。\n')
    readme_content.append('您也可以通过以下方式获得社区支持：\n')
    readme_content.append('* 在项目讨论区提问\n')
    readme_content.append('* 联系项目维护者\n\n')
    
    # 页脚
    readme_content.append('<div align="center">')
    readme_content.append('    <a href="#readme-top">回到顶部</a>')
    readme_content.append('</div>')
    
    # 保存到文件
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write('\n'.join(readme_content))
        print(f"README.md已成功生成并保存到: {save_path}")
    except Exception as e:
        print(f"生成文件时出错: {str(e)}")

if __name__ == "__main__":
    generate_readme()
    