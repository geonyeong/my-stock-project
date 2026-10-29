from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class EarningsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    time: datetime
    symbol: str
    eps_estimate: Decimal | None
    eps_reported: Decimal | None
    surprise_pct: Decimal | None
