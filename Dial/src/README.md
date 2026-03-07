# Dial Source Modules

Source code for the Dial pipeline: NL-LQP generation, tagging, RAG retrieval, and translation.

## Subpackages

- **nl_lqp/**  
  - `generate_nl_lqp.py`: Generate dialect-agnostic NL-LQP from questions and schema.  
  - `tag_dialect_aware_lqp.py`: Tag dialect-sensitive operators and map to functional categories.

- **knowledge/**  
  - `rag_retriever.py`: RAG retrieval over dialect knowledge.  
  - `runner.py`: Batch run over tagged LQP; outputs per-dialect files.  
  - `knowledge/`: Rule-based and functional dialect text (MySQL, Postgres, SQL Server, etc.).

- **schema/**  
  - `ddl_fetcher.py`: Fetch DDL / schema for databases.

- **translation/**  
  - `main.py`: Translation entry (rag2sql), execution check, semantic validation.  
  - `rag_retrieval.py`, `prompt_builder.py`, `result_saver.py`, `db_operations.py`, etc.

All paths and DB/API settings are read from `Dial/conf/settings.py`.
