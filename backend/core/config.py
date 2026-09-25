import os
from dataclasses import dataclass, field
from functools import lru_cache


def _async_database_url(url: str) -> str:
    # compose 는 libpq 형식(postgresql://)을 주므로 asyncpg 드라이버 형식으로 바꾼다.
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    database_url: str
    redis_url: str
    ollama_url: str
    ollama_model: str
    cors_origins: list[str] = field(default_factory=list)


@lru_cache
def get_settings() -> Settings:
    return Settings(
        database_url=_async_database_url(
            os.environ.get("DATABASE_URL", "postgresql://stockuser:stockpassword@localhost:5432/stockdb")
        ),
        redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        ollama_url=os.environ.get("OLLAMA_URL", "http://localhost:11434"),
        ollama_model=os.environ.get("OLLAMA_MODEL", "qwen3:8b"),
        cors_origins=_split_csv(os.environ.get("CORS_ORIGINS", "http://localhost:3000")),
    )
