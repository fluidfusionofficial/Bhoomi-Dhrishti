from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "parcel-identity"
    DATABASE_URL: str = "postgresql+asyncpg://bhoomi:bhoomi@postgres:5432/bhoomi"
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_SECRET: str = "change-me-in-production"
    KEYCLOAK_URL: str = "http://keycloak:8080"
    KEYCLOAK_REALM: str = "bhoomi-dhrishti"
    AUDIT_SERVICE_URL: str = "http://audit:8011"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
