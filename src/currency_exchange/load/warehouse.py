import logging
from pathlib import Path

import duckdb

from currency_exchange.config import PROJECT_ROOT

logger = logging.getLogger(__name__)
DDL_FILE = PROJECT_ROOT / "sql" / "ddl" / "create_table.sql"


def connect(db_path: Path) -> duckdb.DuckDBPyConnection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def create_tables(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(DDL_FILE.read_text(encoding="utf-8"))
