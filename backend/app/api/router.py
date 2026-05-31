from fastapi import APIRouter

from app.api.v1 import (
    auth,
    students,
    attendance,
    assessments,
    analytics,
    notifications,
    ai,
    copilot,
    deo_copilot,
)

from app.api.v1.dropout_batch_predict import (
    router as dropout_batch_router
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(students.router)
api_router.include_router(attendance.router)
api_router.include_router(assessments.router)
api_router.include_router(analytics.router)
api_router.include_router(notifications.router)
api_router.include_router(ai.router)

api_router.include_router(
    dropout_batch_router,
    prefix="/dropout",
    tags=["Dropout Prediction"]
)

api_router.include_router(copilot.router)
api_router.include_router(deo_copilot.router)