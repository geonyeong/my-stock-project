import pandas as pd

from collectors.rates.series import RATE_SERIES
from db.session import SessionLocal
from prediction.features import candles_frame, earnings_frame, rates_frame, sentiment_frame
from repositories import timeseries


async def load_candles(symbols: list[str]) -> pd.DataFrame:
    async with SessionLocal() as session:
        return candles_frame(await timeseries.load_daily_candles(session, symbols))


async def load_sentiment(symbols: list[str]) -> pd.DataFrame:
    async with SessionLocal() as session:
        return sentiment_frame(await timeseries.load_daily_sentiment(session, symbols))


async def load_earnings(symbols: list[str]) -> pd.DataFrame:
    async with SessionLocal() as session:
        return earnings_frame(await timeseries.load_earnings_events(session, symbols))


async def load_rates() -> pd.DataFrame:
    async with SessionLocal() as session:
        rows = await timeseries.load_daily_rates(session, [s.code for s in RATE_SERIES])
    return rates_frame(rows)
