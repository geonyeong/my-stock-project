-- 기존 볼륨에 macro_daily_rates 를 추가한다. 새 볼륨은 init.sql 에 이미 포함되어 있다.
-- 적용: docker compose exec -T timescaledb sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < docker/timescaledb/migrations/001_macro_daily_rates.sql
-- 여러 번 실행해도 안전하다.

CREATE TABLE IF NOT EXISTS macro_daily_rates (
    time TIMESTAMPTZ NOT NULL,
    series_code VARCHAR(20) NOT NULL,
    value NUMERIC(8, 4) NOT NULL,
    source VARCHAR(20) NOT NULL,
    PRIMARY KEY (time, series_code)
);

SELECT create_hypertable('macro_daily_rates', 'time', chunk_time_interval => INTERVAL '1 year', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_macro_series_time ON macro_daily_rates (series_code, time DESC);
