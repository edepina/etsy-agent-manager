from pydantic_settings import BaseSettings
from functools import lru_cache
from datetime import datetime
import os


def _read_password_hash() -> str:
    """Read the admin password hash from a dedicated file, bypassing Docker Compose interpolation."""
    hash_file = os.environ.get("PASSWORD_HASH_FILE", "/app/data/admin_password_hash.txt")
    try:
        with open(hash_file, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return os.environ.get("ADMIN_PASSWORD_HASH", "")


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://edson:password@db:5432/etsy_agents"
    DB_PASSWORD: str = "password"
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    ANTHROPIC_API_KEY: str = ""
    ETSY_API_KEY: str = ""
    ETSY_SHARED_SECRET: str = ""
    SECRET_KEY: str = "change-this-to-a-random-string"
    DEBUG: bool = True

    # Authentication settings
    ADMIN_USERNAME: str = "admin"
    SESSION_SECRET_KEY: str = "change-this-to-a-random-secret"
    SESSION_TIMEOUT_HOURS: int = 24

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def ADMIN_PASSWORD_HASH(self) -> str:
        return _read_password_hash()

    @staticmethod
    def now() -> datetime:
        return datetime.now()


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
