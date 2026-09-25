from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: str | None = None


def ok(data: T) -> ApiResponse[T]:
    return ApiResponse[T](success=True, data=data, error=None)


def fail_body(message: str) -> dict:
    return {"success": False, "data": None, "error": message}
