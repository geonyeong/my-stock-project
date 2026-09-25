import math
from dataclasses import dataclass
from datetime import date, datetime

from prediction.writer import PredictionRow, direction_from_path, to_price, to_probability

# 80% 구간에 해당하는 표준정규 분위수
Z_80 = 1.2816


@dataclass(frozen=True)
class ForecastPath:
    symbol: str
    as_of: datetime
    last_close: float
    target_dates: list[date]
    mean: list[float]
    lower: list[float]
    upper: list[float]


def prob_above(last_close: float, mean: float, lower: float, upper: float) -> float:
    """80% 구간을 정규분포로 보고 종가가 last_close 보다 높을 확률을 근사한다."""
    sigma = (upper - lower) / (2 * Z_80)
    if sigma <= 0:
        return 1.0 if mean > last_close else 0.0
    return 0.5 * (1 + math.erf((mean - last_close) / (sigma * math.sqrt(2))))


def to_rows(path: ForecastPath, model_name: str) -> list[PredictionRow]:
    rows: list[PredictionRow] = []
    for target, mean, low, high in zip(path.target_dates, path.mean, path.lower, path.upper, strict=True):
        rows.append(
            PredictionRow(
                time=path.as_of,
                symbol=path.symbol,
                target_date=target,
                model_name=model_name,
                direction_signal=direction_from_path(path.last_close, mean),
                win_probability=to_probability(prob_above(path.last_close, mean, low, high)),
                predicted_close=to_price(mean),
                lower_bound=to_price(low),
                upper_bound=to_price(high),
            )
        )
    return rows
