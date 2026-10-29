from datetime import date

import numpy as np
import pandas as pd

from prediction.calendar import trading_days_after

PRICE_FEATURES = [
    "ret_1",
    "ret_5",
    "ret_10",
    "ret_20",
    "ma_ratio_5",
    "ma_ratio_20",
    "ma_ratio_60",
    "rsi_14",
    "volatility_20",
    "volume_ratio_20",
    "hl_range",
]
SENTIMENT_FEATURES = ["sentiment_mean_5", "news_count_5"]
# 단위는 %p. 변화량은 미국 거래일 기준 n 영업일 전 대비.
RATE_FEATURES = ["us10y_chg_5", "us10y_chg_20", "us3m_chg_20", "us_spread_10y_3m"]
# 실적 수치는 발표 뒤에야 알 수 있어 일정 여부만 쓴다.
EARNINGS_FEATURES = ["earnings_in_horizon"]
# 60일 이동평균이 채워져야 피처가 유효하다.
WARMUP_DAYS = 60


def candles_frame(rows: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    for col in ["open_price", "high_price", "low_price", "close_price"]:
        frame[col] = frame[col].astype(float)
    frame["volume"] = frame["volume"].astype(float)
    frame["day"] = pd.to_datetime(frame["time"]).dt.tz_convert("Asia/Seoul").dt.date
    return frame.sort_values(["symbol", "day"]).reset_index(drop=True)


def _rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(100.0).where(loss.notna())


def _price_features(g: pd.DataFrame) -> pd.DataFrame:
    close = g["close_price"]
    daily_ret = close.pct_change()
    out = pd.DataFrame(index=g.index)
    for n in (1, 5, 10, 20):
        out[f"ret_{n}"] = close.pct_change(n)
    for n in (5, 20, 60):
        out[f"ma_ratio_{n}"] = close / close.rolling(n).mean() - 1
    out["rsi_14"] = _rsi(close) / 100
    out["volatility_20"] = daily_ret.rolling(20).std()
    out["volume_ratio_20"] = g["volume"] / g["volume"].rolling(20).mean()
    out["hl_range"] = (g["high_price"] - g["low_price"]) / close
    return out


def _sentiment_features(g: pd.DataFrame, sentiment: pd.DataFrame) -> pd.DataFrame:
    merged = g[["symbol", "day"]].merge(sentiment, on=["symbol", "day"], how="left")
    merged.index = g.index
    score_sum = (merged["sentiment_mean"].fillna(0) * merged["news_count"].fillna(0)).rolling(5, min_periods=1).sum()
    count = merged["news_count"].fillna(0).rolling(5, min_periods=1).sum()
    return pd.DataFrame(
        {"sentiment_mean_5": (score_sum / count.replace(0, np.nan)).fillna(0.0), "news_count_5": count},
        index=g.index,
    )


def _rate_series_features(rates: pd.DataFrame) -> pd.DataFrame:
    """미국 거래일(rate_day) 단위로 금리 피처를 계산한다."""
    wide = rates.sort_values("rate_day").set_index("rate_day").ffill()
    out = pd.DataFrame(index=wide.index)
    out["us10y_chg_5"] = wide["US10Y"].diff(5)
    out["us10y_chg_20"] = wide["US10Y"].diff(20)
    out["us3m_chg_20"] = wide["US3M"].diff(20)
    out["us_spread_10y_3m"] = wide["US10Y"] - wide["US3M"]
    return out.reset_index()


def _attach_rates(g: pd.DataFrame, rate_feats: pd.DataFrame) -> pd.DataFrame:
    """한국 거래일 D 에는 미국 거래일 D-1 이하 값만 붙인다.

    미국 장 마감(뉴욕 16시)은 한국 시각 다음 날 새벽이라, 같은 날짜 값을 쓰면 미래 정보가 섞인다.
    """
    left = pd.DataFrame({"kr_day": pd.to_datetime(g["day"]), "_idx": g.index}).sort_values("kr_day")
    right = rate_feats.assign(rate_day=pd.to_datetime(rate_feats["rate_day"])).sort_values("rate_day")
    merged = pd.merge_asof(left, right, left_on="kr_day", right_on="rate_day", allow_exact_matches=False)
    return merged.set_index("_idx")[RATE_FEATURES].reindex(g.index)


def _attach_earnings(g: pd.DataFrame, events: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """기준일 D 다음 거래일부터 목표일까지 실적 발표가 있으면 1.

    당일 발표는 빼 둔다. 장중·장후 시각을 알 수 없어 그날 종가에 이미 반영됐을 수 있다.
    yfinance 는 일정이 공지된 시점을 주지 않으므로, 과거 구간은 실제 발표일을 그 전부터 알려진 일정으로 본다.
    """
    symbol = g["symbol"].iloc[0]
    event_days = sorted(events.loc[events["symbol"] == symbol, "event_day"].unique())
    flags = [_earnings_flag(day, event_days, horizon) for day in g["day"]]
    return pd.DataFrame({"earnings_in_horizon": flags}, index=g.index)


def _earnings_flag(day: date, event_days: list[date], horizon: int) -> float:
    if not event_days:
        return 0.0
    target = trading_days_after(day, horizon)[-1]
    return 1.0 if any(day < event <= target for event in event_days) else 0.0


def build_features(
    candles: pd.DataFrame,
    horizon: int,
    sentiment: pd.DataFrame | None = None,
    rates: pd.DataFrame | None = None,
    earnings: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """종목별 피처와 horizon 거래일 뒤 상승 여부 라벨을 만든다. 최신 행은 라벨이 NaN 이다."""
    rate_feats = _rate_series_features(rates) if rates is not None else None
    parts: list[pd.DataFrame] = []
    for _, g in candles.groupby("symbol", sort=False):
        feats = _price_features(g)
        if sentiment is not None:
            feats = feats.join(_sentiment_features(g, sentiment))
        if rate_feats is not None:
            feats = feats.join(_attach_rates(g, rate_feats))
        if earnings is not None:
            feats = feats.join(_attach_earnings(g, earnings, horizon))
        future_ret = g["close_price"].shift(-horizon) / g["close_price"] - 1
        feats["label"] = (future_ret > 0).astype(float).where(future_ret.notna())
        feats[["symbol", "day", "time", "close_price"]] = g[["symbol", "day", "time", "close_price"]]
        parts.append(feats.iloc[WARMUP_DAYS:])
    return pd.concat(parts).reset_index(drop=True) if parts else pd.DataFrame()


def sentiment_frame(rows: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=["symbol", "day", "sentiment_mean", "news_count"])
    frame["sentiment_mean"] = frame["sentiment_mean"].astype(float)
    frame["news_count"] = frame["news_count"].astype(float)
    return frame


def earnings_frame(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["symbol", "event_day"])
    frame = pd.DataFrame(rows)
    frame["event_day"] = pd.to_datetime(frame["time"]).dt.tz_convert("Asia/Seoul").dt.date
    return frame[["symbol", "event_day"]].drop_duplicates()


def rates_frame(rows: list[dict]) -> pd.DataFrame:
    """series_code 별 행을 미국 거래일(rate_day) × 시리즈 열로 펼친다."""
    if not rows:
        return pd.DataFrame(columns=["rate_day"])
    frame = pd.DataFrame(rows)
    frame["rate_day"] = pd.to_datetime(frame["time"]).dt.tz_convert("America/New_York").dt.date
    frame["value"] = frame["value"].astype(float)
    wide = frame.pivot_table(index="rate_day", columns="series_code", values="value", aggfunc="last")
    return wide.reset_index()
