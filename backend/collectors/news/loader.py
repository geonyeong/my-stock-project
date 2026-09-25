from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from collectors.news.google_rss import RawArticle
from models import NewsSentiment
from sentiment.types import SentimentResult


async def existing_urls(session: AsyncSession, urls: list[str]) -> set[str]:
    if not urls:
        return set()
    stmt = select(NewsSentiment.url).where(NewsSentiment.url.in_(urls))
    return set((await session.scalars(stmt)).all())


async def insert_scored(
    session: AsyncSession, symbol: str | None, scored: list[tuple[RawArticle, SentimentResult]]
) -> int:
    """(time, url) 이 겹치면 건너뛴다."""
    if not scored:
        return 0
    rows = [
        {
            "time": article.time,
            "symbol": symbol,
            "source": article.source,
            "title": article.title,
            "url": article.url,
            "summary": article.summary,
            "sentiment_label": result.label,
            "sentiment_score": result.score,
            "impact_score": result.impact,
        }
        for article, result in scored
    ]
    stmt = insert(NewsSentiment).values(rows).on_conflict_do_nothing(index_elements=["time", "url"])
    res = await session.execute(stmt)
    await session.commit()
    return res.rowcount or 0
