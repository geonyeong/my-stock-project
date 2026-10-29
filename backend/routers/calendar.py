from fastapi import APIRouter

from prediction.holidays import HOLIDAY_LIST_END, KRX_CLOSED_DAYS
from schemas.common import ApiResponse, ok

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/holidays", response_model=ApiResponse[list[str]])
async def list_holidays():
    """화면이 5거래일 구간을 계산할 때 쓰는 휴장일. 주말은 포함하지 않는다."""
    days = sorted(day.isoformat() for day in KRX_CLOSED_DAYS if day <= HOLIDAY_LIST_END)
    return ok(days)
