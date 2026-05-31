from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",          # silently ignore unknown env vars
    )

    # App
    APP_NAME: str = "EduAI Governance Platform"
    APP_ENV: str = "development"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["http://localhost:19000", "http://localhost:3000"]

    # Database — set DATABASE_URL in your .env file
    # Format: postgresql+asyncpg://user:password@localhost:5432/dbname
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/eduai_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # JWT — override JWT_SECRET_KEY in .env for production
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production-do-not-use-in-prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Redis (optional — not required for copilot module)
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 300

    # OpenAI (optional — only for dropout predictor)
    OPENAI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o"
    AI_TEMPERATURE: float = 0.3
    DROPOUT_PREDICTION_THRESHOLD: float = 0.65

    # NVIDIA NIM (Admin Copilot)
    NVIDIA_NIM_API_KEY: str = ""
    NVIDIA_NIM_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_NIM_MODEL: str = "meta/llama-3.3-70b-instruct"

    # Ollama (legacy/local Admin Copilot option)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"          # run: ollama pull llama3.2

    # Firebase (optional — not required for copilot)
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_PRIVATE_KEY: str = ""
    FIREBASE_CLIENT_EMAIL: str = ""

    # Twilio (optional — not required for copilot)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_NUMBER: str = ""

    # AWS (optional — not required for copilot)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-south-1"
    AWS_S3_BUCKET: str = ""

    # Sentry (optional)
    SENTRY_DSN: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def _parse_debug(cls, value):
        if isinstance(value, str) and value.lower() in {"release", "production", "prod"}:
            return False
        return value


settings = Settings()
