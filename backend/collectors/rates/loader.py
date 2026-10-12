from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from collectors.rates.yahoo_rates import RatePoint
from models import MacroDailyRate


async def last_rate_time(session: AsyncSession, series_code: str) -> datetime | None:
    stmt = select(func.max(MacroDailyRate.time)).where(MacroDailyRate.series_code == series_code)
    return await session.scalar(stmt)


async def upsert_rate_points(session: AsyncSession, series_code: str, source: str, points: list[RatePoint]) -> int:
    """(time, series_code) 기준으로 덮어쓴다. 기존 행은 지우지 않는다."""
    if not points:
        return 0
    rows = [{"time": p.time, "series_code": series_code, "value": p.value, "source": source} for p in points]
    stmt = insert(MacroDailyRate).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[MacroDailyRate.time, MacroDailyRate.series_code],
        set_={"value": stmt.excluded.value, "source": stmt.excluded.source},
    )
    await session.execute(stmt)
    await session.commit()
    return len(rows)
