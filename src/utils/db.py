"""DuckDB database helpers."""
from __future__ import annotations

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]  # src/utils/ -> project root


def connect(db_path: str | Path | None = None, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    if db_path is None:
        db_path = ROOT / "database" / "albion_analytics.duckdb"
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path), read_only=read_only)


def execute_sql_file(con: duckdb.DuckDBPyConnection, sql_path: str | Path) -> None:
    sql_path = Path(sql_path)
    sql = sql_path.read_text(encoding="utf-8")
    # DuckDB execute can run multiple statements separated by semicolons.
    con.execute(sql)
