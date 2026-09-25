from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from repositories import stocks as stocks_repo
from schemas.common import ApiResponse, ok
from schemas.stock import CandleOut, StockOut

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("", response_model=ApiResponse[list[StockOut]])
async def list_stocks(session: AsyncSession = Depends(get_session)):
    rows = await stocks_repo.list_stocks(session)
    return ok([StockOut.model_validate(r) for r in rows])


@router.get("/{symbol}", response_model=ApiResponse[StockOut])
async def get_stock(symbol: str, session: AsyncSession = Depends(get_session)):
    stock = await stocks_repo.get_stock(session, symbol)
    if stock is None:
        raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다.")
    return ok(StockOut.model_validate(stock))


@router.get("/{symbol}/candles", response_model=ApiResponse[list[CandleOut]])
async def list_daily_candles(
    symbol: str,
    limit: int = Query(120, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
):
    if await stocks_repo.get_stock(session, symbol) is None:
        raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다.")
    rows = await stocks_repo.list_daily_candles(session, symbol, limit)
    return ok([CandleOut.model_validate(r) for r in rows])
