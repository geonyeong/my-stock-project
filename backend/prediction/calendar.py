from datetime import date, timedelta

from prediction.holidays import KRX_CLOSED_DAYS


def is_krx_session(day: date) -> bool:
    """주말과 등록된 한국거래소 휴장일이 아니면 거래일로 본다."""
    return day.weekday() < 5 and day not in KRX_CLOSED_DAYS


def trading_days_after(last_day: date, n: int) -> list[date]:
    """last_day 다음 한국거래소 거래일 n 개. 등록된 휴장일은 건너뛴다."""
    found: list[date] = []
    cursor = last_day
    while len(found) < n:
        cursor += timedelta(days=1)
        if is_krx_session(cursor):
            found.append(cursor)
    return found
