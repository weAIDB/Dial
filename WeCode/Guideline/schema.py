import json

def build_din_schema_from_json(db_info: dict) -> str:
    """
    Builds a DIN-SQL style schema string from a pre-parsed database JSON object.
    """
    table_names = db_info['table_names_original']
    column_names = db_info['column_names_original']
    foreign_keys_pairs = db_info['foreign_keys']

    tables = {}
    # Initialize tables and columns
    for i, table_name in enumerate(table_names):
        tables[table_name] = []

    # Populate columns for each table
    for i, (table_idx, col_name) in enumerate(column_names):
        if table_idx == -1: # Skip '*' column
            continue
        table_name = table_names[table_idx]
        tables[table_name].append(col_name)

    # Format foreign keys
    foreign_keys_str_list = []
    # The 'foreign_keys' field is a list of pairs of column indices.
    for col_idx_1, col_idx_2 in foreign_keys_pairs:
        if col_idx_1 < len(column_names) and col_idx_2 < len(column_names):
            table_idx_1, col_name_1 = column_names[col_idx_1]
            table_idx_2, col_name_2 = column_names[col_idx_2]
            
            if table_idx_1 != -1 and table_idx_2 != -1:
                table_name_1 = table_names[table_idx_1]
                table_name_2 = table_names[table_idx_2]
                foreign_keys_str_list.append(f"{table_name_1}.{col_name_1} = {table_name_2}.{col_name_2}")

    # Assemble the final string
    schema_parts = []
    for table_name, cols in tables.items():
        # Prepend '*' to the column list to match the exact DIN-SQL format
        all_cols = ['*'] + cols
        schema_parts.append(f"Table {table_name}, columns = [{','.join(all_cols)}]")
    
    if foreign_keys_str_list:
        schema_parts.append(f"Foreign_keys = [{','.join(foreign_keys_str_list)}]")
        
    return "\n".join(schema_parts)

# --- Example Usage ---
# 1. Load tables.json with UTF-8 encoding
# with open('data/tables.json', 'r', encoding='utf-8') as f:
#     # This file is large, so we can't load it all at once.
#     # For demonstration, we'll assume we have the JSON object for one db.
#     # In a real script, you would iterate through the file or load it line-by-line.
#     all_schemas = json.load(f)

# # 2. Find the schema for a specific db_id
# db_id_to_find = "research_project_evaluation_and_scoring"
# # In the full 'all_schemas' list, you would search like this:
# target_schema_info = next((item for item in all_schemas if item["db_id"] == db_id_to_find), None)

# # 3. Generate the DIN-SQL style schema string
# if target_schema_info:
#     din_schema = build_din_schema_from_json(target_schema_info)
#     print(f"--- Schema for {db_id_to_find} ---")
#     print(din_schema)
