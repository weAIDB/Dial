# dataset/db_manager.py
# Migrates SQLite databases to MySQL, PostgreSQL, SQL Server, and DuckDB.
# Source: SQLite files (e.g. from duckdb_sqlite_databases.zip).
# Use run_migration.py to drive batch migration.

import os
import logging
import tempfile
import pandas as pd
import sqlite3
import duckdb
import re
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

from config import (
    DB_CONFIG,
    MIGRATION_ROW_LIMIT,
    DATA_SOURCES,
    MIGRATION_TARGETS,
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
    DB_POOL_TIMEOUT,
    DB_POOL_RECYCLE,
    DUCKDB_STORAGE_PATH,
    REUSE_EXISTING_DB,
    CLEANUP_EMPTY_DB,
)

MAX_DB_NAME_LENGTH = 60

try:
    import sqlglot
    from sqlglot import exp
    HAS_SQLGLOT = True
except ImportError:
    HAS_SQLGLOT = False


def _is_engine_enabled(dialect: str) -> bool:
    """Check if an engine is in MIGRATION_TARGETS and has valid config."""
    if dialect not in MIGRATION_TARGETS:
        return False
    conf = DB_CONFIG.get(dialect, {})
    if dialect == "oracle":
        return bool(conf.get("dsn") or conf.get("host"))
    return bool(conf.get("host"))


class DBManager:
    """Manages creation and migration of databases from SQLite to MySQL/Postgres/SQL Server/DuckDB."""

    def __init__(self):
        self._mysql_enabled = _is_engine_enabled("mysql")
        self._postgres_enabled = _is_engine_enabled("postgres")
        self._sqlserver_enabled = _is_engine_enabled("sqlserver")
        self._duckdb_enabled = _is_engine_enabled("duckdb")

        self.mysql_admin_engine = None
        self.pg_admin_engine = None
        self.sqlserver_admin_engine = None

        if self._mysql_enabled:
            self.mysql_admin_engine = self._create_engine("mysql", db_name=None, is_admin=True)
        if self._postgres_enabled:
            self.pg_admin_engine = self._create_engine("postgres", db_name="postgres", isolation_level="AUTOCOMMIT", is_admin=True)
        if self._sqlserver_enabled:
            self.sqlserver_admin_engine = self._create_engine("sqlserver", db_name="master", isolation_level="AUTOCOMMIT", is_admin=True)

        if self._duckdb_enabled:
            if DUCKDB_STORAGE_PATH:
                self.duckdb_temp_dir = DUCKDB_STORAGE_PATH
                os.makedirs(self.duckdb_temp_dir, exist_ok=True)
                self._duckdb_is_temp = False
            else:
                self.duckdb_temp_dir = tempfile.mkdtemp(prefix="duckdb_")
                self._duckdb_is_temp = True
        else:
            self.duckdb_temp_dir = None
            self._duckdb_is_temp = False
        self.active_engines = {}
    
    def _is_db_name_too_long(self, db_id):
        """Check if database name exceeds the maximum allowed length."""
        return len(db_id) > MAX_DB_NAME_LENGTH
        
    def _create_engine(self, dialect, db_name=None, isolation_level=None, is_admin=False):
        conf = DB_CONFIG.get(dialect, {})
        if dialect == 'mysql':
            url = f"mysql+pymysql://{conf['user']}:{conf['password']}@{conf['host']}:{conf['port']}"
            if db_name:
                url += f"/{db_name}?charset=utf8mb4"
        elif dialect == 'postgres':
            url = f"postgresql+psycopg2://{conf['user']}:{conf['password']}@{conf['host']}:{conf['port']}"
            if db_name:
                url += f"/{db_name}"
        elif dialect == 'sqlserver':
            password_encoded = quote_plus(conf['password'])
            driver_encoded = quote_plus(conf['driver'])
            url = f"mssql+pyodbc://{conf['user']}:{password_encoded}@{conf['host']}:{conf['port']}"
            if db_name:
                url += f"/{db_name}?driver={driver_encoded}"
            else:
                url += f"?driver={driver_encoded}"
        else:
            raise ValueError(f"Unsupported dialect for engine creation: {dialect}")
        
        # Admin engines (for CREATE/DROP DB) use minimal pool to prevent connection exhaustion
        # Worker engines use normal pool for query execution
        if is_admin:
            kwargs = {
                'pool_size': 1,
                'max_overflow': 1,
                'pool_timeout': DB_POOL_TIMEOUT,
                'pool_recycle': DB_POOL_RECYCLE,
                'pool_pre_ping': True,
            }
        else:
            kwargs = {
                'pool_size': DB_POOL_SIZE,
                'max_overflow': DB_MAX_OVERFLOW,
                'pool_timeout': DB_POOL_TIMEOUT,
                'pool_recycle': DB_POOL_RECYCLE,
                'pool_pre_ping': True,
            }
        
        if isolation_level:
            kwargs['isolation_level'] = isolation_level
            
        return create_engine(url, **kwargs)

    def find_sqlite_db_path(self, source, db_id):
        """Finds the SQLite database file for a given source and db_id."""
        # Get sqlite_db_dir from DATA_SOURCES
        source_config = DATA_SOURCES.get(source, {})
        sqlite_db_dir = source_config.get('sqlite_db_dir', '')
        
        base_paths = [sqlite_db_dir] if sqlite_db_dir else []
        
        if not base_paths:
             # Fallback: try all available paths from all sources
             for src_config in DATA_SOURCES.values():
                 db_dir = src_config.get('sqlite_db_dir', '')
                 if db_dir:
                     base_paths.append(db_dir)
        
        for base_path in base_paths:
            potential_path = os.path.join(base_path, db_id, f"{db_id}.sqlite")
            if os.path.exists(potential_path):
                return potential_path
            
            # Also try without the inner db_id folder just in case
            potential_path_flat = os.path.join(base_path, f"{db_id}.sqlite")
            if os.path.exists(potential_path_flat):
                return potential_path_flat

        return None

    def _clean_dataframe_for_migration(self, df):
        """
        Clean DataFrame before migration to handle type compatibility issues.
        - Convert empty strings to None (NULL) for numeric columns
        - This prevents errors like "Could not convert string '' to DOUBLE"
        """
        if df.empty:
            return df
        
        # Replace empty strings with None across all columns
        df = df.replace('', None)
        
        # Additional cleaning: strip whitespace from string columns
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
        
        return df

    def _extract_tables_from_sql(self, sql):
        """Extract table names from SQL using sqlglot."""
        if not HAS_SQLGLOT or not sql:
            return set()
        try:
            parsed = sqlglot.parse_one(sql, read='sqlite')
            tables = set()
            for table in parsed.find_all(exp.Table):
                if table.name:
                    tables.add(table.name)
            return tables
        except:
            # Fallback: simple regex extraction
            pattern = r'\bFROM\s+["\[]?([\w]+)["\]]?|\bJOIN\s+["\[]?([\w]+)["\]]?'
            matches = re.findall(pattern, sql, re.IGNORECASE)
            return set(m[0] or m[1] for m in matches if m[0] or m[1])

    def _collect_essential_data(self, sqlite_conn, items, all_tables):
        """
        Collect essential data that SQL queries need.
        Also marks items with empty SQLite results for skipping.
        
        NEW APPROACH: Use rowid tracking to get EXACT rows that each SQL uses.
        For each table, we modify the original SQL to return rowids, then 
        use those rowids to extract the exact rows needed.
        
        Returns: {table_name: DataFrame of essential rows}
        """
        essential_rowids = {t: set() for t in all_tables}  # {table: set of rowids}
        
        for item in items:
            sqlite_sql = item.get('sqlite')
            if not sqlite_sql:
                continue
            # Handle case where sqlite_sql is a dict
            if isinstance(sqlite_sql, dict):
                sqlite_sql = sqlite_sql.get('query') or sqlite_sql.get('sql') or sqlite_sql.get('SQL')
            if not isinstance(sqlite_sql, str) or not sqlite_sql:
                continue
            
            try:
                # Execute SQL to check if it returns results
                cursor = sqlite_conn.cursor()
                cursor.execute(sqlite_sql)
                result = cursor.fetchall()
                
                if not result:
                    # Mark this item for skipping - SQLite returns empty result
                    item['_skip_empty_sqlite'] = True
                    continue
                
                # Get tables involved in this SQL
                involved_tables = self._extract_tables_from_sql(sqlite_sql)
                
                # For each involved table, get the rowids of rows actually used
                for table_name in involved_tables:
                    if table_name not in all_tables:
                        continue
                    
                    try:
                        # Method: Use a subquery to find rowids that satisfy the query conditions
                        # For single table: SELECT rowid FROM table WHERE <conditions>
                        # For multi-table: SELECT DISTINCT t.rowid FROM t JOIN ... WHERE ...
                        
                        if len(involved_tables) == 1:
                            # Single table - extract WHERE clause and get matching rowids
                            where_match = re.search(r'\bWHERE\b(.+?)(?:GROUP|ORDER|LIMIT|HAVING|;|$)', 
                                                   sqlite_sql, re.IGNORECASE | re.DOTALL)
                            if where_match:
                                where_clause = where_match.group(1).strip()
                                where_clause = re.sub(r'\b(GROUP|ORDER|LIMIT|HAVING)\b.*$', '', 
                                                     where_clause, flags=re.IGNORECASE).strip()
                                if where_clause:
                                    rowid_sql = f'SELECT rowid FROM "{table_name}" WHERE {where_clause}'
                                    try:
                                        cursor.execute(rowid_sql)
                                        rowids = [r[0] for r in cursor.fetchall()]
                                        essential_rowids[table_name].update(rowids)
                                        continue
                                    except:
                                        pass
                            
                            # No WHERE clause - get all rowids used (could be SELECT * FROM t)
                            # In this case, we need to get rowids based on what the SQL returns
                            # For aggregate queries like COUNT(*), we need all rows
                            try:
                                rowid_sql = f'SELECT rowid FROM "{table_name}"'
                                cursor.execute(rowid_sql)
                                rowids = [r[0] for r in cursor.fetchall()]
                                essential_rowids[table_name].update(rowids)
                            except:
                                pass
                        else:
                            # Multi-table JOIN query
                            # Try to construct a query that gets rowids from this specific table
                            # by wrapping the original query's logic
                            
                            # Strategy: Replace SELECT clause with SELECT table.rowid
                            # and add DISTINCT to avoid duplicates
                            try:
                                # Find FROM clause position
                                from_match = re.search(r'\bFROM\b', sqlite_sql, re.IGNORECASE)
                                if from_match:
                                    # Build: SELECT DISTINCT "table_name".rowid FROM ... (rest of original SQL)
                                    rest_sql = sqlite_sql[from_match.start():]
                                    rowid_sql = f'SELECT DISTINCT "{table_name}".rowid {rest_sql}'
                                    
                                    # Remove any ORDER BY or LIMIT at the end (we want all matching rows)
                                    rowid_sql = re.sub(r'\bORDER\s+BY\b.+$', '', rowid_sql, flags=re.IGNORECASE)
                                    rowid_sql = re.sub(r'\bLIMIT\b\s+\d+.*$', '', rowid_sql, flags=re.IGNORECASE)
                                    
                                    cursor.execute(rowid_sql)
                                    rowids = [r[0] for r in cursor.fetchall() if r[0] is not None]
                                    essential_rowids[table_name].update(rowids)
                            except Exception as e:
                                logging.debug(f"Failed to get rowids for {table_name} in multi-table query: {e}")
                                # Fallback: if we can't get specific rowids, mark that we need data from this table
                                # We'll handle this in the migration phase by getting more data
                                essential_rowids[table_name].add(-1)  # Special marker
                                
                    except Exception as e:
                        logging.debug(f"Error collecting rowids for {table_name}: {e}")
                        
            except Exception as e:
                # SQL execution failed - mark for skip
                item['_skip_empty_sqlite'] = True
        
        # Now fetch actual data using the collected rowids
        result = {}
        for table_name in all_tables:
            rowids = essential_rowids.get(table_name, set())
            
            if not rowids:
                result[table_name] = pd.DataFrame()
                continue
            
            try:
                if -1 in rowids:
                    # Special marker: we couldn't get specific rowids, get reasonable amount of data
                    rowids.discard(-1)
                    if rowids:
                        # We have some rowids plus fallback marker - get those rowids + extra
                        rowid_list = list(rowids)[:5000]  # Limit to prevent huge queries
                        placeholders = ','.join(['?' for _ in rowid_list])
                        df1 = pd.read_sql_query(
                            f'SELECT * FROM "{table_name}" WHERE rowid IN ({placeholders})',
                            sqlite_conn, params=rowid_list
                        )
                        # Also get some extra data as fallback
                        df2 = pd.read_sql_query(
                            f'SELECT * FROM "{table_name}" LIMIT 500',
                            sqlite_conn
                        )
                        result[table_name] = pd.concat([df1, df2], ignore_index=True).drop_duplicates()
                    else:
                        # Only fallback marker - get reasonable amount
                        result[table_name] = pd.read_sql_query(
                            f'SELECT * FROM "{table_name}" LIMIT 1000',
                            sqlite_conn
                        )
                else:
                    # We have specific rowids - get exactly those rows
                    rowid_list = list(rowids)[:10000]  # Safety limit
                    if len(rowid_list) > 0:
                        # Batch fetch to avoid too-long SQL
                        dfs = []
                        batch_size = 500
                        for i in range(0, len(rowid_list), batch_size):
                            batch = rowid_list[i:i+batch_size]
                            placeholders = ','.join(['?' for _ in batch])
                            df = pd.read_sql_query(
                                f'SELECT * FROM "{table_name}" WHERE rowid IN ({placeholders})',
                                sqlite_conn, params=batch
                            )
                            dfs.append(df)
                        result[table_name] = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
                    else:
                        result[table_name] = pd.DataFrame()
            except Exception as e:
                logging.debug(f"Error fetching data for {table_name}: {e}")
                result[table_name] = pd.DataFrame()
        
        return result

    def _check_table_has_data(self, engine, table_name, dialect):
        """Check if a table exists and has data in the target database."""
        try:
            if dialect == 'duckdb':
                result = engine.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()
                return result[0] > 0
            else:
                with engine.connect() as conn:
                    result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                    return result.fetchone()[0] > 0
        except:
            return False

    def _supplement_essential_data(self, sqlite_path, engines, items, duckdb_conn):
        """
        When reusing a database, check if essential data for items exists.
        Strategy:
        1. Collect essential rowids needed by current items
        2. Check if target tables have data
        3. If table is empty or doesn't exist, migrate the essential data
        """
        with sqlite3.connect(sqlite_path) as sqlite_conn:
            cursor = sqlite_conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            all_tables = [t[0] for t in cursor.fetchall() if not t[0].startswith('sqlite_')]
            
            # Collect essential data needed by items
            essential_data = self._collect_essential_data(sqlite_conn, items, all_tables)
            
            for table_name, df_essential in essential_data.items():
                if df_essential.empty:
                    continue
                df_essential = self._clean_dataframe_for_migration(df_essential)

                if "mysql" in engines and not self._check_table_has_data(engines["mysql"], table_name, "mysql"):
                    try:
                        df_essential.to_sql(table_name, engines["mysql"], if_exists="replace", index=False)
                        logging.debug(f"Supplemented {table_name} to MySQL ({len(df_essential)} rows)")
                    except Exception as e:
                        logging.debug(f"Could not supplement {table_name} to MySQL: {e}")
                if "postgres" in engines and not self._check_table_has_data(engines["postgres"], table_name, "postgres"):
                    try:
                        df_essential.to_sql(table_name, engines["postgres"], if_exists="replace", index=False)
                        logging.debug(f"Supplemented {table_name} to Postgres ({len(df_essential)} rows)")
                    except Exception as e:
                        logging.debug(f"Could not supplement {table_name} to Postgres: {e}")
                if "sqlserver" in engines and not self._check_table_has_data(engines["sqlserver"], table_name, "sqlserver"):
                    try:
                        df_essential.to_sql(table_name, engines["sqlserver"], if_exists="replace", index=False)
                        logging.debug(f"Supplemented {table_name} to SQL Server ({len(df_essential)} rows)")
                    except Exception as e:
                        logging.debug(f"Could not supplement {table_name} to SQL Server: {e}")
                if duckdb_conn and not self._check_table_has_data(duckdb_conn, table_name, "duckdb"):
                    try:
                        duckdb_conn.register("temp_supplement_df", df_essential)
                        duckdb_conn.execute(f'CREATE OR REPLACE TABLE "{table_name}" AS SELECT * FROM temp_supplement_df')
                        duckdb_conn.unregister("temp_supplement_df")
                        logging.debug(f"Supplemented {table_name} to DuckDB ({len(df_essential)} rows)")
                    except Exception as e:
                        logging.debug(f"Could not supplement {table_name} to DuckDB: {e}")
            
            for table_name in all_tables:
                if table_name not in essential_data or essential_data[table_name].empty:
                    df_sample = pd.read_sql_query(
                        f'SELECT * FROM "{table_name}" LIMIT {MIGRATION_ROW_LIMIT}', sqlite_conn
                    )
                    if not df_sample.empty:
                        df_sample = self._clean_dataframe_for_migration(df_sample)
                        if "mysql" in engines and not self._check_table_has_data(engines["mysql"], table_name, "mysql"):
                            try:
                                df_sample.to_sql(table_name, engines["mysql"], if_exists="replace", index=False)
                            except Exception:
                                pass
                        if "postgres" in engines and not self._check_table_has_data(engines["postgres"], table_name, "postgres"):
                            try:
                                df_sample.to_sql(table_name, engines["postgres"], if_exists="replace", index=False)
                            except Exception:
                                pass
                        if "sqlserver" in engines and not self._check_table_has_data(engines["sqlserver"], table_name, "sqlserver"):
                            try:
                                df_sample.to_sql(table_name, engines["sqlserver"], if_exists="replace", index=False)
                            except Exception:
                                pass
                        if duckdb_conn and not self._check_table_has_data(duckdb_conn, table_name, "duckdb"):
                            try:
                                duckdb_conn.register("temp_sample_df", df_sample)
                                duckdb_conn.execute(f'CREATE OR REPLACE TABLE "{table_name}" AS SELECT * FROM temp_sample_df')
                                duckdb_conn.unregister("temp_sample_df")
                            except Exception:
                                pass

    def _check_db_exists(self, db_id):
        """Check if database exists in all enabled target systems."""
        try:
            if self._mysql_enabled and self.mysql_admin_engine:
                with self.mysql_admin_engine.connect() as conn:
                    result = conn.execute(text(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{db_id}'"))
                    if not result.fetchone():
                        return False
            if self._postgres_enabled and self.pg_admin_engine:
                with self.pg_admin_engine.connect() as conn:
                    result = conn.execute(text(f"SELECT datname FROM pg_database WHERE datname = '{db_id}'"))
                    if not result.fetchone():
                        return False
            if self._sqlserver_enabled and self.sqlserver_admin_engine:
                with self.sqlserver_admin_engine.connect() as conn:
                    result = conn.execute(text(f"SELECT name FROM sys.databases WHERE name = '{db_id}'"))
                    if not result.fetchone():
                        return False
            if self._duckdb_enabled and self.duckdb_temp_dir:
                duckdb_path = os.path.join(self.duckdb_temp_dir, f"{db_id}.duckdb")
                if not os.path.exists(duckdb_path):
                    return False
            return True
        except Exception as e:
            logging.debug(f"Error checking if {db_id} exists: {e}")
            return False

    def setup_and_migrate(self, db_id, sqlite_path, items=None):
        """
        Creates MySQL/PG/SQLServer databases and DuckDB, migrates data from SQLite.
        
        If REUSE_EXISTING_DB is True and database exists, skip creation and migration.
        If items are provided, uses smart migration:
        1. First, extract data that the SQLs actually need (essential data)
        2. Then, supplement with additional data up to MIGRATION_ROW_LIMIT
        
        Returns None if db_id is too long (skip this database).
        """
        # Skip if database name is too long
        if self._is_db_name_too_long(db_id):
            logging.warning(f"Skipping database '{db_id[:50]}...' - name too long ({len(db_id)} > {MAX_DB_NAME_LENGTH})")
            return None
        
        # Check if we should reuse existing database
        reusing = False
        if REUSE_EXISTING_DB and self._check_db_exists(db_id):
            logging.info(f"Reusing existing database: {db_id}")
            reusing = True
            try:
                engines = {"sqlite": create_engine(f"sqlite:///{sqlite_path}")}
                duckdb_conn = None
                if self._mysql_enabled:
                    engines["mysql"] = self._create_engine("mysql", db_id)
                if self._postgres_enabled:
                    engines["postgres"] = self._create_engine("postgres", db_id)
                if self._sqlserver_enabled:
                    engines["sqlserver"] = self._create_engine("sqlserver", db_id)
                if self._duckdb_enabled and self.duckdb_temp_dir:
                    duckdb_path = os.path.join(self.duckdb_temp_dir, f"{db_id}.duckdb")
                    duckdb_conn = duckdb.connect(duckdb_path)
                    engines["duckdb"] = duckdb_conn

                if items:
                    self._supplement_essential_data(sqlite_path, engines, items, duckdb_conn)
                
                self.active_engines[db_id] = engines
                return engines
            except Exception as e:
                logging.warning(f"Failed to reuse {db_id}, will recreate: {e}")
                reusing = False
                # Fall through to create new database
        
        self.teardown_database(db_id)

        try:
            if self._mysql_enabled and self.mysql_admin_engine:
                with self.mysql_admin_engine.connect() as conn:
                    conn.execute(text(f"CREATE DATABASE `{db_id}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            if self._postgres_enabled and self.pg_admin_engine:
                with self.pg_admin_engine.connect() as conn:
                    conn.execute(text(f'CREATE DATABASE "{db_id}"'))
            if self._sqlserver_enabled and self.sqlserver_admin_engine:
                with self.sqlserver_admin_engine.connect() as conn:
                    conn.execute(text(f"CREATE DATABASE [{db_id}]"))

            engines = {"sqlite": create_engine(f"sqlite:///{sqlite_path}")}
            duckdb_conn = None
            if self._mysql_enabled:
                engines["mysql"] = self._create_engine("mysql", db_id)
            if self._postgres_enabled:
                engines["postgres"] = self._create_engine("postgres", db_id)
            if self._sqlserver_enabled:
                engines["sqlserver"] = self._create_engine("sqlserver", db_id)
            if self._duckdb_enabled and self.duckdb_temp_dir:
                duckdb_path = os.path.join(self.duckdb_temp_dir, f"{db_id}.duckdb")
                duckdb_conn = duckdb.connect(duckdb_path)
                engines["duckdb"] = duckdb_conn
            
            # 3. Migrate Data (Smart Migration)
            with sqlite3.connect(sqlite_path) as sqlite_conn:
                cursor = sqlite_conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                all_tables = [t[0] for t in cursor.fetchall() if not t[0].startswith('sqlite_')]
                
                # Collect essential data if items provided
                essential_data = {}
                if items:
                    essential_data = self._collect_essential_data(sqlite_conn, items, all_tables)
                
                for table_name in all_tables:
                    # Start with essential data (if any)
                    if table_name in essential_data and not essential_data[table_name].empty:
                        df_essential = essential_data[table_name]
                        essential_count = len(df_essential)
                        
                        # Get rowids/primary key to exclude from supplement
                        # Since we don't know PK, we use hash of all columns
                        df_essential['_row_hash'] = df_essential.apply(
                            lambda row: hash(tuple(row)), axis=1
                        )
                        essential_hashes = set(df_essential['_row_hash'].tolist())
                        df_essential = df_essential.drop(columns=['_row_hash'])
                        
                        # Supplement with MIGRATION_ROW_LIMIT additional random rows (not duplicates)
                        # Get more data, excluding what we already have
                        df_all = pd.read_sql_query(
                            f'SELECT * FROM "{table_name}" LIMIT {MIGRATION_ROW_LIMIT + essential_count + 100}', 
                            sqlite_conn
                        )
                        df_all['_row_hash'] = df_all.apply(
                            lambda row: hash(tuple(row)), axis=1
                        )
                        df_supplement = df_all[~df_all['_row_hash'].isin(essential_hashes)]
                        df_supplement = df_supplement.drop(columns=['_row_hash']).head(MIGRATION_ROW_LIMIT)
                        
                        # Combine essential + supplement
                        df = pd.concat([df_essential, df_supplement], ignore_index=True)
                    else:
                        # No essential data, use regular migration
                        df = pd.read_sql_query(
                            f'SELECT * FROM "{table_name}" LIMIT {MIGRATION_ROW_LIMIT}', 
                            sqlite_conn
                        )
                    
                    if df.empty:
                        continue
                    
                    # Clean data before migration (handle empty strings, etc.)
                    df = self._clean_dataframe_for_migration(df)
                    
                    if "mysql" in engines:
                        try:
                            df.to_sql(table_name, engines["mysql"], if_exists="replace", index=False)
                        except Exception as e:
                            logging.warning(f"Failed to migrate {table_name} to MySQL: {e}")
                    if "postgres" in engines:
                        try:
                            df.to_sql(table_name, engines["postgres"], if_exists="replace", index=False)
                        except Exception as e:
                            logging.warning(f"Failed to migrate {table_name} to Postgres: {e}")
                    if "sqlserver" in engines:
                        try:
                            df.to_sql(table_name, engines["sqlserver"], if_exists="replace", index=False)
                        except Exception as e:
                            logging.warning(f"Failed to migrate {table_name} to SQL Server: {e}")
                    if duckdb_conn:
                        try:
                            duckdb_conn.register("temp_df", df)
                            duckdb_conn.execute(f'CREATE OR REPLACE TABLE "{table_name}" AS SELECT * FROM temp_df')
                            duckdb_conn.unregister("temp_df")
                        except Exception as e:
                            logging.warning(f"Failed to migrate {table_name} to DuckDB: {e}")
            
            self.active_engines[db_id] = engines
            return engines
            
        except Exception as e:
            logging.error(f"Failed to setup database {db_id}: {e}")
            self.teardown_database(db_id)
            return None

    def teardown_database(self, db_id):
        """Drops the temporary databases."""
        # Dispose active engines first
        if db_id in self.active_engines:
            for key, engine in self.active_engines[db_id].items():
                if key == 'duckdb':
                    try:
                        engine.close()  # DuckDB connection
                    except Exception:
                        pass
                else:
                    engine.dispose()
            del self.active_engines[db_id]

        if self._mysql_enabled and self.mysql_admin_engine:
            try:
                with self.mysql_admin_engine.connect() as conn:
                    conn.execute(text(f"DROP DATABASE IF EXISTS `{db_id}`"))
            except Exception as e:
                logging.warning(f"Error dropping MySQL DB {db_id}: {e}")

        if self._postgres_enabled and self.pg_admin_engine:
            try:
                with self.pg_admin_engine.connect() as conn:
                    terminate_sql = f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{db_id}' AND pid <> pg_backend_pid();
                    """
                    try:
                        conn.execute(text(terminate_sql))
                    except Exception:
                        pass
                    conn.execute(text(f'DROP DATABASE IF EXISTS "{db_id}"'))
            except Exception as e:
                logging.warning(f"Error dropping Postgres DB {db_id}: {e}")

        if self._sqlserver_enabled and self.sqlserver_admin_engine:
            try:
                with self.sqlserver_admin_engine.connect() as conn:
                    conn.execute(text(f"""
                        IF EXISTS (SELECT name FROM sys.databases WHERE name = '{db_id}')
                        BEGIN
                            ALTER DATABASE [{db_id}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
                            DROP DATABASE [{db_id}];
                        END
                    """))
            except Exception as e:
                logging.warning(f"Error dropping SQL Server DB {db_id}: {e}")

        if self._duckdb_enabled and self.duckdb_temp_dir:
            try:
                duckdb_path = os.path.join(self.duckdb_temp_dir, f"{db_id}.duckdb")
                if os.path.exists(duckdb_path):
                    os.remove(duckdb_path)
                wal_path = duckdb_path + ".wal"
                if os.path.exists(wal_path):
                    os.remove(wal_path)
            except Exception as e:
                logging.warning(f"Error removing DuckDB file {db_id}: {e}")

    def dispose(self):
        """Clean up admin engines and temp directory."""
        if self.mysql_admin_engine:
            self.mysql_admin_engine.dispose()
        if self.pg_admin_engine:
            self.pg_admin_engine.dispose()
        if self.sqlserver_admin_engine:
            self.sqlserver_admin_engine.dispose()
        if self._duckdb_is_temp and self.duckdb_temp_dir and os.path.exists(self.duckdb_temp_dir):
            try:
                import shutil
                shutil.rmtree(self.duckdb_temp_dir, ignore_errors=True)
            except Exception:
                pass
