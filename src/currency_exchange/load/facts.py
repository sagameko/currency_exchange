"""Load the fct_daily_rate fact table."""

import json
import logging
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import duckdb

from currency_exchange.load.dimensions import date_key

logger = logging.getLogger(__name__)


def read_clean(path: Path) -> list[dict]:
    """Read clean JSON Lines and turn text back into real types (date, Decimal)."""
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                rows.append(
                    {
                        "date": date.fromisoformat(r["date"]),
                        "currency_code": r["currency_code"],
                        "foreign_per_aud": Decimal(
                            r["foreign_per_aud"]
                        ),  # "0.66834" -> Decimal
                    }
                )
    return rows


def load_fct_daily_rate(
    con: duckdb.DuckDBPyConnection, rows: list[dict], start: date, end: date
) -> int:
    """Replace every fact row in the date range with the new rows (idempotent)."""
    loaded_at = datetime.now(UTC).replace(tzinfo=None)  # stored as UTC
    fact_rows = [
        [date_key(r["date"]), r["currency_code"], r["foreign_per_aud"], loaded_at]
        for r in rows
    ]

    deleted = con.execute(
        "DELETE FROM fct_daily_rate WHERE date_key BETWEEN ? AND ?",
        [date_key(start), date_key(end)],
    ).fetchone()[0]
    if fact_rows:
        con.executemany(
            "INSERT INTO fct_daily_rate (date_key, currency_code, foreign_per_aud, loaded_at) "
            "VALUES (?, ?, ?, ?)",
            fact_rows,
        )
    logger.info(
        "fct_daily_rate: replaced %d old rows with %d new rows for %s to %s",
        deleted,
        len(fact_rows),
        start,
        end,
    )
    return len(fact_rows)
