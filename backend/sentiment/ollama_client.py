"""로컬 Ollama 로 국내 뉴스의 감성과 주가 영향도를 평가한다."""

import json
import logging
import time

import httpx

from core.config import get_settings
from sentiment.types import LABELS, SentimentResult, to_score

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SEC = 120.0
MAX_RETRIES = 2
RETRY_BACKOFF_SEC = 2.0

SYSTEM_PROMPT = (
    "너는 한국 주식시장 뉴스 분석가다. 주어진 뉴스가 해당 종목 주가에 주는 영향을 평가한다. "
    '반드시 JSON 한 개만 출력한다: {"label": "positive|negative|neutral", '
    '"score": -1.0~1.0 사이 실수(부정은 음수), "impact": 0.0~1.0 사이 실수(주가 영향 크기)}'
)


class OllamaUnavailableError(RuntimeError):
    pass


def _parse(content: str) -> SentimentResult:
    payload = json.loads(content)
    label = str(payload.get("label", "neutral")).lower()
    if label not in LABELS:
        label = "neutral"
    return SentimentResult(
        label=label,
        score=to_score(float(payload.get("score", 0.0))),
        impact=to_score(float(payload.get("impact", 0.0)), low=0.0, high=1.0),
    )


def _chat(client: httpx.Client, user_prompt: str) -> str:
    settings = get_settings()
    body = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "format": "json",
        "stream": False,
        "think": False,
        "options": {"temperature": 0},
    }
    res = client.post(f"{settings.ollama_url}/api/chat", json=body)
    res.raise_for_status()
    return res.json()["message"]["content"]


def analyze(client: httpx.Client, stock_name: str, title: str, summary: str | None) -> SentimentResult:
    user_prompt = f"종목: {stock_name}\n제목: {title}\n요약: {summary or '-'}"
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return _parse(_chat(client, user_prompt))
        except httpx.ConnectError as exc:
            raise OllamaUnavailableError(f"Ollama 서버에 연결할 수 없습니다: {get_settings().ollama_url}") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise OllamaUnavailableError(f"Ollama 에 모델이 없습니다: {get_settings().ollama_model}") from exc
            last_error = exc
            logger.warning("Ollama 감성 평가 실패 attempt=%d/%d: %s", attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SEC * attempt)
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            last_error = exc
            logger.warning("Ollama 감성 평가 실패 attempt=%d/%d: %s", attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SEC * attempt)
    raise RuntimeError(f"Ollama 감성 평가가 {MAX_RETRIES}회 모두 실패했습니다.") from last_error


def new_client() -> httpx.Client:
    return httpx.Client(timeout=REQUEST_TIMEOUT_SEC)
