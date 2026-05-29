from fastapi import APIRouter

from app.api.v1 import auth, students, attendance, assessments, analytics, notifications, ai

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(students.router)
api_router.include_router(attendance.router)
api_router.include_router(assessments.router)
api_router.include_router(analytics.router)
api_router.include_router(notifications.router)
api_router.include_router(ai.router)
