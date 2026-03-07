# Root launcher for dataset migration (SQLite -> MySQL/Postgres/SQL Server/DuckDB).
# Usage: python run_migration.py

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

from dataset.run_migration import main

if __name__ == "__main__":
    main()
