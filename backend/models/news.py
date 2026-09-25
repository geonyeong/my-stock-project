from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class NewsSentiment(Base):
    __tablename__ = "news_sentiments"
    __table_args__ = (UniqueConstraint("time", "url"),)

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    symbol: Mapped[str | None] = mapped_column(String(20), ForeignKey("stocks.symbol"))
    source: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    sentiment_label: Mapped[str] = mapped_column(String(10))
    sentiment_score: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    impact_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    summary: Mapped[str | None] = mapped_column(Text)
