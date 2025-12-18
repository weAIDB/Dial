import os
from sqlalchemy import create_engine, text
import pandas as pd
from decimal import Decimal

# --- Configuration ---
SQLITE_DB_ROOT_PATH = ""
MIGRATION_ROW_LIMIT = 100

# --- Database Credentials ---
DB_CONFIG = {
    'mysql': {
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', '123456'),
        'host': os.getenv('MYSQL_HOST', '192.168.103.1'),
        'port': os.getenv('MYSQL_PORT', '3306'),
    },
    'postgres': {
        'user': os.getenv('PG_USER', 'postgres'),
        'password': os.getenv('PG_PASSWORD', '123456'),
        'host': os.getenv('PG_HOST', '192.168.103.1'),
        'port': os.getenv('PG_PORT', '5433'),
    }
}

def normalize(data_set):
    """
    Normalizes the result set to handle type discrepancies (Decimal vs float)
    and formatting issues (whitespace trimming, float precision).
    Expects data_set to be an iterable of tuples/rows.
    """
    if not isinstance(data_set, set):
        return data_set
        
    norm_set = set()
    for row in data_set:
        new_row = []
        for item in row:
            if isinstance(item, Decimal):
                item = float(item)
            
            if isinstance(item, float):
                item = round(item, 6)
            elif isinstance(item, str):
                item = item.strip()
            
            new_row.append(item)
        norm_set.add(tuple(new_row))
    return norm_set

def setup_database_with_pandas(target_dialect, db_id):
    """Checks if a database exists. If not, creates and migrates it."""
    db_name = db_id.replace('-', '_')
    conf = DB_CONFIG[target_dialect]

    # Define connection URLs
    if target_dialect == 'mysql':
        server_url = f"mysql+pymysql://{conf['user']}:{conf['password']}@{conf['host']}:{conf['port']}"
        db_url = f"{server_url}/{db_name}"
    else: # postgres
        server_url = f"postgresql+psycopg2://{conf['user']}:{conf['password']}@{conf['host']}:{conf['port']}/postgres"
        db_url = f"postgresql+psycopg2://{conf['user']}:{conf['password']}@{conf['host']}:{conf['port']}/{db_name}"

    # 1. Check if the database already exists
    try:
        # Try to connect directly to the database. If it succeeds, it exists.
        existing_engine = create_engine(db_url)
        with existing_engine.connect() as conn:
            return existing_engine # DB exists, return engine and skip setup
    except Exception:
        pass

    # 2. Connect to server to create the database
    server_engine = create_engine(server_url)
    with server_engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
        conn.execute(text(f"CREATE DATABASE {db_name}"))

    # 3. Connect to the newly created database for migration
    target_engine = create_engine(db_url)

    # 4. Connect to source SQLite DB
    sqlite_db_path = os.path.join(SQLITE_DB_ROOT_PATH, db_id, f"{db_id}.sqlite")
    if not os.path.exists(sqlite_db_path):
        # Fallback to checking if it is just in data/databases/db_id/db_id.sqlite relative to current dir if needed
        # But for now we stick to the hardcoded path from reference implementation
        raise FileNotFoundError(f"SQLite database not found at {sqlite_db_path}")
    sqlite_engine = create_engine(f'sqlite:///{sqlite_db_path}')

    # 5. Use pandas to migrate data
    with sqlite_engine.connect() as sqlite_conn:
        cursor = sqlite_conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        table_names = [table[0] for table in cursor.fetchall() if not table[0].startswith('sqlite_')]
        
        for table_name in table_names:
            df = pd.read_sql_query(f'SELECT * FROM "{table_name}" LIMIT {MIGRATION_ROW_LIMIT}', sqlite_conn)
            df.to_sql(table_name, target_engine, if_exists='replace', index=False)
            
    return target_engine

def get_db_engine(dialect, db_id):
    if dialect == 'sqlite':
        db_path = os.path.join(SQLITE_DB_ROOT_PATH, db_id, f"{db_id}.sqlite")
        return create_engine(f'sqlite:///{db_path}') if os.path.exists(db_path) else None
    elif dialect in ['mysql', 'postgres']:
        conf = DB_CONFIG[dialect]
        if not all([conf['host'], conf['port'], conf['user']]):
            return None 
        try:
            return setup_database_with_pandas(dialect, db_id)
        except Exception as e:
            print(f"Error setting up {dialect} database for {db_id}: {e}")
            return None
    return None

def execute_query(engine, query):
    if not engine:
        return False, "Database Engine not available"
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query))
            # Convert SQLAlchemy Row objects to tuples, then to set for order-independent comparison
            raw_set = set(tuple(row) for row in result)
            # Normalize data types (Decimal -> float, etc.)
            normalized_set = normalize(raw_set)
            return True, normalized_set
    except Exception as e:
        return False, str(e)
