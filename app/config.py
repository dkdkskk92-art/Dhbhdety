from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_URL: str
    WEBAPP_URL: str = https://bot-1795241907-1794-ayzen.bothost.tech"
    START_SPARKS: int = 10
    PVP_WAIT_MINUTES: int = 10

    @field_validator("DATABASE_URL")
    @classmethod
    def _force_asyncpg(cls, v: str) -> str:
        if v.startswith("postgresql://") or v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1).replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        return v

    class Config:
        env_file = ".env"

settings = Settings()
