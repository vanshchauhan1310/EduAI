"""
SQLAlchemy Models — Import all models here so Alembic and Base.metadata can discover them.
"""

from app.models.user import User
from app.models.student import Student
from app.models.school import School, Mandal, District
from app.models.teacher import Teacher
from app.models.attendance import Attendance
from app.models.assessment import Assessment, AssessmentResult
from app.models.student_ml_input import StudentMLInput
from app.models.student_prediction import StudentPrediction
from app.models import listeners  # noqa: F401 — auto-populate student_ml_input on student create
from app.models.notification import Notification
from app.models.ai_insight import AIInsight
from app.models.copilot import (
    CircularSummary,
    GeneratedLetter,
    GeneratedReport,
    Translation,
    DocumentTranslation,
    GeneratedSchoolHealthAnalysis,
    GeneratedMEOReport,
)
from app.models.deo_copilot import (
    DistrictBrief,
    RiskScan,
    RiskAlert,
    TeacherRationalizationPlan,
    TeacherRationalization,
    DistrictCommunication,
)
from app.models.career import CareerRecommendation
