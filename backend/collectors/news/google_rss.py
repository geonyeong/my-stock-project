import logging
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Literal

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

Language = Literal["ko", "en"]

RSS_URL = "https://news.google.com/rss/search"
LOCALE_PARAMS: dict[Language, dict[str, str]] = {
    "ko": {"hl": "ko", "gl": "KR", "ceid": "KR:ko"},
    "en": {"hl": "en-US", "gl": "US", "ceid": "US:en"},
}
REQUEST_TIMEOUT_SEC = 15.0
MAX_RETRIES = 3
RETRY_BACKOFF_SEC = 2.0
SOURCE_MAX_LEN = 50
SUMMARY_MAX_LEN = 1000


@dataclass(frozen=True)
class RawArticle:
    time: datetime
    title: str
    url: str
    source: str
    summary: str | None
    language: Language


def _get(client: httpx.Client, params: dict[str, str]) -> str:
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            res = client.get(RSS_URL, params=params)
            res.raise_for_status()
            return res.text
        except httpx.HTTPError as exc:
            last_error = exc
            logger.warning("RSS 요청 실패 q=%s attempt=%d/%d: %s", params.get("q"), attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SEC * attempt)
    raise RuntimeError(f"RSS 요청이 {MAX_RETRIES}회 모두 실패했습니다.") from last_error


def _strip_source_suffix(title: str, source: str) -> str:
    suffix = f" - {source}"
    return title[: -len(suffix)] if source and title.endswith(suffix) else title


def _parse(xml_text: str, language: Language) -> list[RawArticle]:
    articles: list[RawArticle] = []
    for item in ET.fromstring(xml_text).iter("item"):
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        pub_date = item.findtext("pubDate")
        if not title or not url or not pub_date:
            continue
        source = (item.findtext("source") or "google_news").strip()
        description = item.findtext("description")
        summary = BeautifulSoup(description, "html.parser").get_text(" ", strip=True) if description else None
        articles.append(
            RawArticle(
                time=parsedate_to_datetime(pub_date),
                title=_strip_source_suffix(title, source),
                url=url,
                source=source[:SOURCE_MAX_LEN],
                summary=summary[:SUMMARY_MAX_LEN] if summary else None,
                language=language,
            )
        )
    return articles


def fetch_articles(query: str, language: Language, limit: int) -> list[RawArticle]:
    """Google News RSS 검색 결과를 최신순으로 limit 개까지 돌려준다."""
    params = {"q": f"{query} when:7d", **LOCALE_PARAMS[language]}
    with httpx.Client(timeout=REQUEST_TIMEOUT_SEC, follow_redirects=True) as client:
        xml_text = _get(client, params)
    articles = sorted(_parse(xml_text, language), key=lambda a: a.time, reverse=True)
    return articles[:limit]
