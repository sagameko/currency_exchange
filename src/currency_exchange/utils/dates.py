"""Date helpers."""

from datetime import date, timedelta


def choose_date_range(
    watermark: date | None, today: date, initial_start: date, lookback_days: int
) -> tuple[date, date]:
    """Decide which dates to load.

    - First run (no watermark): load all history from initial_start.
    - Later runs: start lookback_days before the watermark, to catch late corrections.
    - Never start before initial_start.
    """
    if watermark is None:
        start = initial_start
    else:
        start = max(watermark - timedelta(days=lookback_days), initial_start)
    return start, today
