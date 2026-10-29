from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class EarningsEvent(Base):
    __tablename__ = "earnings_events"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), ForeignKey("stocks.symbol", ondelete="CASCADE"), primary_key=True)
    eps_estimate: Mapped[Decimal | None] = mapped_column(Numeric(16, 4))
    eps_reported: Mapped[Decimal | None] = mapped_column(Numeric(16, 4))
    surprise_pct: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    source: Mapped[str] = mapped_column(String(20))
