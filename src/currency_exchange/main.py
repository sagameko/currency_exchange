import logging
from datetime import date
from currency_exchange.config import load_settings
from currency_exchange.logging_setup import setup_logging
from currency_exchange.extract.frankfurter import extract

logger = logging.getLogger(__name__)


def main():
    settings = load_settings()
    setup_logging(settings.log_dir)

    logger.info(
        "FX pipeline started: %s -> %s, history from %s, lookback %d days",
        settings.base_currency,
        ", ".join(settings.currencies),
        settings.initial_start_date,
        settings.lookback_days,
    )

    path = extract(settings, date(2026, 1, 1), date(2026, 1, 31))
    logger.info("Raw file: %s", path)


if __name__ == "__main__":
    main()
