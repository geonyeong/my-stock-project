from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class AiPrediction(Base):
    __tablename__ = "ai_predictions"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), ForeignKey("stocks.symbol"), primary_key=True)
    target_date: Mapped[date] = mapped_column(Date, primary_key=True)
    model_name: Mapped[str] = mapped_column(String(50), primary_key=True)
    predicted_close: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    upper_bound: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    lower_bound: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    direction_signal: Mapped[str] = mapped_column(String(10))
    win_probability: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
