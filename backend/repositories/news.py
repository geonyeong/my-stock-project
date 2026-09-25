from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import NewsSentiment


async def list_news(session: AsyncSession, symbol: str | None, limit: int) -> Sequence[NewsSentiment]:
    stmt = select(NewsSentiment).order_by(NewsSentiment.time.desc()).limit(limit)
    if symbol:
        stmt = stmt.where(NewsSentiment.symbol == symbol)
    return (await session.scalars(stmt)).all()
