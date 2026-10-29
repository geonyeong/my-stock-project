from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class WalkForwardOut(BaseModel):
    accuracy: float
    baseline_accuracy: float
    test_start: str
    test_end: str


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    time: datetime
    target_date: date
    model_name: str
    direction_signal: str
    win_probability: Decimal | None
    predicted_close: Decimal | None
    upper_bound: Decimal | None
    lower_bound: Decimal | None
    evaluation: WalkForwardOut | None = None
