from dataclasses import dataclass


@dataclass(frozen=True)
class UniverseItem:
    symbol: str
    name: str
    market: str
    sector: str
    yahoo_ticker: str
    news_query_ko: str
    news_query_en: str


# 운영자가 고른 국내 대표 종목·ETF. 추가·삭제는 여기서 한다.
UNIVERSE: tuple[UniverseItem, ...] = (
    UniverseItem("005930", "삼성전자", "KOSPI", "반도체", "005930.KS", "삼성전자", "Samsung Electronics"),
    UniverseItem("000660", "SK하이닉스", "KOSPI", "반도체", "000660.KS", "SK하이닉스", "SK Hynix"),
    UniverseItem("035420", "NAVER", "KOSPI", "인터넷", "035420.KS", "네이버 주가", "Naver Corp"),
    UniverseItem("005380", "현대차", "KOSPI", "자동차", "005380.KS", "현대차 주가", "Hyundai Motor"),
    UniverseItem("035720", "카카오", "KOSPI", "인터넷", "035720.KS", "카카오 주가", "Kakao Corp"),
    UniverseItem("069500", "KODEX 200", "KOSPI", "ETF", "069500.KS", "코스피200", "KOSPI 200"),
    UniverseItem("229200", "KODEX 코스닥150", "KOSPI", "ETF", "229200.KS", "코스닥150", "KOSDAQ 150"),
)

UNIVERSE_BY_SYMBOL: dict[str, UniverseItem] = {item.symbol: item for item in UNIVERSE}


def resolve(symbols: list[str] | None) -> list[UniverseItem]:
    if not symbols:
        return list(UNIVERSE)
    unknown = [s for s in symbols if s not in UNIVERSE_BY_SYMBOL]
    if unknown:
        raise ValueError(f"유니버스에 없는 종목: {', '.join(unknown)}")
    return [UNIVERSE_BY_SYMBOL[s] for s in symbols]
