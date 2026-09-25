"""LightGBM 방향 예측을 학습하고 최신 날짜 기준 예측을 ai_predictions 에 기록한다.

win_probability 에는 horizon 거래일 뒤 종가가 기준일 종가보다 높을 확률(상승 확률)을 저장한다.

실행 예:
  docker compose exec backend python -m prediction.run_lightgbm
  docker compose exec backend python -m prediction.run_lightgbm --with-sentiment
"""

import argparse
import asyncio
import logging

from collectors.universe import UNIVERSE
from core.logging import setup_logging
from db.session import SessionLocal, engine
from prediction import lightgbm_model
from prediction.calendar import trading_days_after
from prediction.data import load_candles, load_sentiment
from prediction.features import PRICE_FEATURES, SENTIMENT_FEATURES, build_features
from prediction.writer import PredictionRow, direction_from_prob, to_probability, upsert_predictions

logger = logging.getLogger(__name__)

HORIZON_DAYS = 5


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LightGBM 방향 예측")
    parser.add_argument(
        "--with-sentiment",
        action="store_true",
        help="뉴스 감성 피처 포함. 감성 이력이 학습 기간을 충분히 덮기 전에는 쓰지 않는다.",
    )
    return parser.parse_args()


def _log_metrics(metrics: list[lightgbm_model.FoldMetric]) -> None:
    for m in metrics:
        logger.info(
            "walk-forward %s~%s n=%d acc=%.3f baseline=%.3f logloss=%.4f",
            m.test_start, m.test_end, m.n_test, m.accuracy, m.baseline_accuracy, m.log_loss,
        )


async def run(with_sentiment: bool) -> int:
    symbols = [item.symbol for item in UNIVERSE]
    candles = await load_candles(symbols)
    sentiment = await load_sentiment(symbols) if with_sentiment else None
    features = PRICE_FEATURES + (SENTIMENT_FEATURES if with_sentiment else [])
    model_name = f"lightgbm_dir_{HORIZON_DAYS}d" + ("_sent" if with_sentiment else "")

    data = build_features(candles, HORIZON_DAYS, sentiment)
    metrics = lightgbm_model.walk_forward(data, features, HORIZON_DAYS)
    _log_metrics(metrics)

    booster = lightgbm_model.train_final(data, features)
    path = lightgbm_model.save(booster, model_name, features, metrics)
    logger.info("모델 저장 %s", path)

    latest = lightgbm_model.predict_latest(booster, data, features)
    rows = [
        PredictionRow(
            time=r.time,
            symbol=r.symbol,
            target_date=trading_days_after(r.day, HORIZON_DAYS)[-1],
            model_name=model_name,
            direction_signal=direction_from_prob(r.prob_up),
            win_probability=to_probability(r.prob_up),
        )
        for r in latest.itertuples()
    ]
    async with SessionLocal() as session:
        return await upsert_predictions(session, rows)


async def main() -> None:
    args = _parse_args()
    try:
        count = await run(args.with_sentiment)
        logger.info("예측 기록 rows=%d", count)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
