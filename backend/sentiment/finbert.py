"""ProsusAI/finbert 로 영문 뉴스 감성을 계산한다.

torch, transformers 는 requirements-ml.txt 에 있다. 호스트 venv 에서 실행해야 MPS 를 쓸 수 있고,
Docker 컨테이너(Linux)에서는 CPU 로 동작한다.
"""

import logging
from functools import lru_cache
from typing import Any

from sentiment.types import SentimentResult, to_score

logger = logging.getLogger(__name__)

MODEL_NAME = "ProsusAI/finbert"
MAX_TOKENS = 256
BATCH_SIZE = 16


class FinBertUnavailableError(RuntimeError):
    pass


def _device() -> str:
    import torch

    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


@lru_cache(maxsize=1)
def _pipeline() -> Any:
    try:
        from transformers import pipeline
    except ImportError as exc:
        raise FinBertUnavailableError("transformers/torch 가 설치되지 않았습니다. requirements-ml.txt 를 설치하세요.") from exc

    device = _device()
    logger.info("FinBERT 로딩 model=%s device=%s", MODEL_NAME, device)
    return pipeline("text-classification", model=MODEL_NAME, device=device, top_k=None, truncation=True, max_length=MAX_TOKENS)


def analyze(texts: list[str]) -> list[SentimentResult]:
    if not texts:
        return []
    outputs = _pipeline()(texts, batch_size=BATCH_SIZE)
    results: list[SentimentResult] = []
    for scores in outputs:
        probs = {item["label"].lower(): float(item["score"]) for item in scores}
        label = max(("positive", "negative", "neutral"), key=lambda k: probs.get(k, 0.0))
        results.append(
            SentimentResult(
                label=label,
                score=to_score(probs.get("positive", 0.0) - probs.get("negative", 0.0)),
                impact=None,
            )
        )
    return results
