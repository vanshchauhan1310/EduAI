"""
Shared application configuration
================================
Single source of truth for settings used by BOTH the EduSakhi learning core
and the governance layer. Reads from environment / .env.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Plain settings object (kept dependency-light, like the rest of EduSakhi)."""

    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = "EduSakhi AI Education Platform"
    API_V1_PREFIX: str = "/api/v1"

    # ── Database (shared sync engine in database/db.py) ───────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./edusakhi.db")

    # ── Auth / JWT ────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )

    # ── EduSakhi AI ───────────────────────────────────────────────────────────
    HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", "")
    HF_MODEL: str = os.getenv("HF_MODEL", "Qwen/Qwen3-8B")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")


settings = Settings()
