import logging
from datetime import date
from pathlib import Path

import duckdb

from currency_exchange.config import PROJECT_ROOT, Settings
from currency_exchange.load.dimensions import load_dim_currency, load_dim_date
from currency_exchange.load.facts import load_fct_daily_rate, read_clean
from currency_exchange.load.state import get_watermark, set_watermark
from currency_exchange.transform.clean_rates import clean_path

logger = logging.getLogger(__name__)
DDL_FILE = PROJECT_ROOT / "sql" / "ddl" / "create_table.sql"


def connect(db_path: Path) -> duckdb.DuckDBPyConnection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def create_tables(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(DDL_FILE.read_text(encoding="utf-8"))


def load_all(
    settings: Settings, start: date, end: date, currency_names: dict[str, str]
) -> int:
    """Load dimensions, facts and the watermark in ONE transaction: all or nothing."""
    rows = read_clean(clean_path(settings, start, end))
    published = {r["date"] for r in rows}

    con = connect(settings.database)
    try:
        create_tables(con)
        con.execute("BEGIN TRANSACTION")
        try:
            load_dim_currency(con, settings.currencies, currency_names)
            load_dim_date(con, start, end, published)
            count = load_fct_daily_rate(con, rows, start, end)

            if published:  # only move forward if we loaded data
                old = get_watermark(con)
                latest = max(published)
                new = latest if old is None else max(old, latest)
                set_watermark(con, new)
                logger.info("Watermark moved to %s", new)

            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")  # undo dims, facts AND watermark
            raise
        return count
    finally:
        con.close()
