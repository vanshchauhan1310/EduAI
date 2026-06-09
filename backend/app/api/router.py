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
    career,
    tutor,
)

from app.api.v1.dropout_batch_predict import (
    router as dropout_batch_router
)

from app.api.v1.dropout_prediction import (
    router as dropout_prediction_router
)

from app.api.v1.dropout_excel import (
    router as dropout_excel_router
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(students.router)
api_router.include_router(attendance.router)
api_router.include_router(assessments.router)
api_router.include_router(career.router)
api_router.include_router(tutor.router)
api_router.include_router(analytics.router)
api_router.include_router(notifications.router)
api_router.include_router(ai.router)

api_router.include_router(
    dropout_batch_router,
    prefix="/dropout/legacy",
    tags=["Dropout Prediction — Legacy Excel"]
)

api_router.include_router(
    dropout_excel_router,
    prefix="/dropout",
    tags=["Dropout Prediction — HM Portal"]
)

api_router.include_router(
    dropout_prediction_router,
    prefix="/dropout",
    tags=["Dropout Prediction"]
)

api_router.include_router(copilot.router)
api_router.include_router(deo_copilot.router)