"""유니버스 종목의 실적 발표 일정을 earnings_events 에 적재한다.

ETF 는 실적 발표가 없어 건너뛴다. 응답이 비어 있으면 기존 일정을 지우지 않고 경고만 남긴다.

실행 예:
  docker compose exec backend python -m collectors.earnings.run
  docker compose exec backend python -m collectors.earnings.run --symbol 005930
"""

import argparse
import asyncio
import logging
from datetime import datetime

from collectors.earnings import loader
from collectors.earnings.yahoo_earnings import SOURCE, fetch_earnings_points
from collectors.universe import resolve
from core.logging import setup_logging
from db.session import SessionLocal, engine

logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="실적 발표 일정 수집")
    parser.add_argument("--symbol", nargs="*", help="생략하면 ETF 를 제외한 유니버스 전체")
    return parser.parse_args()


async def collect_one(symbol: str, ticker: str) -> int:
    points = await asyncio.to_thread(fetch_earnings_points, ticker)
    if not points:
        logger.warning("실적 일정이 비어 있습니다 symbol=%s source=%s", symbol, SOURCE)
        return 0
    async with SessionLocal() as session:
        return await loader.upsert_earnings(session, symbol, points)


async def main() -> None:
    args = _parse_args()
    targets = [item for item in resolve(args.symbol) if item.sector != "ETF"]
    failed: list[str] = []
    try:
        for item in targets:
            try:
                count = await collect_one(item.symbol, item.yahoo_ticker)
                logger.info("실적 일정 적재 symbol=%s source=%s rows=%d", item.symbol, SOURCE, count)
            except Exception:
                failed.append(item.symbol)
                logger.exception(
                    "실적 일정 수집 실패 symbol=%s source=%s at=%s",
                    item.symbol, SOURCE, datetime.now().isoformat(),
                )
    finally:
        await engine.dispose()
    if failed:
        logger.error("실패 종목: %s", ", ".join(failed))
        raise SystemExit(1)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
