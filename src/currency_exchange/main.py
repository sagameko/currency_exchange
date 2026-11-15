import logging
import sys
from datetime import date

from currency_exchange.config import load_settings
from currency_exchange.extract.frankfurter import extract
from currency_exchange.load.state import get_watermark
from currency_exchange.load.warehouse import connect, create_tables
from currency_exchange.logging_setup import setup_logging
from currency_exchange.transform.clean_rates import transform
from currency_exchange.utils.dates import choose_date_range

logger = logging.getLogger(__name__)


def main():
    settings = load_settings()
    setup_logging(settings.log_dir)

    con = connect(settings.database)
    try:
        create_tables(con)
        watermark = get_watermark(con)
    finally:
        con.close()

    start, end = choose_date_range(
        watermark, date.today(), settings.initial_start_date, settings.lookback_days
    )
    if watermark is None:
        logger.info(
            "First run: no watermark yet, loading history from %s to %s", start, end
        )
    else:
        logger.info(
            "Watermark is %s: loading %s to %s (lookback %d days)",
            watermark,
            start,
            end,
            settings.lookback_days,
        )

    try:
        extract(settings, start, end)
        transform(settings, start, end)
    except Exception:
        logger.exception("Pipeline failed")
        sys.exit(1)
    logger.info("Pipeline finished (load step comes next)")


if __name__ == "__main__":
    main()
