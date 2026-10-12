"""미국 국채 금리를 수집해 macro_daily_rates 에 적재한다.

실행 예:
  docker compose exec backend python -m collectors.rates.run
  docker compose exec backend python -m collectors.rates.run --series US10Y --start 2023-01-01
"""

import argparse
import asyncio
import logging
from datetime import date, datetime, timedelta

from collectors.rates import loader
from collectors.rates.series import RATE_SERIES, RATE_SERIES_BY_CODE, RateSeries
from collectors.rates.yahoo_rates import SOURCE, fetch_rate_points
from core.logging import setup_logging
from db.session import SessionLocal, engine

logger = logging.getLogger(__name__)

# LightGBM 학습 기간(일봉 3년)과 20일 변화량 계산 여유를 덮는다.
DEFAULT_HISTORY_DAYS = 365 * 3 + 60
INCREMENTAL_OVERLAP_DAYS = 7


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="국채 금리 수집")
    parser.add_argument("--series", nargs="*", choices=list(RATE_SERIES_BY_CODE), help="생략하면 전체")
    parser.add_argument("--start", type=date.fromisoformat, help="시작일 YYYY-MM-DD. 생략하면 증분 수집")
    return parser.parse_args()


async def _resolve_start(series: RateSeries, explicit: date | None) -> date:
    if explicit:
        return explicit
    async with SessionLocal() as session:
        last = await loader.last_rate_time(session, series.code)
    if last is None:
        return date.today() - timedelta(days=DEFAULT_HISTORY_DAYS)
    return last.astimezone(series.timezone).date() - timedelta(days=INCREMENTAL_OVERLAP_DAYS)


async def collect_one(series: RateSeries, explicit_start: date | None) -> int:
    start = await _resolve_start(series, explicit_start)
    end = datetime.now(series.timezone).date()
    points = await asyncio.to_thread(fetch_rate_points, series, start, end)
    async with SessionLocal() as session:
        return await loader.upsert_rate_points(session, series.code, SOURCE, points)


async def main() -> None:
    args = _parse_args()
    targets = [RATE_SERIES_BY_CODE[c] for c in args.series] if args.series else list(RATE_SERIES)
    failed: list[str] = []
    try:
        for series in targets:
            try:
                count = await collect_one(series, args.start)
                logger.info("금리 적재 series=%s source=%s rows=%d", series.code, SOURCE, count)
            except Exception:
                failed.append(series.code)
                logger.exception("금리 수집 실패 series=%s source=%s at=%s", series.code, SOURCE, datetime.now().isoformat())
    finally:
        await engine.dispose()
    if failed:
        logger.error("실패 시리즈: %s", ", ".join(failed))
        raise SystemExit(1)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
