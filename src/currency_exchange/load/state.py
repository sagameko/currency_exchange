"""Read and write the pipeline watermark (the last date loaded successfully)."""

from datetime import date

import duckdb

PIPELINE_NAME = "fx_daily_rates"


def get_watermark(
    con: duckdb.DuckDBPyConnection, pipeline_name: str = PIPELINE_NAME
) -> date | None:
    """Return the last loaded date, or None if the pipeline has never run."""
    row = con.execute(
        "SELECT last_loaded_date FROM etl_state WHERE pipeline_name = ?",
        [pipeline_name],
    ).fetchone()
    return row[0] if row else None


def set_watermark(
    con: duckdb.DuckDBPyConnection,
    last_loaded_date: date,
    pipeline_name: str = PIPELINE_NAME,
) -> None:
    """Insert or update the watermark. Does NOT commit: the caller decides when."""
    con.execute(
        """
        INSERT INTO etl_state (pipeline_name, last_loaded_date, updated_at)
        VALUES (?, ?, now())
        ON CONFLICT (pipeline_name) DO UPDATE SET
            last_loaded_date = excluded.last_loaded_date,
            updated_at = excluded.updated_at
        """,
        [pipeline_name, last_loaded_date],
    )
