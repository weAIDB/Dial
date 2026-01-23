# schema_corrector.py
import re
from difflib import get_close_matches

def parse_schema_string(schema_str):
    """
    将 "table.col,table.col" 字符串解析为字典 {table: [cols]}
    """
    if not schema_str:
        return {}
    
    schema_map = {}
    try:
        # 处理逗号分隔，同时去除可能存在的空格
        items = [x.strip() for x in schema_str.split(',')]
        for item in items:
            if '.' in item:
                table, col = item.split('.', 1)
                table = table.strip().lower() # 统一小写处理
                col = col.strip().lower()
                if table not in schema_map:
                    schema_map[table] = set()
                schema_map[table].add(col)
    except Exception as e:
        print(f"⚠️ Schema 解析警告: {e}")
    return schema_map

def correct_sql_schema(sql, true_tc_str):
    """
    对 SQL 中的列名进行纠错，但包含【ID豁免机制】
    """
    if not sql or not true_tc_str:
        return sql

    # 1. 解析 Schema
    schema_map = parse_schema_string(true_tc_str)
    if not schema_map:
        return sql

    # 2. 提取 SQL 中的 table.column 模式
    # 正则解释：匹配 字母/数字/下划线 . 字母/数字/下划线/"
    # 兼容 table.column 和 table."column"
    pattern = re.compile(r'\b([a-zA-Z0-9_]+)\.([a-zA-Z0-9_"]+)\b')
    
    # 记录需要替换的映射 (Old -> New)
    replacements = {}

    matches = pattern.findall(sql)
    for table_alias, col_raw in matches:
        # 清理列名引号（用于比对）
        col_name = col_raw.replace('"', '').lower()
        
        # ---------------------------------------------------------
        # 核心逻辑：ID 豁免 (ID Immunity) - 保护推断出的 ID 不被乱改
        # ---------------------------------------------------------
        if col_name == 'id' or col_name.endswith('_id'):
            # 如果是 ID 列，即使不在 Schema 中，也【绝对不改】
            continue 

        # ---------------------------------------------------------
        # 普通列纠错逻辑
        # ---------------------------------------------------------
        # 检查这个列名是否存在于 Schema 的任何表中
        # (简化逻辑：只要Schema里有这个列名就行，不管属于哪个表，防止Alias解析困难)
        all_valid_columns = set()
        for cols in schema_map.values():
            all_valid_columns.update(cols)
            
        if col_name in all_valid_columns:
            continue # 列名存在，无需修改

        # 如果列名不存在，尝试找最相似的
        # 场景：company_name -> name
        close_matches = get_close_matches(col_name, list(all_valid_columns), n=1, cutoff=0.7)
        
        if close_matches:
            best_match = close_matches[0]
            # 只有当相似度足够高，且不是把 ID 改成 Name 时才替换
            print(f"🔧 [Schema修正] 检测到幻觉列: {col_raw} -> 修正为: {best_match}")
            
            # 更稳妥的替换方式
            old_str = f"{table_alias}.{col_raw}"
            new_str = f"{table_alias}.{best_match}"
            
            # 如果原列名有引号，保留引号风格（针对 Oracle）
            if '"' in col_raw and '"' not in best_match:
                 new_str = f'{table_alias}."{best_match.upper()}"' # Oracle通常喜欢大写
            
            replacements[old_str] = new_str

    # 执行替换
    corrected_sql = sql
    for old, new in replacements.items():
        corrected_sql = corrected_sql.replace(old, new)

    return corrected_sql