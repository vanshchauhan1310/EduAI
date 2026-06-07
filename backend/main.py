"""
EduAI Governance Platform — FastAPI Application Entry Point.

Production architecture:
    MySQL → FastAPI → Dropout Prediction Model → dropout_predictions table → Dashboards
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.router import api_router
from app.database.session import engine, Base

# ─── Logging Configuration ────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─── Lifespan (Startup / Shutdown) ────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — runs on startup and shutdown."""
    # Startup
    logger.info("Starting EduAI Governance Platform v%s", settings.APP_VERSION)
    logger.info("Environment: %s", settings.APP_ENV)

    # Create tables (dev only — use Alembic migrations in production)
    if settings.APP_ENV in ("development", "dev"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")

    yield

    # Shutdown
    logger.info("Shutting down EduAI Governance Platform")
    await engine.dispose()


# ─── FastAPI App ──────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Education Governance Platform API",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
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
    return JSONResponse({
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    })


@app.get("/", tags=["Root"])
async def root():
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }