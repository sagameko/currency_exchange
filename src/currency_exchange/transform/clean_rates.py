"""Transform raw Frankfurter JSON into clean rows: one row per currency per published day."""

import json
import logging
from datetime import date
from decimal import Decimal
from pathlib import Path

from currency_exchange.config import Settings
from currency_exchange.extract.frankfurter import raw_path

logger = logging.getLogger(__name__)


class DataQualityError(Exception):
    """Raised when too many rows fail the quality checks."""


def read_raw(path: Path) -> dict:
    """Read a raw file, turning every decimal number into Decimal (never float)."""
    with open(path, encoding="utf-8") as f:
        return json.load(f, parse_float=Decimal)


def to_rows(record: dict) -> list[dict]:
    """Flatten {"rates": {date: {currency: rate}}} into one dict per (date, currency)."""
    rows = []
    for day, day_rates in record["payload"].get("rates", {}).items():  # level 1: dates
        for currency, rate in day_rates.items():  # level 2: currencies
            rows.append(
                {"date": day, "currency_code": currency, "foreign_per_aud": rate}
            )
    return rows


def keep_requested_range(rows: list[dict], start: date, end: date) -> list[dict]:
    """Drop rows the API sent from outside the range we asked for (e.g. 31/12 for a 1/1 start)."""
    kept = [r for r in rows if start <= date.fromisoformat(r["date"]) <= end]
    dropped = len(rows) - len(kept)
    if dropped:
        logger.info(
            "Dropped %d rows outside the requested range %s to %s", dropped, start, end
        )
    return kept


def validate_row(row: dict, currencies: set[str]) -> list[str]:
    """Return a list of problems with this row. An empty list means the row is valid."""
    errors = []
    try:
        date.fromisoformat(row["date"])
    except (TypeError, ValueError):
        errors.append(f"invalid date {row['date']!r}")
    if row["currency_code"] not in currencies:
        errors.append(f"unexpected currency {row['currency_code']!r}")
    rate = row["foreign_per_aud"]
    if not isinstance(rate, Decimal | int) or rate <= 0:
        errors.append(f"rate must be a positive number, got {rate!r}")
    return errors


def clean_rows(
    rows: list[dict], currencies: set[str], max_bad_ratio: float
) -> list[dict]:
    """Keep valid, unique rows; stop the pipeline if too many rows are bad."""
    clean, bad, seen = [], 0, set()
    for row in rows:
        errors = validate_row(row, currencies)
        key = (row["date"], row["currency_code"])
        if key in seen:
            errors.append("duplicate date and currency")
        if errors:
            bad += 1
            logger.debug("Dropping %s: %s", key, "; ".join(errors))
            continue
        seen.add(key)
        clean.append(row)

    total = len(rows)
    if total and bad / total > max_bad_ratio:
        raise DataQualityError(
            f"{bad} of {total} rows failed checks, limit is {max_bad_ratio:.0%}"
        )
    if bad:
        logger.warning("Dropped %d of %d rows that failed checks", bad, total)
    return clean


def clean_path(settings: Settings, start: date, end: date) -> Path:
    """Same date range -> same file, so re-running overwrites."""
    return settings.clean_dir / "daily_rates" / f"{start}_{end}.jsonl"


def save_clean(rows: list[dict], path: Path) -> None:
    """Write JSON Lines. Decimals are written as strings so no precision is lost."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(row, default=str) + "\n" for row in rows)
    tmp_path.replace(path)


def transform(settings: Settings, start: date, end: date) -> Path:
    """Read the raw file for a date range, clean it, and save the clean rows."""
    record = read_raw(raw_path(settings, start, end))
    rows = keep_requested_range(to_rows(record), start, end)
    clean = clean_rows(rows, set(settings.currencies), settings.max_bad_ratio)

    out = clean_path(settings, start, end)
    save_clean(clean, out)
    days = len({r["date"] for r in clean})
    logger.info("Saved %d clean rows (%d days) to %s", len(clean), days, out)
    return out
