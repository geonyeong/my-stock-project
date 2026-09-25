from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class StockDailyCandle(Base):
    __tablename__ = "stock_daily_candles"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), ForeignKey("stocks.symbol"), primary_key=True)
    open_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    high_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    low_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    close_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    volume: Mapped[int] = mapped_column(BigInteger)
    trading_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    flctu_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
