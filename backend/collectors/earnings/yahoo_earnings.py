import logging
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

SOURCE = "yahoo"
KST = ZoneInfo("Asia/Seoul")
REQUEST_ATTEMPTS = 3
RETRY_BACKOFF_SEC = 2.0
# 분기 실적 약 6년과 다가오는 예정일을 한 번에 받는다.
FETCH_LIMIT = 24
EPS_SCALE = Decimal("0.0001")
SURPRISE_SCALE = Decimal("0.0001")


@dataclass(frozen=True)
class EarningsPoint:
    time: datetime
    eps_estimate: Decimal | None
    eps_reported: Decimal | None
    surprise_pct: Decimal | None


def _optional_decimal(value: object, scale: Decimal) -> Decimal | None:
    if value is None or pd.isna(value):
        return None
    return Decimal(str(value)).quantize(scale, rounding=ROUND_HALF_UP)


def _to_point(ts: object, row: pd.Series) -> EarningsPoint:
    day = pd.Timestamp(ts).tz_convert(KST).date()
    return EarningsPoint(
        time=datetime(day.year, day.month, day.day, tzinfo=KST),
        eps_estimate=_optional_decimal(row["EPS Estimate"], EPS_SCALE),
        eps_reported=_optional_decimal(row["Reported EPS"], EPS_SCALE),
        surprise_pct=_optional_decimal(row["Surprise(%)"], SURPRISE_SCALE),
    )


def _dedupe(points: list[EarningsPoint]) -> list[EarningsPoint]:
    """같은 한국 날짜가 여러 번이면 발표 EPS 가 있는 행을 남긴다."""
    chosen: dict[datetime, EarningsPoint] = {}
    for point in points:
        current = chosen.get(point.time)
        if current is None or (current.eps_reported is None and point.eps_reported is not None):
            chosen[point.time] = point
    return list(chosen.values())


def fetch_earnings_points(ticker: str) -> list[EarningsPoint]:
    """yfinance 실적 일정을 한국 날짜 00:00 기준으로 돌려준다. 타임아웃 대신 재시도 상한을 둔다."""
    frame = _download_earnings(ticker)
    if frame is None or frame.empty:
        return []
    missing = [name for name in ("EPS Estimate", "Reported EPS", "Surprise(%)") if name not in frame.columns]
    if missing:
        raise RuntimeError(f"{ticker} 실적 일정 컬럼이 없습니다: {', '.join(missing)}")
    points = [_to_point(ts, row) for ts, row in frame.iterrows()]
    return _dedupe(points)


def _download_earnings(ticker: str) -> pd.DataFrame | None:
    last_error: Exception | None = None
    for attempt in range(1, REQUEST_ATTEMPTS + 1):
        try:
            return yf.Ticker(ticker).get_earnings_dates(limit=FETCH_LIMIT)
        except Exception as exc:
            last_error = exc
            logger.warning(
                "실적 일정 요청 실패 source=%s ticker=%s attempt=%d/%d: %s",
                SOURCE, ticker, attempt, REQUEST_ATTEMPTS, exc,
            )
            if attempt < REQUEST_ATTEMPTS:
                time.sleep(RETRY_BACKOFF_SEC * attempt)
    raise RuntimeError(f"{ticker} 실적 일정 요청이 {REQUEST_ATTEMPTS}회 모두 실패했습니다.") from last_error
