from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://edson:password@db:5432/etsy_agents"
    DB_PASSWORD: str = "password"
    REDIS_URL: str = "redis://redis:6379/0"
    ANTHROPIC_API_KEY: str = ""
    ETSY_API_KEY: str = ""
    ETSY_SHARED_SECRET: str = ""
    SECRET_KEY: str = "change-this-to-a-random-string"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
