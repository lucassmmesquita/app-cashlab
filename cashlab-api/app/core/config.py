from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings — CashLab API"""

    # App info
    APP_NAME: str = "CashLab API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./cashlab.db"

    # CORS - origens permitidas (separar por vírgula)
    CORS_ORIGINS: str = "http://localhost:8081,http://localhost:19006"

    # JWT Authentication
    SECRET_KEY: str = "sua-chave-secreta-jwt-256-bits-trocar-em-producao"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Upload de PDFs
    MAX_PDF_SIZE_MB: int = 10
    UPLOAD_DIR: str = "./uploads"

    # OpenAI (OCR de prints de transações)
    OPENAI_API_KEY: str = ""

    # Social Login — Google
    GOOGLE_CLIENT_ID: str = ""

    # Social Login — Apple
    APPLE_TEAM_ID: str = ""
    APPLE_BUNDLE_ID: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
