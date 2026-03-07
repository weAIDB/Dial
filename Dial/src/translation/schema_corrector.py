import re
from difflib import get_close_matches

# Common Oracle Reserved Words List
ORACLE_RESERVED_WORDS = {
    "ACCESS", "ADD", "ALL", "ALTER", "AND", "ANY", "AS", "ASC", "AUDIT", "BETWEEN", "BY", "CHAR", "CHECK", "CLUSTER",
    "COLUMN", "COMMENT", "COMPRESS", "CONNECT", "CREATE", "CURRENT", "DATE", "DECIMAL", "DEFAULT", "DELETE", "DESC",
    "DISTINCT", "DROP", "ELSE", "EXCLUSIVE", "EXISTS", "FILE", "FLOAT", "FOR", "FROM", "GRANT", "GROUP", "HAVING",
    "IDENTIFIED", "IMMEDIATE", "IN", "INCREMENT", "INDEX", "INITIAL", "INSERT", "INTEGER", "INTERSECT", "INTO", "IS",
    "LEVEL", "LIKE", "LOCK", "LONG", "MAXEXTENTS", "MINUS", "MLSLABEL", "MODE", "MODIFY", "NOAUDIT", "NOCOMPRESS",
    "NOT", "NOWAIT", "NULL", "NUMBER", "OFFLINE", "ON", "ONLINE", "OPTION", "OR", "ORDER", "PCTFREE", "PRIOR",
    "PRIVILEGES", "PUBLIC", "RAW", "RENAME", "RESOURCE", "REVOKE", "ROW", "ROWID", "ROWNUM", "SELECT", "SESSION",
    "SET", "SHARE", "SIZE", "SMALLINT", "START", "SUCCESSFUL", "SYNONYM", "SYSDATE", "TABLE", "THEN", "TO", "TRIGGER",
    "UID", "UNION", "UNIQUE", "UPDATE", "USER", "VALIDATE", "VALUES", "VARCHAR", "VARCHAR2", "VIEW", "WHENEVER",
    "WHERE", "WITH"
}

def parse_standard_schema(schema_str):
    """
    Parses standard Schema information.
    Returns: { "table_low": {"orig": "TableOrig", "cols": {"col_low": "ColOrig"}} }
    """
    schema_info = {}
    if not schema_str: return schema_info
    
    items = [x.strip() for x in schema_str.split(',')]
    for item in items:
        if '.' in item:
            t_orig, c_orig = item.split('.', 1)
            t_low, c_low = t_orig.strip().lower(), c_orig.strip().lower()
            
            if t_low not in schema_info:
                schema_info[t_low] = {"orig": t_orig.strip(), "cols": {}}
            schema_info[t_low]["cols"][c_low] = c_orig.strip()
    return schema_info

def extract_cte_names(sql):
    """
    Extracts CTE (Common Table Expression) names from SQL.
    Used to protect temporary tables defined in CTEs from being incorrectly corrected as physical tables.
    """
    cte_names = set()
    # Pattern: WITH table_name AS or , table_name AS
    pattern = re.compile(r'(?:WITH|,)\s+([a-zA-Z0-9_"]+)\s+AS\s*\(', re.IGNORECASE)
    matches = pattern.findall(sql)
    
    for m in matches:
        cte_name = m.replace('"', '').lower()
        if cte_name not in ["select", "from", "where", "group", "order"]: 
            cte_names.add(cte_name)
            
    return cte_names

def extract_physical_aliases(sql, valid_tables):
    """
    Parses SQL to establish mapping from aliases to table names.
    """
    # Matches FROM table alias or JOIN table alias
    pattern = re.compile(r'(?:FROM|JOIN)\s+([a-zA-Z0-9_"]+)\s+(?:AS\s+)?([a-zA-Z0-9_"]+)', re.IGNORECASE)
    matches = pattern.findall(sql)
    
    alias_map = {}
    for table_raw, alias_raw in matches:
        t_low = table_raw.replace('"', '').lower()
        a_low = alias_raw.replace('"', '').lower()
        
        # Only record alias if table name exists in known list (Physical + CTE)
        if t_low in valid_tables:
            alias_map[a_low] = t_low
            
    return alias_map

def correct_sql_schema(sql, true_tc_str, db_type="oracle"):
    if not sql or not true_tc_str: return sql
    
    db_type_low = db_type.lower()
    
    # 1. Parse Physical Schema
    schema_info = parse_standard_schema(true_tc_str)
    
    # 2. Extract CTE names and add to exemption list
    cte_names = extract_cte_names(sql)
    for cte in cte_names:
        if cte not in schema_info:
            # Mark as WILDCARD: columns are dynamically generated, skip spelling checks
            schema_info[cte] = {"orig": cte, "cols": "__WILDCARD__"}

    # 3. Get all valid table names
    valid_tables = set(schema_info.keys())
    
    # 4. Parse aliases
    alias_map = extract_physical_aliases(sql, valid_tables)
    
    # 5. Regex replacement logic
    pattern = re.compile(r'([a-zA-Z0-9_"]+)\.([a-zA-Z0-9_"]+)')

    def fix_match(match):
        prefix_raw = match.group(1)
        col_raw = match.group(2)
        
        prefix_low = prefix_raw.replace('"', '').lower()
        col_low = col_raw.replace('"', '').lower()
        
        # Determine target table
        target_table_low = None
        if prefix_low in valid_tables:
            target_table_low = prefix_low
        elif prefix_low in alias_map:
            target_table_low = alias_map[prefix_low]
            
        if not target_table_low:
            return f"{prefix_raw}.{col_raw}"
            
        table_meta = schema_info[target_table_low]
        valid_cols_dict = table_meta["cols"]
        
        # Skip check for CTE tables
        if valid_cols_dict == "__WILDCARD__":
            return f"{prefix_raw}.{col_raw}"
        
        # --- Physical Table Check Logic ---
        
        # 1. Exact Match
        if col_low in valid_cols_dict:
            final_col_name = valid_cols_dict[col_low]
        else:
            # 2. Fuzzy Match (Threshold increased to 0.85)
            # Replace only if spelling is very close (prevents status -> id)
            close_matches = get_close_matches(col_low, list(valid_cols_dict.keys()), n=1, cutoff=0.85)
            
            if close_matches:
                match_col = close_matches[0]
                
                # Semantic Defense Check
                # Prevents 'status'/'name' from being replaced by 'id' to avoid type errors (e.g., ORA-01722)
                is_risky = False
                semantic_keywords = ['status', 'name', 'type', 'date', 'mode']
                if 'id' in match_col and any(k in col_low for k in semantic_keywords):
                    is_risky = True
                
                if not is_risky:
                    final_col_name = valid_cols_dict[match_col]
                    print(f"🔧 [Schema Correction] {target_table_low}: {col_raw} -> {final_col_name}")
                else:
                    # Risky operation, refuse replacement
                    return f"{prefix_raw}.{col_raw}"
            else:
                return f"{prefix_raw}.{col_raw}"

        # 3. Format Output (Oracle enforces double quotes for reserved words)
        if "oracle" in db_type_low:
            if final_col_name.upper() in ORACLE_RESERVED_WORDS:
                return f'{prefix_raw}."{final_col_name.upper()}"'
            # If contains mixed case or special chars, protect with quotes
            if not final_col_name.isupper() and not final_col_name.islower():
                return f'{prefix_raw}."{final_col_name}"'
            return f"{prefix_raw}.{final_col_name}"
        
        elif "postgre" in db_type_low:
             if not final_col_name.islower():
                return f'{prefix_raw}."{final_col_name}"'
             return f"{prefix_raw}.{final_col_name}"

        return f"{prefix_raw}.{final_col_name}"

    return pattern.sub(fix_match, sql)