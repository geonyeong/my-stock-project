-- 기존 볼륨에 earnings_events 를 추가한다. 새 볼륨은 init.sql 에 이미 포함되어 있다.
-- 적용: docker compose exec -T timescaledb sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < docker/timescaledb/migrations/002_earnings_events.sql
-- 여러 번 실행해도 안전하다.

CREATE TABLE IF NOT EXISTS earnings_events (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    eps_estimate NUMERIC(16, 4),
    eps_reported NUMERIC(16, 4),
    surprise_pct NUMERIC(12, 4),
    source VARCHAR(20) NOT NULL,
    PRIMARY KEY (time, symbol),
    FOREIGN KEY (symbol) REFERENCES stocks (symbol) ON DELETE CASCADE
);

SELECT create_hypertable('earnings_events', 'time', chunk_time_interval => INTERVAL '1 year', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_earnings_symbol_time ON earnings_events (symbol, time DESC);
