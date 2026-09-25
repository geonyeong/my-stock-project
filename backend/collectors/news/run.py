"""종목별 뉴스를 수집하고 감성을 매겨 news_sentiments 에 적재한다.

국내 뉴스는 Ollama, 영문 뉴스는 FinBERT 를 쓴다. FinBERT 는 requirements-ml.txt 가 설치된
호스트 venv 에서 실행해야 MPS 를 쓴다. 설치되지 않은 환경에서는 영문 뉴스를 건너뛴다.

실행 예:
  docker compose exec backend python -m collectors.news.run --lang ko
  (backend/.venv) python -m collectors.news.run --lang en
"""

import argparse
import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from collectors.news import loader
from collectors.news.google_rss import Language, fetch_articles
from collectors.universe import UniverseItem, resolve
from core.logging import setup_logging
from db.session import SessionLocal, engine
from sentiment.service import SentimentService

logger = logging.getLogger(__name__)

KST = ZoneInfo("Asia/Seoul")
SOURCE = "google_news_rss"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="뉴스 수집 + 감성 분석")
    parser.add_argument("--symbols", nargs="*", help="대상 종목 코드. 생략하면 유니버스 전체")
    parser.add_argument("--lang", nargs="*", choices=["ko", "en"], default=["ko", "en"])
    parser.add_argument("--limit", type=int, default=20, help="종목·언어별 최대 기사 수")
    return parser.parse_args()


async def collect_one(item: UniverseItem, langs: list[Language], limit: int, service: SentimentService) -> int:
    queries: dict[Language, str] = {"ko": item.news_query_ko, "en": item.news_query_en}
    articles = []
    for lang in langs:
        articles += await asyncio.to_thread(fetch_articles, queries[lang], lang, limit)

    async with SessionLocal() as session:
        known = await loader.existing_urls(session, [a.url for a in articles])
    fresh = [a for a in articles if a.url not in known]

    scored = await asyncio.to_thread(service.score, item.name, fresh)
    async with SessionLocal() as session:
        return await loader.insert_scored(session, item.symbol, scored)


async def main() -> None:
    args = _parse_args()
    try:
        items = resolve(args.symbols)
    except ValueError as exc:
        raise SystemExit(str(exc)) from None

    service = SentimentService()
    failed: list[str] = []
    try:
        for item in items:
            try:
                count = await collect_one(item, args.lang, args.limit, service)
                logger.info("뉴스 적재 symbol=%s source=%s rows=%d", item.symbol, SOURCE, count)
            except Exception:
                failed.append(item.symbol)
                logger.exception("뉴스 수집 실패 symbol=%s source=%s at=%s", item.symbol, SOURCE, datetime.now(KST).isoformat())
    finally:
        service.close()
        await engine.dispose()
    if failed:
        logger.error("실패 종목: %s", ", ".join(failed))
        raise SystemExit(1)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
