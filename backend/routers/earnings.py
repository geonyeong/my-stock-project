from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from repositories import earnings as earnings_repo
from repositories import stocks as stocks_repo
from schemas.common import ApiResponse, ok
from schemas.earnings import EarningsOut

router = APIRouter(tags=["earnings"])
KST = ZoneInfo("Asia/Seoul")


def _today_start() -> datetime:
    now = datetime.now(KST)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


@router.get("/earnings/upcoming", response_model=ApiResponse[list[EarningsOut]])
async def upcoming_earnings(
    limit: int = Query(100, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    rows = await earnings_repo.list_upcoming(session, _today_start(), limit)
    return ok([EarningsOut.model_validate(row) for row in rows])


@router.get("/stocks/{symbol}/earnings", response_model=ApiResponse[list[EarningsOut]])
async def symbol_earnings(
    symbol: str,
    limit: int = Query(12, ge=1, le=48),
    session: AsyncSession = Depends(get_session),
):
    if await stocks_repo.get_stock(session, symbol) is None:
        raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다.")
    rows = await earnings_repo.list_for_symbol(session, symbol, limit)
    return ok([EarningsOut.model_validate(row) for row in rows])
