"""예측 배치가 쓰는 시계열 조회. pandas 로 바로 넘기기 쉬운 dict 목록을 돌려준다."""

from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import Date

from models import EarningsEvent, MacroDailyRate, NewsSentiment, StockDailyCandle


async def load_daily_candles(session: AsyncSession, symbols: list[str]) -> list[dict]:
    stmt = (
        select(
            StockDailyCandle.symbol,
            StockDailyCandle.time,
            StockDailyCandle.open_price,
            StockDailyCandle.high_price,
            StockDailyCandle.low_price,
            StockDailyCandle.close_price,
            StockDailyCandle.volume,
        )
        .where(StockDailyCandle.symbol.in_(symbols))
        .order_by(StockDailyCandle.symbol, StockDailyCandle.time)
    )
    return [dict(row._mapping) for row in await session.execute(stmt)]


async def load_daily_sentiment(session: AsyncSession, symbols: list[str]) -> list[dict]:
    """종목·한국 날짜별 평균 감성 점수와 기사 수."""
    day = cast(func.timezone("Asia/Seoul", NewsSentiment.time), Date).label("day")
    stmt = (
        select(
            NewsSentiment.symbol,
            day,
            func.avg(NewsSentiment.sentiment_score).label("sentiment_mean"),
            func.count().label("news_count"),
        )
        .where(NewsSentiment.symbol.in_(symbols))
        .group_by(NewsSentiment.symbol, day)
    )
    return [dict(row._mapping) for row in await session.execute(stmt)]


async def load_earnings_events(session: AsyncSession, symbols: list[str]) -> list[dict]:
    stmt = (
        select(EarningsEvent.symbol, EarningsEvent.time)
        .where(EarningsEvent.symbol.in_(symbols))
        .order_by(EarningsEvent.symbol, EarningsEvent.time)
    )
    return [dict(row._mapping) for row in await session.execute(stmt)]


async def load_daily_rates(session: AsyncSession, series_codes: list[str]) -> list[dict]:
    stmt = (
        select(MacroDailyRate.series_code, MacroDailyRate.time, MacroDailyRate.value)
        .where(MacroDailyRate.series_code.in_(series_codes))
        .order_by(MacroDailyRate.time)
    )
    return [dict(row._mapping) for row in await session.execute(stmt)]
