CREATE TABLE IF NOT EXISTS etl_state (
    pipeline_name   TEXT    PRIMARY KEY,
    last_loaded_date    DATE    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
);