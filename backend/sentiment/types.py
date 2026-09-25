from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

SentimentLabel = Literal["positive", "negative", "neutral"]
LABELS: tuple[SentimentLabel, ...] = ("positive", "negative", "neutral")


@dataclass(frozen=True)
class SentimentResult:
    label: SentimentLabel
    # -1(부정) ~ 1(긍정). 일별 평균을 피처로 쓰기 위해 부호를 둔다.
    score: Decimal
    # 0 ~ 1. 주가 영향도. 모델이 제공하지 않으면 None.
    impact: Decimal | None


def to_score(value: float, low: float = -1.0, high: float = 1.0) -> Decimal:
    clamped = min(max(float(value), low), high)
    return Decimal(str(clamped)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
