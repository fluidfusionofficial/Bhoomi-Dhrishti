from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "geospatial"
    DATABASE_URL: str = "postgresql+asyncpg://bhoomi:bhoomi@postgres:5432/bhoomi"
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_SECRET: str = "change-me-in-production"
    KEYCLOAK_URL: str = "http://keycloak:8080"
    KEYCLOAK_REALM: str = "bhoomi-dhrishti"
    AUDIT_SERVICE_URL: str = "http://audit:8011"
    LOG_LEVEL: str = "INFO"
    # Tile cache: seconds to keep MVT tiles in Cache-Control headers
    TILE_CACHE_MAX_AGE: int = 300
    # Maximum zoom level enforced at the endpoint
    TILE_MAX_ZOOM: int = 22

    class Config:
        env_file = ".env"


settings = Settings()
