import logging

from collectors.news.google_rss import RawArticle
from sentiment import finbert, ollama_client
from sentiment.types import SentimentResult

logger = logging.getLogger(__name__)


class SentimentService:
    """언어별 모델로 감성을 매긴다. 쓸 수 없는 모델은 한 번 경고하고 해당 언어를 건너뛴다."""

    def __init__(self) -> None:
        self._ollama = ollama_client.new_client()
        self._disabled: set[str] = set()

    def close(self) -> None:
        self._ollama.close()

    def score(self, stock_name: str, articles: list[RawArticle]) -> list[tuple[RawArticle, SentimentResult]]:
        ko = [a for a in articles if a.language == "ko"]
        en = [a for a in articles if a.language == "en"]
        return self._score_ko(stock_name, ko) + self._score_en(en)

    def _score_ko(self, stock_name: str, articles: list[RawArticle]) -> list[tuple[RawArticle, SentimentResult]]:
        if not articles or "ko" in self._disabled:
            return []
        scored: list[tuple[RawArticle, SentimentResult]] = []
        for article in articles:
            try:
                scored.append((article, ollama_client.analyze(self._ollama, stock_name, article.title, article.summary)))
            except ollama_client.OllamaUnavailableError as exc:
                logger.warning("국내 뉴스 감성 비활성화: %s", exc)
                self._disabled.add("ko")
                break
            except RuntimeError:
                logger.exception("감성 평가 실패, 기사 건너뜀 url=%s", article.url)
        return scored

    def _score_en(self, articles: list[RawArticle]) -> list[tuple[RawArticle, SentimentResult]]:
        if not articles or "en" in self._disabled:
            return []
        try:
            results = finbert.analyze([a.title for a in articles])
        except finbert.FinBertUnavailableError as exc:
            logger.warning("영문 뉴스 감성 비활성화: %s", exc)
            self._disabled.add("en")
            return []
        return list(zip(articles, results, strict=True))
