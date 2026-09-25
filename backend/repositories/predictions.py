from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import AiPrediction


async def list_latest_predictions(session: AsyncSession, symbol: str) -> Sequence[AiPrediction]:
    """모델별로 가장 최근 기준 시각(time)의 예측 행 전체를 돌려준다."""
    latest = (
        select(AiPrediction.model_name, func.max(AiPrediction.time).label("max_time"))
        .where(AiPrediction.symbol == symbol)
        .group_by(AiPrediction.model_name)
        .subquery()
    )
    stmt = (
        select(AiPrediction)
        .join(
            latest,
            (AiPrediction.model_name == latest.c.model_name) & (AiPrediction.time == latest.c.max_time),
        )
        .where(AiPrediction.symbol == symbol)
        .order_by(AiPrediction.model_name, AiPrediction.target_date)
    )
    return (await session.scalars(stmt)).all()
