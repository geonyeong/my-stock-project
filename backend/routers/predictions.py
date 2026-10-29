from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from prediction.lightgbm_model import load_evaluation
from repositories import predictions as predictions_repo
from repositories import stocks as stocks_repo
from schemas.common import ApiResponse, ok
from schemas.prediction import PredictionOut, WalkForwardOut

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/{symbol}", response_model=ApiResponse[list[PredictionOut]])
async def list_latest_predictions(symbol: str, session: AsyncSession = Depends(get_session)):
    if await stocks_repo.get_stock(session, symbol) is None:
        raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다.")
    rows = await predictions_repo.list_latest_predictions(session, symbol)
    payloads = [PredictionOut.model_validate(row) for row in rows]
    cached: dict[str, WalkForwardOut | None] = {}
    for item in payloads:
        if not item.model_name.startswith("lightgbm"):
            continue
        if item.model_name not in cached:
            summary = load_evaluation(item.model_name)
            cached[item.model_name] = WalkForwardOut.model_validate(summary) if summary else None
        item.evaluation = cached[item.model_name]
    return ok(payloads)
