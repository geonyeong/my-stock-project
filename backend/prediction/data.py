import pandas as pd

from db.session import SessionLocal
from prediction.features import candles_frame, sentiment_frame
from repositories import timeseries


async def load_candles(symbols: list[str]) -> pd.DataFrame:
    async with SessionLocal() as session:
        return candles_frame(await timeseries.load_daily_candles(session, symbols))


async def load_sentiment(symbols: list[str]) -> pd.DataFrame:
    async with SessionLocal() as session:
        return sentiment_frame(await timeseries.load_daily_sentiment(session, symbols))
