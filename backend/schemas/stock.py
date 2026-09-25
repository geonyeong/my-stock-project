from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class StockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    name: str
    market: str
    sector: str | None
    is_active: bool


class CandleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    time: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int
    trading_value: Decimal | None
    flctu_rate: Decimal | None
