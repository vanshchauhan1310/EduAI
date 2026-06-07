'''from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.core.config import settings
from app.api.router import api_router
from app.database.session import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
        environment=settings.APP_ENV,
    )

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Education Governance Platform API",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    return JSONResponse({"status": "healthy", "version": settings.APP_VERSION})'''
from fastapi import FastAPI

from app.api.v1.dropout import (
    router as train_router
)

from app.api.v1.dropout_batch_predict import (
    router as predict_router
)

from app.api.v1.ai_assessment import (
    router as ai_assessment_router
)

app = FastAPI(
    title="EduAI Backend"
)

app.include_router(
    train_router,
    prefix="/api/v1/dropout",
    tags=["Dropout Training"]
)

app.include_router(
    predict_router,
    prefix="/api/v1/dropout",
    tags=["Dropout Prediction"]
)

app.include_router(
    ai_assessment_router,
    prefix="/api/v1"
)