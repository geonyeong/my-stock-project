from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from repositories import predictions as predictions_repo
from repositories import stocks as stocks_repo
from schemas.common import ApiResponse, ok
from schemas.prediction import PredictionOut

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/{symbol}", response_model=ApiResponse[list[PredictionOut]])
async def list_latest_predictions(symbol: str, session: AsyncSession = Depends(get_session)):
    if await stocks_repo.get_stock(session, symbol) is None:
        raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다.")
    rows = await predictions_repo.list_latest_predictions(session, symbol)
    return ok([PredictionOut.model_validate(r) for r in rows])
