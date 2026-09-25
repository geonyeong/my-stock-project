"""DLinear 로 과거 60거래일 종가 패턴에서 향후 경로를 추정한다. torch 는 requirements-ml.txt 에 있다.

모든 종목이 가중치를 공유한다. 입력 창의 마지막 종가로 나눈 상대 변화율을 학습해 종목 간 가격 수준 차이를 없앤다.
구간은 검증 구간 잔차의 시점별 표준편차로 만든다(80%).
"""

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from prediction.calendar import trading_days_after
from prediction.forecast import Z_80, ForecastPath

logger = logging.getLogger(__name__)

INPUT_DAYS = 60
MA_KERNEL = 25
VAL_RATIO = 0.15
MAX_EPOCHS = 60
PATIENCE = 6
BATCH_SIZE = 128
LEARNING_RATE = 1e-3
SEED = 42


class TorchUnavailableError(RuntimeError):
    pass


@dataclass
class Windows:
    x: np.ndarray
    y: np.ndarray
    end_day: np.ndarray


def _torch():
    try:
        import torch
    except ImportError as exc:
        raise TorchUnavailableError("torch 가 설치되지 않았습니다. requirements-ml.txt 를 설치하세요.") from exc
    return torch


def _device(torch) -> str:
    return "mps" if torch.backends.mps.is_available() else "cpu"


def _build_model(torch, horizon: int):
    nn = torch.nn

    class DLinear(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.pool = nn.AvgPool1d(MA_KERNEL, stride=1)
            self.trend = nn.Linear(INPUT_DAYS, horizon)
            self.seasonal = nn.Linear(INPUT_DAYS, horizon)

        def forward(self, x):
            pad = (MA_KERNEL - 1) // 2
            padded = torch.cat([x[:, :1].repeat(1, pad), x, x[:, -1:].repeat(1, MA_KERNEL - 1 - pad)], dim=1)
            trend = self.pool(padded.unsqueeze(1)).squeeze(1)
            return self.trend(trend) + self.seasonal(x - trend)

    return DLinear()


def _make_windows(candles: pd.DataFrame, horizon: int) -> Windows:
    xs, ys, ends = [], [], []
    for _, g in candles.groupby("symbol", sort=False):
        close = g["close_price"].to_numpy(dtype=np.float64)
        days = g["day"].to_numpy()
        for i in range(INPUT_DAYS, len(close) - horizon + 1):
            base = close[i - 1]
            xs.append(close[i - INPUT_DAYS : i] / base - 1)
            ys.append(close[i : i + horizon] / base - 1)
            ends.append(days[i + horizon - 1])
    return Windows(np.asarray(xs, np.float32), np.asarray(ys, np.float32), np.asarray(ends))


def _split(w: Windows) -> tuple[Windows, Windows]:
    cutoff = np.sort(w.end_day)[int(len(w.end_day) * (1 - VAL_RATIO))]
    train, val = w.end_day < cutoff, w.end_day >= cutoff
    return Windows(w.x[train], w.y[train], w.end_day[train]), Windows(w.x[val], w.y[val], w.end_day[val])


def _train(torch, train: Windows, val: Windows, horizon: int):
    torch.manual_seed(SEED)
    device = _device(torch)
    model = _build_model(torch, horizon).to(device)
    optim = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    loss_fn = torch.nn.MSELoss()
    x_tr, y_tr = torch.from_numpy(train.x).to(device), torch.from_numpy(train.y).to(device)
    x_va, y_va = torch.from_numpy(val.x).to(device), torch.from_numpy(val.y).to(device)

    best_loss, best_state, stale = float("inf"), None, 0
    for epoch in range(MAX_EPOCHS):
        model.train()
        for idx in torch.randperm(len(x_tr), device=device).split(BATCH_SIZE):
            optim.zero_grad()
            loss_fn(model(x_tr[idx]), y_tr[idx]).backward()
            optim.step()
        model.eval()
        with torch.no_grad():
            val_loss = loss_fn(model(x_va), y_va).item()
        if val_loss < best_loss:
            best_loss, stale = val_loss, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            stale += 1
            if stale >= PATIENCE:
                break
    logger.info("DLinear 학습 종료 epoch=%d best_val_mse=%.6f device=%s", epoch + 1, best_loss, device)
    model.load_state_dict(best_state)
    return model


def _predict(torch, model, x: np.ndarray) -> np.ndarray:
    device = next(model.parameters()).device
    with torch.no_grad():
        return model(torch.from_numpy(x).to(device)).cpu().numpy()


def forecast_all(candles: pd.DataFrame, horizon: int) -> list[ForecastPath]:
    torch = _torch()
    train, val = _split(_make_windows(candles, horizon))
    model = _train(torch, train, val, horizon)
    resid_std = (_predict(torch, model, val.x) - val.y).std(axis=0)

    paths: list[ForecastPath] = []
    for symbol, g in candles.groupby("symbol", sort=False):
        if len(g) < INPUT_DAYS:
            continue
        close = g["close_price"].to_numpy(dtype=np.float64)
        base = close[-1]
        x = (close[-INPUT_DAYS:] / base - 1).astype(np.float32)[None, :]
        rel = _predict(torch, model, x)[0]
        last = g.iloc[-1]
        paths.append(
            ForecastPath(
                symbol=str(symbol),
                as_of=last["time"],
                last_close=float(base),
                target_dates=trading_days_after(last["day"], horizon),
                mean=(base * (1 + rel)).tolist(),
                lower=(base * (1 + rel - Z_80 * resid_std)).tolist(),
                upper=(base * (1 + rel + Z_80 * resid_std)).tolist(),
            )
        )
    return paths
