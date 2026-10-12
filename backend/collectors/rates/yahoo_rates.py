from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

import pandas as pd

from collectors.prices.yahoo import download_history
from collectors.rates.series import RateSeries

SOURCE = "yahoo"


@dataclass(frozen=True)
class RatePoint:
    time: datetime
    value: Decimal


def fetch_rate_points(series: RateSeries, start: date, end: date) -> list[RatePoint]:
    """종가 기준 일별 금리(%)를 돌려준다. time 은 해당 시장 현지 날짜 00:00 이다."""
    frame = download_history(series.yahoo_ticker, start, end).dropna(subset=["Close"])
    points: list[RatePoint] = []
    for ts, close in frame["Close"].items():
        day = pd.Timestamp(ts).date()
        points.append(
            RatePoint(
                time=datetime(day.year, day.month, day.day, tzinfo=series.timezone),
                value=Decimal(str(close)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            )
        )
    return points
