from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import EarningsEvent


async def list_for_symbol(session: AsyncSession, symbol: str, limit: int) -> Sequence[EarningsEvent]:
    stmt = (
        select(EarningsEvent)
        .where(EarningsEvent.symbol == symbol)
        .order_by(EarningsEvent.time.desc())
        .limit(limit)
    )
    return (await session.scalars(stmt)).all()


async def list_upcoming(session: AsyncSession, start: datetime, limit: int) -> Sequence[EarningsEvent]:
    stmt = (
        select(EarningsEvent)
        .where(EarningsEvent.time >= start)
        .order_by(EarningsEvent.time)
        .limit(limit)
    )
    return (await session.scalars(stmt)).all()
