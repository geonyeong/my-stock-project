"""유니버스 종목의 일봉을 수집해 stock_daily_candles 에 적재한다.

실행 예:
  docker compose exec backend python -m collectors.prices.run
  docker compose exec backend python -m collectors.prices.run --symbols 005930 000660 --start 2023-01-01
"""

import argparse
import asyncio
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from collectors.prices import loader
from collectors.prices.yahoo import SOURCE, fetch_daily_bars
from collectors.universe import UniverseItem, resolve
from core.logging import setup_logging
from db.session import SessionLocal, engine
from models import Stock

logger = logging.getLogger(__name__)

KST = ZoneInfo("Asia/Seoul")
DEFAULT_HISTORY_YEARS = 3
# 수정 발표·지연 반영을 덮어쓰려고 마지막 적재일보다 며칠 앞에서 다시 받는다.
INCREMENTAL_OVERLAP_DAYS = 7


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="일봉 수집")
    parser.add_argument("--symbols", nargs="*", help="대상 종목 코드. 생략하면 유니버스 전체")
    parser.add_argument("--start", type=date.fromisoformat, help="시작일 YYYY-MM-DD. 생략하면 증분 수집")
    parser.add_argument("--years", type=int, default=DEFAULT_HISTORY_YEARS, help="적재 이력이 없을 때 받을 기간(년)")
    return parser.parse_args()


async def _resolve_start(item: UniverseItem, explicit: date | None, years: int) -> date:
    if explicit:
        return explicit
    async with SessionLocal() as session:
        last = await loader.last_candle_time(session, item.symbol)
    if last is None:
        return date.today() - timedelta(days=365 * years)
    return last.astimezone(KST).date() - timedelta(days=INCREMENTAL_OVERLAP_DAYS)


async def collect_one(item: UniverseItem, explicit_start: date | None, years: int) -> int:
    async with SessionLocal() as session:
        if await session.get(Stock, item.symbol) is None:
            raise LookupError("stocks 테이블에 없는 종목입니다. scripts.seed_stocks 를 먼저 실행하세요.")

    start = await _resolve_start(item, explicit_start, years)
    end = datetime.now(KST).date()
    bars = await asyncio.to_thread(fetch_daily_bars, item.yahoo_ticker, start, end)

    async with SessionLocal() as session:
        return await loader.upsert_daily_bars(session, item.symbol, bars)


async def main() -> None:
    args = _parse_args()
    try:
        items = resolve(args.symbols)
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    failed: list[str] = []
    try:
        for item in items:
            try:
                count = await collect_one(item, args.start, args.years)
                logger.info("일봉 적재 symbol=%s source=%s rows=%d", item.symbol, SOURCE, count)
            except Exception:
                failed.append(item.symbol)
                logger.exception("일봉 수집 실패 symbol=%s source=%s at=%s", item.symbol, SOURCE, datetime.now(KST).isoformat())
    finally:
        await engine.dispose()
    if failed:
        logger.error("실패 종목: %s", ", ".join(failed))
        raise SystemExit(1)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
