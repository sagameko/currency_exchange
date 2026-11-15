import logging
from datetime import date, timedelta

import duckdb

logger = logging.getLogger(__name__)


def date_key(d: date) -> int:
    """2026-01-02 -> 20260102"""
    return int(d.strftime("%Y%m%d"))


def load_dim_currency(
    con: duckdb.DuckDBPyConnection, currencies: list[str], names: dict[str, str]
) -> int:
    """Upsert the configured currencies with their full names."""
    rows = [[code, names.get(code, code)] for code in currencies]
    con.executemany(
        """
        INSERT INTO dim_currency (currency_code, currency_name) VALUES (?, ?)
        ON CONFLICT (currency_code) DO UPDATE SET currency_name = excluded.currency_name
        """,
        rows,
    )
    logger.info("dim_currency: %d currencies upserted", len(rows))
    return len(rows)


def load_dim_date(
    con: duckdb.DuckDBPyConnection, start: date, end: date, published_dates: set[date]
) -> int:
    """One row per calendar day, including weekends; is_published comes from the data."""
    rows = []
    day = start
    while day <= end:
        rows.append(
            [
                date_key(day),
                day,
                day.day,
                day.month,
                day.strftime("%B"),  # 'January'
                (day.month - 1) // 3 + 1,  # quarter 1-4
                day.year,
                day.strftime("%A"),  # 'Friday'
                day.weekday() >= 5,  # Saturday or Sunday
                day in published_dates,  # did the ECB publish rates on this day?
            ]
        )
        day += timedelta(days=1)

    con.executemany(
        """
        INSERT INTO dim_date (date_key, full_date, day, month, month_name, quarter, year,
                              day_of_week, is_weekend, is_published)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (date_key) DO UPDATE SET is_published = excluded.is_published
        """,
        rows,
    )
    logger.info(
        "dim_date: %d days from %s to %s (%d published)",
        len(rows),
        start,
        end,
        len(published_dates),
    )
    return len(rows)
