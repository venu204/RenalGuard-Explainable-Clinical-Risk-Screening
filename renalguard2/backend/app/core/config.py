from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATABASE_URL = f"sqlite:///{(PROJECT_ROOT / 'renalguard.db').as_posix()}"

class Settings(BaseSettings):
    # SQLite keeps the academic project self-contained. Set DATABASE_URL in .env
    # only when deliberately deploying it with another database provider.
    DATABASE_URL: str = DEFAULT_DATABASE_URL
    SECRET_KEY: str = "renalguard-secret-key-change-in-production-32x"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    MODEL_DIR: str = str(PROJECT_ROOT / "ml" / "models")

    class Config:
        env_file = PROJECT_ROOT / ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
