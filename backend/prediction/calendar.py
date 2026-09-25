from datetime import date

import pandas as pd


def trading_days_after(last_day: date, n: int) -> list[date]:
    """last_day 다음 평일 n 개. 한국 공휴일은 반영하지 않는다."""
    days = pd.bdate_range(start=pd.Timestamp(last_day) + pd.Timedelta(days=1), periods=n)
    return [d.date() for d in days]
