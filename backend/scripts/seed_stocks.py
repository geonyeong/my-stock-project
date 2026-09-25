"""유니버스 종목을 stocks 테이블에 등록한다.

실행: docker compose exec backend python -m scripts.seed_stocks
"""

import asyncio
import logging

from sqlalchemy.dialects.postgresql import insert

from collectors.universe import UNIVERSE
from core.logging import setup_logging
from db.session import SessionLocal, engine
from models import Stock

logger = logging.getLogger(__name__)


async def seed() -> None:
    rows = [
        {"symbol": i.symbol, "name": i.name, "market": i.market, "sector": i.sector, "is_active": True}
        for i in UNIVERSE
    ]
    stmt = insert(Stock).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Stock.symbol],
        set_={"name": stmt.excluded.name, "market": stmt.excluded.market, "sector": stmt.excluded.sector},
    )
    async with SessionLocal() as session:
        await session.execute(stmt)
        await session.commit()
    logger.info("종목 %d개 등록", len(rows))


async def main() -> None:
    try:
        await seed()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
