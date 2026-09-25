CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

CREATE TABLE IF NOT EXISTS stocks (
    symbol VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    market VARCHAR(10) NOT NULL,
    sector VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stock_daily_candles (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    open_price NUMERIC(12, 2) NOT NULL,
    high_price NUMERIC(12, 2) NOT NULL,
    low_price NUMERIC(12, 2) NOT NULL,
    close_price NUMERIC(12, 2) NOT NULL,
    volume BIGINT NOT NULL,
    trading_value NUMERIC(20, 2),
    flctu_rate NUMERIC(6, 2),
    PRIMARY KEY (time, symbol),
    FOREIGN KEY (symbol) REFERENCES stocks (symbol) ON DELETE CASCADE
);

SELECT create_hypertable('stock_daily_candles', 'time', chunk_time_interval => INTERVAL '1 month', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_daily_symbol_time ON stock_daily_candles (symbol, time DESC);

CREATE TABLE IF NOT EXISTS stock_minute_candles (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    open_price NUMERIC(12, 2) NOT NULL,
    high_price NUMERIC(12, 2) NOT NULL,
    low_price NUMERIC(12, 2) NOT NULL,
    close_price NUMERIC(12, 2) NOT NULL,
    volume BIGINT NOT NULL,
    PRIMARY KEY (time, symbol),
    FOREIGN KEY (symbol) REFERENCES stocks (symbol) ON DELETE CASCADE
);

SELECT create_hypertable('stock_minute_candles', 'time', chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_minute_symbol_time ON stock_minute_candles (symbol, time DESC);

CREATE TABLE IF NOT EXISTS news_sentiments (
    time TIMESTAMPTZ NOT NULL,
    id BIGSERIAL,
    symbol VARCHAR(20),
    source VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    url TEXT,
    sentiment_label VARCHAR(10) NOT NULL,
    sentiment_score NUMERIC(5, 4) NOT NULL,
    impact_score NUMERIC(5, 4),
    summary TEXT,
    PRIMARY KEY (time, id),
    -- 하이퍼테이블의 유니크 제약은 파티션 컬럼(time)을 포함해야 한다.
    UNIQUE (time, url),
    FOREIGN KEY (symbol) REFERENCES stocks (symbol) ON DELETE SET NULL
);

SELECT create_hypertable('news_sentiments', 'time', chunk_time_interval => INTERVAL '1 month', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_news_symbol_time ON news_sentiments (symbol, time DESC);

CREATE TABLE IF NOT EXISTS ai_predictions (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    target_date DATE NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    predicted_close NUMERIC(12, 2),
    upper_bound NUMERIC(12, 2),
    lower_bound NUMERIC(12, 2),
    direction_signal VARCHAR(10) NOT NULL,
    win_probability NUMERIC(5, 4),
    PRIMARY KEY (time, symbol, model_name, target_date),
    FOREIGN KEY (symbol) REFERENCES stocks (symbol) ON DELETE CASCADE
);

SELECT create_hypertable('ai_predictions', 'time', chunk_time_interval => INTERVAL '1 month', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_predictions_symbol_target ON ai_predictions (symbol, target_date DESC);
