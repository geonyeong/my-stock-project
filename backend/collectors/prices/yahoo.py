import logging
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

SOURCE = "yahoo"
KST = ZoneInfo("Asia/Seoul")
REQUEST_TIMEOUT_SEC = 20
MAX_RETRIES = 3
RETRY_BACKOFF_SEC = 2.0
# 첫 행의 등락률을 계산하려고 요청 시작일보다 앞선 구간을 함께 받는다.
LOOKBACK_BUFFER_DAYS = 14


@dataclass(frozen=True)
class DailyBar:
    time: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int
    flctu_rate: Decimal | None


def _to_price(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _download(ticker: str, start: date, end: date) -> pd.DataFrame:
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return yf.Ticker(ticker).history(
                start=start.isoformat(),
                end=(end + timedelta(days=1)).isoformat(),
                interval="1d",
                auto_adjust=False,
                actions=False,
                timeout=REQUEST_TIMEOUT_SEC,
                raise_errors=True,
            )
        except Exception as exc:
            last_error = exc
            logger.warning("일봉 요청 실패 source=%s ticker=%s attempt=%d/%d: %s", SOURCE, ticker, attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SEC * attempt)
    raise RuntimeError(f"{ticker} 일봉 요청이 {MAX_RETRIES}회 모두 실패했습니다.") from last_error


def _normalize(frame: pd.DataFrame, start: date) -> list[DailyBar]:
    frame = frame.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
    frame = frame[frame["Volume"] > 0]
    prev_close = frame["Close"].shift(1)
    rates = (frame["Close"] / prev_close - 1) * 100

    bars: list[DailyBar] = []
    for ts, row in frame.iterrows():
        day = pd.Timestamp(ts).date()
        if day < start:
            continue
        rate = rates.loc[ts]
        bars.append(
            DailyBar(
                time=datetime(day.year, day.month, day.day, tzinfo=KST),
                open_price=_to_price(row["Open"]),
                high_price=_to_price(row["High"]),
                low_price=_to_price(row["Low"]),
                close_price=_to_price(row["Close"]),
                volume=int(row["Volume"]),
                flctu_rate=None if pd.isna(rate) else _to_price(rate),
            )
        )
    return bars


def fetch_daily_bars(ticker: str, start: date, end: date) -> list[DailyBar]:
    """yfinance 로 [start, end] 구간 일봉을 가져온다. 수정주가가 아닌 원시 가격이다."""
    frame = _download(ticker, start - timedelta(days=LOOKBACK_BUFFER_DAYS), end)
    return _normalize(frame, start)
