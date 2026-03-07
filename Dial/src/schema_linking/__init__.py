# src/schema_linking/__init__.py
# Step 0: Schema linking — when true_tables_columns is missing, use LLM to select relevant tables.columns from full DB schema.

from .schema_linking import main_async

__all__ = ["main_async"]
