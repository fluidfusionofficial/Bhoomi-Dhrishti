from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://bhoomi:bhoomi@postgres:5432/bhoomi"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str = "changeme"
    keycloak_url: str = "http://keycloak:8080"
    keycloak_realm: str = "bhoomi-dhrishti"
    audit_service_url: str = "http://audit:8011"
    service_name: str = "search"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
