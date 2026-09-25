from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class NewsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    time: datetime
    symbol: str | None
    source: str
    title: str
    url: str | None
    sentiment_label: str
    sentiment_score: Decimal
    impact_score: Decimal | None
