from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from repositories import news as news_repo
from schemas.common import ApiResponse, ok
from schemas.news import NewsOut

router = APIRouter(prefix="/news", tags=["news"])


@router.get("", response_model=ApiResponse[list[NewsOut]])
async def list_news(
    symbol: str | None = Query(None, max_length=20),
    limit: int = Query(30, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    rows = await news_repo.list_news(session, symbol, limit)
    return ok([NewsOut.model_validate(r) for r in rows])
