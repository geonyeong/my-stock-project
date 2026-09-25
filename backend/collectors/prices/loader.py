from dataclasses import asdict
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from collectors.prices.yahoo import DailyBar
from models import StockDailyCandle

BATCH_SIZE = 500


async def last_candle_time(session: AsyncSession, symbol: str) -> datetime | None:
    stmt = select(func.max(StockDailyCandle.time)).where(StockDailyCandle.symbol == symbol)
    return await session.scalar(stmt)


async def upsert_daily_bars(session: AsyncSession, symbol: str, bars: list[DailyBar]) -> int:
    """(time, symbol) 기준으로 덮어쓴다. 기존 행은 지우지 않는다."""
    for i in range(0, len(bars), BATCH_SIZE):
        rows = [{"symbol": symbol, **asdict(bar)} for bar in bars[i : i + BATCH_SIZE]]
        stmt = insert(StockDailyCandle).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[StockDailyCandle.time, StockDailyCandle.symbol],
            set_={
                "open_price": stmt.excluded.open_price,
                "high_price": stmt.excluded.high_price,
                "low_price": stmt.excluded.low_price,
                "close_price": stmt.excluded.close_price,
                "volume": stmt.excluded.volume,
                "flctu_rate": stmt.excluded.flctu_rate,
            },
        )
        await session.execute(stmt)
    await session.commit()
    return len(bars)
