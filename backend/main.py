"""
EduAI Governance Platform — FastAPI Application Entry Point.

Production: gunicorn -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120 main:app
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.api.router import api_router
from app.database.session import engine, Base
from app.ai.exam_prep.embedding_model import get_embedding_model

# ─── Logging Configuration ────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_is_production = settings.APP_ENV in ("production", "prod")


# ─── Lifespan (Startup / Shutdown) ────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting EduAI Governance Platform v%s [%s]", settings.APP_VERSION, settings.APP_ENV)

    # Create tables only in dev — production uses `alembic upgrade head` (run by render.yaml startCommand)
    if not _is_production:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified (dev mode)")

    # Pre-load the shared embedding model. Failure degrades exam-prep features but doesn't block startup.
    try:
        logger.info("Pre-loading sentence embedding model...")
        get_embedding_model()
        logger.info("Embedding model ready")
    except Exception as exc:
        logger.error("Embedding model failed to load: %s — exam prep features unavailable", exc)

    yield

    logger.info("Shutting down EduAI Governance Platform")
    await engine.dispose()


# ─── FastAPI App ──────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Education Governance Platform API",
    version=settings.APP_VERSION,
    # Disable interactive docs in production (no public API exposure needed)
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    lifespan=lifespan,
)

# ─── Middleware ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ─── Routes ───────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    """Render polls this endpoint to determine if the service is healthy."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        logger.error("Health check DB ping failed: %s", exc)
        db_status = "error"

    status = "healthy" if db_status == "connected" else "degraded"
    return JSONResponse(
        {"status": status, "version": settings.APP_VERSION, "environment": settings.APP_ENV},
        status_code=200 if status == "healthy" else 503,
    )
