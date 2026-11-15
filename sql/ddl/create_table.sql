CREATE TABLE IF NOT EXISTS etl_state (
    pipeline_name   TEXT    PRIMARY KEY,
    last_loaded_date    DATE    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
);

CREATE TABLE IF NOT EXISTS dim_currency (
    currency_code TEXT  PRIMARY KEY,
    currency_name TEXT  NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key      INTEGER PRIMARY KEY,         -- 20260102
    full_date     DATE    NOT NULL UNIQUE,
    day           INTEGER NOT NULL,
    month         INTEGER NOT NULL,
    month_name    TEXT    NOT NULL,
    quarter       INTEGER NOT NULL,
    year          INTEGER NOT NULL,
    day_of_week   TEXT    NOT NULL,
    is_weekend    BOOLEAN NOT NULL,
    is_published  BOOLEAN NOT NULL             -- did the ECB publish rates on this day?
);

CREATE TABLE IF NOT EXISTS fct_daily_rate (
    date_key         INTEGER        NOT NULL,
    currency_code    TEXT           NOT NULL,
    foreign_per_aud  DECIMAL(18, 8) NOT NULL,  -- 1 AUD = this many units of the currency
    loaded_at        TIMESTAMP      NOT NULL,  -- when this row was loaded (UTC)
    PRIMARY KEY (date_key, currency_code)      -- the grain
);