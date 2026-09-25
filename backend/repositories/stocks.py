from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Stock, StockDailyCandle


async def list_stocks(session: AsyncSession, active_only: bool = True) -> Sequence[Stock]:
    stmt = select(Stock).order_by(Stock.market, Stock.symbol)
    if active_only:
        stmt = stmt.where(Stock.is_active.is_(True))
    return (await session.scalars(stmt)).all()


async def get_stock(session: AsyncSession, symbol: str) -> Stock | None:
    return await session.get(Stock, symbol)


async def list_daily_candles(session: AsyncSession, symbol: str, limit: int) -> Sequence[StockDailyCandle]:
    """최근 limit 개를 가져와 시간 오름차순으로 돌려준다."""
    stmt = (
        select(StockDailyCandle)
        .where(StockDailyCandle.symbol == symbol)
        .order_by(StockDailyCandle.time.desc())
        .limit(limit)
    )
    rows = (await session.scalars(stmt)).all()
    return list(reversed(rows))
