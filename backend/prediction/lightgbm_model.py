"""LightGBM 으로 horizon 거래일 뒤 상승 확률을 예측한다.

모든 종목을 한 모델로 학습한다(종목 수가 적어 종목별 모델은 표본이 부족하다).
검증은 날짜 순 walk-forward 이고, 라벨 누수를 막으려고 학습 구간과 검증 구간 사이에 horizon 만큼 간격을 둔다.
"""

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "artifacts"
PARAMS = {
    "objective": "binary",
    "learning_rate": 0.03,
    "num_leaves": 15,
    "min_data_in_leaf": 40,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "lambda_l2": 1.0,
    "verbose": -1,
    "seed": 42,
}
NUM_BOOST_ROUND = 300
N_FOLDS = 4
FOLD_DAYS = 60


@dataclass
class FoldMetric:
    test_start: str
    test_end: str
    n_test: int
    accuracy: float
    baseline_accuracy: float
    log_loss: float


def _log_loss(y: np.ndarray, p: np.ndarray) -> float:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def _fit(train: pd.DataFrame, features: list[str]) -> lgb.Booster:
    dataset = lgb.Dataset(train[features], label=train["label"])
    return lgb.train(PARAMS, dataset, num_boost_round=NUM_BOOST_ROUND)


def walk_forward(data: pd.DataFrame, features: list[str], horizon: int) -> list[FoldMetric]:
    labeled = data.dropna(subset=["label"])
    days = np.array(sorted(labeled["day"].unique()))
    metrics: list[FoldMetric] = []
    for k in range(N_FOLDS, 0, -1):
        test_days = days[len(days) - k * FOLD_DAYS : len(days) - (k - 1) * FOLD_DAYS]
        if len(test_days) == 0 or len(days) - k * FOLD_DAYS - horizon <= 0:
            continue
        train_cutoff = days[len(days) - k * FOLD_DAYS - horizon]
        train = labeled[labeled["day"] < train_cutoff]
        test = labeled[labeled["day"].isin(test_days)]
        prob = _fit(train, features).predict(test[features])
        y = test["label"].to_numpy()
        majority = float(train["label"].mean() >= 0.5)
        metrics.append(
            FoldMetric(
                test_start=str(test_days[0]),
                test_end=str(test_days[-1]),
                n_test=len(test),
                accuracy=float(np.mean((prob >= 0.5) == y)),
                baseline_accuracy=float(np.mean(y == majority)),
                log_loss=_log_loss(y, prob),
            )
        )
    return metrics


def train_final(data: pd.DataFrame, features: list[str]) -> lgb.Booster:
    return _fit(data.dropna(subset=["label"]), features)


def predict_latest(booster: lgb.Booster, data: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """종목별 가장 최근 날짜 행에 대해 상승 확률을 계산한다."""
    latest = data.sort_values("day").groupby("symbol").tail(1).copy()
    latest["prob_up"] = booster.predict(latest[features])
    return latest


def save(booster: lgb.Booster, model_name: str, features: list[str], metrics: list[FoldMetric]) -> Path:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    model_path = ARTIFACT_DIR / f"{model_name}.txt"
    booster.save_model(str(model_path))
    meta = {"features": features, "params": PARAMS, "walk_forward": [asdict(m) for m in metrics]}
    (ARTIFACT_DIR / f"{model_name}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    return model_path
