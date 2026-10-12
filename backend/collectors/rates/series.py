from dataclasses import dataclass
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class RateSeries:
    code: str
    name: str
    yahoo_ticker: str
    timezone: ZoneInfo


NEW_YORK = ZoneInfo("America/New_York")

# Yahoo 지수는 수익률을 % 단위로 준다(예: 4.25 = 4.25%). ^IRX 는 13주 T-bill 할인율이다.
RATE_SERIES: tuple[RateSeries, ...] = (
    RateSeries("US3M", "미국 3개월 T-bill", "^IRX", NEW_YORK),
    RateSeries("US5Y", "미국 5년 국채", "^FVX", NEW_YORK),
    RateSeries("US10Y", "미국 10년 국채", "^TNX", NEW_YORK),
)

RATE_SERIES_BY_CODE: dict[str, RateSeries] = {s.code: s for s in RATE_SERIES}
