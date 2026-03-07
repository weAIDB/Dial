# dataset/run_migration.py
# Entry point for SQLite -> MySQL/Postgres/SQL Server/DuckDB migration.
# Run from project root: python -m dataset.run_migration
# Or from dataset dir: python run_migration.py
#
# Prerequisites:
#   1. Extract duckdb_sqlite_databases.zip
#   2. Set SQLITE_BASE_DIR (or sqlite_db_dir per source) in config
#   3. Set DB_CONFIG for target engines (MySQL, Postgres, SQL Server)
#   4. Optionally add json_files to DATA_SOURCES for smart migration

import os
import sys
import json
import logging
from pathlib import Path
from collections import defaultdict

_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from config import DATA_SOURCES, SQLITE_BASE_DIR, OUTPUT_DIR, CHECKPOINT_INTERVAL, FINAL_OUTPUT_PATH
from db_manager import DBManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("run_migration")


def _apply_field_mapping(item: dict, field_mapping: dict) -> dict:
    """Apply field_mapping to item. Supports nested gold_sql -> sqlite extraction."""
    out = {}
    for src_key, target_key in field_mapping.items():
        val = item.get(src_key)
        if val is not None and isinstance(val, dict) and "sqlite" in val:
            val = val["sqlite"]
        if val is None and "gold_sql" in item:
            gs = item["gold_sql"]
            if isinstance(gs, dict) and "sqlite" in gs:
                val = gs["sqlite"]
        if val is not None:
            out[target_key] = val
    for k, v in item.items():
        if k not in field_mapping and k not in ("gold_sql",):
            out[k] = v
    return out


def _load_items_from_json(json_path: str, field_mapping: dict) -> list:
    """Load items from JSON file and apply field_mapping."""
    path = Path(json_path)
    if not path.exists():
        logger.warning("JSON file not found: %s", json_path)
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error("Failed to load %s: %s", json_path, e)
        return []
    if isinstance(data, dict):
        if "data" in data:
            data = data["data"]
        elif "items" in data:
            data = data["items"]
        else:
            data = list(data.values()) if data else []
    if not isinstance(data, list):
        data = [data]
    return [_apply_field_mapping(it, field_mapping) for it in data]


def _collect_db_items_from_sources() -> dict:
    """Collect {db_id: [items]} from all DATA_SOURCES json_files."""
    db_to_items = defaultdict(list)
    for source_name, source_config in DATA_SOURCES.items():
        json_files = source_config.get("json_files", [])
        field_mapping = source_config.get("field_mapping", {})
        if not field_mapping:
            field_mapping = {"db_id": "db_id", "question": "question", "query": "sqlite"}
        for jf in json_files:
            if not jf or not str(jf).strip():
                continue
            items = _load_items_from_json(jf, field_mapping)
            for it in items:
                db_id = it.get("db_id")
                if db_id:
                    db_to_items[db_id].append(it)
    return dict(db_to_items)


def _discover_db_ids_from_sqlite_dir(sqlite_db_dir: str) -> list:
    """Discover db_ids from directory structure: {dir}/{db_id}/{db_id}.sqlite or {dir}/{db_id}.sqlite."""
    base = Path(sqlite_db_dir)
    if not base.exists():
        return []
    ids = set()
    for p in base.iterdir():
        if p.is_dir():
            if (p / f"{p.name}.sqlite").exists():
                ids.add(p.name)
        elif p.suffix == ".sqlite":
            ids.add(p.stem)
    return sorted(ids)


def _find_sqlite_path(db_id: str, sqlite_db_dir: str) -> str | None:
    """Find SQLite file path for db_id."""
    base = Path(sqlite_db_dir)
    cand1 = base / db_id / f"{db_id}.sqlite"
    cand2 = base / f"{db_id}.sqlite"
    if cand1.exists():
        return str(cand1)
    if cand2.exists():
        return str(cand2)
    return None


def main():
    logger.info("=== Dataset Migration (SQLite -> MySQL/Postgres/SQL Server/DuckDB) ===")

    db_manager = DBManager()
    db_to_items = _collect_db_items_from_sources()

    # Determine sqlite base dir from first non-empty source
    sqlite_base = SQLITE_BASE_DIR
    if not sqlite_base:
        for src_config in DATA_SOURCES.values():
            d = src_config.get("sqlite_db_dir", "")
            if d and Path(d).exists():
                sqlite_base = d
                break

    if not sqlite_base or not Path(sqlite_base).exists():
        logger.error(
            "SQLITE_BASE_DIR or sqlite_db_dir not set or invalid. "
            "Set SQLITE_BASE_DIR in config or sqlite_db_dir in DATA_SOURCES."
        )
        return

    # If no items from JSON, discover db_ids from directory
    if not db_to_items:
        db_ids = _discover_db_ids_from_sqlite_dir(sqlite_base)
        db_to_items = {db_id: [] for db_id in db_ids}
        logger.info("Discovered %d databases from %s", len(db_ids), sqlite_base)

    if not db_to_items:
        logger.warning("No databases to migrate. Add json_files to DATA_SOURCES or ensure sqlite_db_dir has .sqlite files.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    migrated = []
    failed = []

    for i, (db_id, items) in enumerate(db_to_items.items(), 1):
        sqlite_path = _find_sqlite_path(db_id, sqlite_base)
        if not sqlite_path:
            for src_config in DATA_SOURCES.values():
                d = src_config.get("sqlite_db_dir", "")
                if d:
                    sqlite_path = _find_sqlite_path(db_id, d)
                    if sqlite_path:
                        break
        if not sqlite_path:
            logger.warning("No SQLite file for db_id=%s, skipping", db_id)
            failed.append(db_id)
            continue

        logger.info("[%d/%d] Migrating %s (items=%d)", i, len(db_to_items), db_id, len(items))
        try:
            engines = db_manager.setup_and_migrate(db_id, sqlite_path, items=items if items else None)
            if engines:
                migrated.append(db_id)
        except Exception as e:
            logger.error("Migration failed for %s: %s", db_id, e)
            failed.append(db_id)

        if CHECKPOINT_INTERVAL and i % CHECKPOINT_INTERVAL == 0:
            cp_path = Path(OUTPUT_DIR) / f"checkpoint_migrated_{i}.json"
            with open(cp_path, "w", encoding="utf-8") as f:
                json.dump({"migrated": migrated, "failed": failed}, f, indent=2)
            logger.info("Checkpoint saved: %s", cp_path)

    db_manager.dispose()

    out_path = FINAL_OUTPUT_PATH or str(Path(OUTPUT_DIR) / "final_benchmark.json")
    result = {"migrated": migrated, "failed": failed, "total": len(migrated) + len(failed)}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    logger.info("Done. Migrated=%d, Failed=%d. Report: %s", len(migrated), len(failed), out_path)


if __name__ == "__main__":
    main()
