import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from schemas.common import fail_body, ok

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)):
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        logger.exception("DB 헬스체크 실패")
        return JSONResponse(status_code=503, content=fail_body("데이터베이스에 연결할 수 없습니다."))
    return ok({"status": "ok", "database": "ok"})
