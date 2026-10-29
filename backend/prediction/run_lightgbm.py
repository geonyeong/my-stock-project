"""LightGBM 방향 예측을 학습하고 최신 날짜 기준 예측을 ai_predictions 에 기록한다.

win_probability 에는 horizon 거래일 뒤 종가가 기준일 종가보다 높을 확률(상승 확률)을 저장한다.
미국 국채 금리와 실적 일정 피처는 기본으로 포함한다.
collectors.rates.run, collectors.earnings.run 을 먼저 실행해야 한다.

실행 예:
  docker compose exec backend python -m prediction.run_lightgbm
  docker compose exec backend python -m prediction.run_lightgbm --with-sentiment
  docker compose exec backend python -m prediction.run_lightgbm --no-earnings --evaluate-only  # 실적 일정 제외 비교
"""

import argparse
import asyncio
import logging

from collectors.universe import UNIVERSE
from core.logging import setup_logging
from db.session import SessionLocal, engine
from prediction import lightgbm_model
from prediction.calendar import trading_days_after
from prediction.data import load_candles, load_earnings, load_rates, load_sentiment
from prediction.features import (
    EARNINGS_FEATURES,
    PRICE_FEATURES,
    RATE_FEATURES,
    SENTIMENT_FEATURES,
    build_features,
)
from prediction.writer import PredictionRow, direction_from_prob, to_probability, upsert_predictions

logger = logging.getLogger(__name__)

HORIZON_DAYS = 5
# 감성 이력이 일봉 시작보다 이 일수보다 짧으면 대부분 0이라 최근 구간 표시가 된다.
SENTIMENT_GAP_DAYS = 60


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LightGBM 방향 예측")
    parser.add_argument(
        "--with-sentiment",
        action="store_true",
        help="뉴스 감성 피처 포함. 감성 이력이 학습 기간을 충분히 덮기 전에는 쓰지 않는다.",
    )
    parser.add_argument("--no-rates", action="store_true", help="국채 금리 피처 제외 (비교용)")
    parser.add_argument("--no-earnings", action="store_true", help="실적 일정 피처 제외 (비교용)")
    parser.add_argument("--evaluate-only", action="store_true", help="walk-forward 검증만 하고 모델 저장·예측 기록은 하지 않음")
    return parser.parse_args()


def _require_sentiment_history(candles, sentiment) -> None:
    if sentiment is None or sentiment.empty:
        raise SystemExit("뉴스 감성이 없습니다. collectors.news.run 으로 이력을 쌓은 뒤 다시 실행하세요.")
    first_candle = min(candles["day"])
    first_news = min(sentiment["day"])
    gap_days = (first_news - first_candle).days
    if gap_days > SENTIMENT_GAP_DAYS:
        raise SystemExit(
            f"뉴스 감성 시작({first_news})이 일봉 시작({first_candle})보다 {gap_days}일 늦습니다. "
            "학습 구간을 덮을 때까지 --with-sentiment 를 쓰지 마세요."
        )


def _log_metrics(metrics: list[lightgbm_model.FoldMetric]) -> None:
    for m in metrics:
        logger.info(
            "walk-forward %s~%s n=%d acc=%.3f baseline=%.3f logloss=%.4f",
            m.test_start, m.test_end, m.n_test, m.accuracy, m.baseline_accuracy, m.log_loss,
        )
    if metrics:
        logger.info(
            "walk-forward 평균 acc=%.3f baseline=%.3f logloss=%.4f",
            sum(m.accuracy for m in metrics) / len(metrics),
            sum(m.baseline_accuracy for m in metrics) / len(metrics),
            sum(m.log_loss for m in metrics) / len(metrics),
        )


def _model_name(with_sentiment: bool, with_rates: bool, with_earnings: bool) -> str:
    name = f"lightgbm_dir_{HORIZON_DAYS}d"
    if with_sentiment:
        name += "_sent"
    if not with_rates:
        name += "_norate"
    if not with_earnings:
        name += "_noearn"
    return name


async def _write_predictions(booster, data, features: list[str], model_name: str) -> int:
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


async def run(with_sentiment: bool, with_rates: bool, with_earnings: bool, evaluate_only: bool) -> int:
    symbols = [item.symbol for item in UNIVERSE]
    candles = await load_candles(symbols)
    sentiment = await load_sentiment(symbols) if with_sentiment else None
    if with_sentiment:
        _require_sentiment_history(candles, sentiment)
    rates = await load_rates() if with_rates else None
    earnings = await load_earnings(symbols) if with_earnings else None
    if rates is not None and rates.empty:
        raise SystemExit("국채 금리가 없습니다. collectors.rates.run 을 먼저 실행하세요.")
    if earnings is not None and earnings.empty:
        raise SystemExit("실적 일정이 없습니다. collectors.earnings.run 을 먼저 실행하세요.")

    features = (
        PRICE_FEATURES
        + (SENTIMENT_FEATURES if with_sentiment else [])
        + (RATE_FEATURES if with_rates else [])
        + (EARNINGS_FEATURES if with_earnings else [])
    )
    model_name = _model_name(with_sentiment, with_rates, with_earnings)

    data = build_features(candles, HORIZON_DAYS, sentiment, rates, earnings)
    metrics = lightgbm_model.walk_forward(data, features, HORIZON_DAYS)
    _log_metrics(metrics)
    if evaluate_only:
        return 0

    booster = lightgbm_model.train_final(data, features)
    path = lightgbm_model.save(booster, model_name, features, metrics)
    logger.info("모델 저장 %s", path)
    return await _write_predictions(booster, data, features, model_name)


async def main() -> None:
    args = _parse_args()
    try:
        count = await run(args.with_sentiment, not args.no_rates, not args.no_earnings, args.evaluate_only)
        logger.info("예측 기록 rows=%d", count)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
