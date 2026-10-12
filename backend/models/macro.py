from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class MacroDailyRate(Base):
    __tablename__ = "macro_daily_rates"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    series_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    value: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    source: Mapped[str] = mapped_column(String(20))
