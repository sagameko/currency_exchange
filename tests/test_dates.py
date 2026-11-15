from datetime import date

from currency_exchange.utils.dates import choose_date_range

INITIAL = date(2020, 1, 1)
TODAY = date(2026, 11, 15)


def test_first_run_loads_full_history():
    assert choose_date_range(None, TODAY, INITIAL, 3) == (INITIAL, TODAY)


def test_normal_run_goes_back_by_the_lookback():
    assert choose_date_range(date(2026, 11, 13), TODAY, INITIAL, 3) == (
        date(2026, 11, 10),
        TODAY,
    )


def test_lookback_never_goes_before_the_initial_start():
    assert choose_date_range(date(2020, 1, 2), TODAY, INITIAL, 3) == (INITIAL, TODAY)


def test_run_on_the_same_day_as_the_watermark_still_reloads_the_lookback():
    assert choose_date_range(TODAY, TODAY, INITIAL, 3) == (date(2026, 11, 12), TODAY)
