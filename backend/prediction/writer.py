from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from models import AiPrediction

UP_THRESHOLD = 0.55
DOWN_THRESHOLD = 0.45


@dataclass(frozen=True)
class PredictionRow:
    time: datetime
    symbol: str
    target_date: date
    model_name: str
    direction_signal: str
    win_probability: Decimal | None = None
    predicted_close: Decimal | None = None
    upper_bound: Decimal | None = None
    lower_bound: Decimal | None = None


def direction_from_prob(prob_up: float) -> str:
    if prob_up >= UP_THRESHOLD:
        return "up"
    if prob_up <= DOWN_THRESHOLD:
        return "down"
    return "flat"


def direction_from_path(last_close: float, predicted: float, flat_band: float = 0.01) -> str:
    change = predicted / last_close - 1
    if change > flat_band:
        return "up"
    if change < -flat_band:
        return "down"
    return "flat"


def to_probability(value: float) -> Decimal:
    return Decimal(str(min(max(value, 0.0), 1.0))).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def to_price(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def upsert_predictions(session: AsyncSession, rows: list[PredictionRow]) -> int:
    """같은 기준 시각·종목·모델·목표일이면 덮어쓴다."""
    if not rows:
        return 0
    stmt = insert(AiPrediction).values([asdict(r) for r in rows])
    stmt = stmt.on_conflict_do_update(
        index_elements=["time", "symbol", "model_name", "target_date"],
        set_={
            col: stmt.excluded[col]
            for col in ["direction_signal", "win_probability", "predicted_close", "upper_bound", "lower_bound"]
        },
    )
    await session.execute(stmt)
    await session.commit()
    return len(rows)
