"""Prophet 추세 또는 DLinear 경로를 계산해 ai_predictions 에 목표일별로 기록한다.

prophet, torch 는 requirements-ml.txt 에 있다. MPS 를 쓰려면 호스트 venv 에서 실행한다.

실행 예 (backend 디렉터리, .venv 활성화 후):
  python -m prediction.run_forecast --model prophet
  python -m prediction.run_forecast --model dlinear --horizon 10
"""

import argparse
import asyncio
import logging

from collectors.universe import UNIVERSE
from core.logging import setup_logging
from db.session import SessionLocal, engine
from prediction import dlinear_model, prophet_model
from prediction.data import load_candles
from prediction.forecast import ForecastPath, to_rows
from prediction.writer import upsert_predictions

logger = logging.getLogger(__name__)

DEFAULT_HORIZON = 10
MISSING_DEPENDENCY_ERRORS = (prophet_model.ProphetUnavailableError, dlinear_model.TorchUnavailableError)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="가격 경로 예측")
    parser.add_argument("--model", choices=["prophet", "dlinear"], required=True)
    parser.add_argument("--horizon", type=int, default=DEFAULT_HORIZON, choices=range(5, 11), metavar="5~10")
    return parser.parse_args()


def _prophet_paths(candles, horizon: int) -> list[ForecastPath]:
    paths: list[ForecastPath] = []
    for symbol, g in candles.groupby("symbol", sort=False):
        try:
            paths.append(prophet_model.forecast_symbol(g, horizon))
        except prophet_model.ProphetUnavailableError:
            raise
        except Exception:
            logger.exception("Prophet 예측 실패 symbol=%s", symbol)
    return paths


async def run(model: str, horizon: int) -> int:
    candles = await load_candles([item.symbol for item in UNIVERSE])
    if model == "prophet":
        paths = await asyncio.to_thread(_prophet_paths, candles, horizon)
    else:
        paths = await asyncio.to_thread(dlinear_model.forecast_all, candles, horizon)
    rows = [row for path in paths for row in to_rows(path, model)]
    async with SessionLocal() as session:
        return await upsert_predictions(session, rows)


async def main() -> None:
    args = _parse_args()
    try:
        count = await run(args.model, args.horizon)
        logger.info("경로 예측 기록 model=%s rows=%d", args.model, count)
    except MISSING_DEPENDENCY_ERRORS as exc:
        raise SystemExit(str(exc)) from None
    finally:
        await engine.dispose()


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
