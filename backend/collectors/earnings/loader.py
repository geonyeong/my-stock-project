from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from collectors.earnings.yahoo_earnings import SOURCE, EarningsPoint
from models import EarningsEvent

KST = ZoneInfo("Asia/Seoul")


def seoul_today_start() -> datetime:
    now = datetime.now(KST)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


async def upsert_earnings(session: AsyncSession, symbol: str, points: list[EarningsPoint]) -> int:
    """(time, symbol) 기준으로 덮어쓰고, 이번 응답에 없는 오늘 이후 일정은 지운다.

    과거 행은 유지한다. 예정일이 옮겨진 경우에만 오늘 이후의 빠진 일정을 제거한다.
    """
    if not points:
        return 0
    rows = [
        {
            "time": point.time,
            "symbol": symbol,
            "eps_estimate": point.eps_estimate,
            "eps_reported": point.eps_reported,
            "surprise_pct": point.surprise_pct,
            "source": SOURCE,
        }
        for point in points
    ]
    stmt = insert(EarningsEvent).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[EarningsEvent.time, EarningsEvent.symbol],
        set_={
            "eps_estimate": stmt.excluded.eps_estimate,
            "eps_reported": stmt.excluded.eps_reported,
            "surprise_pct": stmt.excluded.surprise_pct,
            "source": stmt.excluded.source,
        },
    )
    await session.execute(stmt)
    kept = [point.time for point in points]
    await session.execute(
        delete(EarningsEvent).where(
            EarningsEvent.symbol == symbol,
            EarningsEvent.time >= seoul_today_start(),
            EarningsEvent.time.notin_(kept),
        )
    )
    await session.commit()
    return len(rows)
