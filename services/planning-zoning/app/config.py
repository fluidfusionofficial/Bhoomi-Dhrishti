from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    SERVICE_NAME: str = "planning-zoning"
    PORT: int = 8005
    DATABASE_URL: str = "postgresql+asyncpg://bhoomi:bhoomi@postgres:5432/bhoomi"
    AUDIT_SERVICE_URL: str = "http://audit:8011"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
