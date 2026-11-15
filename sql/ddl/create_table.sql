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

-- Rate for ANY calendar day: the latest published rate on or before that day.
-- The fact table stays honest (published days only); this view does the carry-forward.
CREATE OR REPLACE VIEW v_rate_as_of AS
WITH calendar AS (
    -- every day x every currency
    SELECT d.date_key, d.full_date, d.day_of_week, c.currency_code
    FROM dim_date d
    CROSS JOIN dim_currency c
),
published_rates AS (
    -- the facts, with a real date column to compare against
    SELECT f.currency_code, d.full_date AS rate_date, f.foreign_per_aud
    FROM fct_daily_rate f
    JOIN dim_date d ON f.date_key = d.date_key
)
SELECT
    cal.date_key,
    cal.full_date,
    cal.day_of_week,
    cal.currency_code,
    r.rate_date,                                              -- which day the rate came from
    r.foreign_per_aud,                                        -- 1 AUD = x foreign
    CAST(1 / r.foreign_per_aud AS DECIMAL(18, 8)) AS aud_per_foreign,   -- 1 foreign = x AUD
    r.rate_date < cal.full_date AS is_carried_forward         -- true on weekends and holidays
FROM calendar cal
ASOF LEFT JOIN published_rates r
    ON cal.currency_code = r.currency_code
   AND cal.full_date >= r.rate_date;