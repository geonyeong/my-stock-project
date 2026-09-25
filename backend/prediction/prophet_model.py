"""Prophet 으로 종목별 추세와 80% 구간을 추정한다. prophet 은 requirements-ml.txt 에 있다."""

import logging

import numpy as np
import pandas as pd

from prediction.calendar import trading_days_after
from prediction.forecast import ForecastPath

logger = logging.getLogger(__name__)

TRAIN_DAYS = 500
INTERVAL_WIDTH = 0.8


class ProphetUnavailableError(RuntimeError):
    pass


def _prophet_cls():
    try:
        from prophet import Prophet
    except ImportError as exc:
        raise ProphetUnavailableError("prophet 이 설치되지 않았습니다. requirements-ml.txt 를 설치하세요.") from exc
    return Prophet


def forecast_symbol(g: pd.DataFrame, horizon: int) -> ForecastPath:
    """로그 종가에 맞춰 곱셈형 변동을 반영하고, 결과는 가격으로 되돌린다."""
    prophet_cls = _prophet_cls()
    hist = g.tail(TRAIN_DAYS)
    train = pd.DataFrame({"ds": pd.to_datetime(hist["day"]), "y": np.log(hist["close_price"].to_numpy())})

    model = prophet_cls(
        interval_width=INTERVAL_WIDTH,
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=True,
        changepoint_prior_scale=0.05,
    )
    model.fit(train)

    last = hist.iloc[-1]
    targets = trading_days_after(last["day"], horizon)
    pred = model.predict(pd.DataFrame({"ds": pd.to_datetime(targets)}))
    return ForecastPath(
        symbol=str(last["symbol"]),
        as_of=last["time"],
        last_close=float(last["close_price"]),
        target_dates=targets,
        mean=np.exp(pred["yhat"]).tolist(),
        lower=np.exp(pred["yhat_lower"]).tolist(),
        upper=np.exp(pred["yhat_upper"]).tolist(),
    )
