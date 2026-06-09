"""
FastAPI Router — Dropout Prediction APIs.

Endpoints:
    POST   /run-predictions      Run predictions for all active students
    GET    /high-risk            List all high-risk students
    GET    /student/{id}         Prediction details for a student
    GET    /school/{id}          School-level dropout analysis
    GET    /mandal/{id}          Mandal-level dropout analysis
    GET    /district/{id}        District-level dropout analysis
    POST   /cron/daily           Trigger daily predictions (cron-ready)
    POST   /model/reload         Force-reload the ML model
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.dropout_prediction import (
    RunPredictionsRequest,
    RunPredictionsResponse,
    HighRiskListResponse,
    HighRiskStudentItem,
    StudentPredictionDetail,
    SchoolDropoutDetailResponse,
    MandalDropoutSummary,
    DistrictDropoutSummary,
    PredictByClassRequest,
    PredictByClassResponse,
    ClassPredictionStudentItem,
    MessageResponse,
)
from app.services.dropout_prediction_service import DropoutPredictionService
from app.ml.dropout.predictor import reload_model as _reload_model
from app.core.dependencies import get_current_user, require_hm
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── Dependency ────────────────────────────────────────────────

def _get_service(db: AsyncSession = Depends(get_db)) -> DropoutPredictionService:
    return DropoutPredictionService(db)


# ─── Background Task Wrapper ──────────────────────────────────

async def _run_predictions_background(
    school_id: int | None,
    academic_year: str | None,
    batch_id: str,
    db_factory,
):
    """Background task that runs the full prediction pipeline."""
    from app.database.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            service = DropoutPredictionService(db)
            result = await service.run_predictions(
                school_id=school_id,
                academic_year=academic_year,
                batch_id=batch_id,
            )
            await db.commit()
            logger.info("Background prediction complete: %s", result)
        except Exception as e:
            await db.rollback()
            logger.error("Background prediction failed: %s", str(e), exc_info=True)


# ─── POST /run-predictions ────────────────────────────────────

@router.post(
    "/run-predictions",
    response_model=RunPredictionsResponse,
    summary="Run dropout predictions for active students",
    description=(
        "Triggers the full ML prediction pipeline in the background. "
        "Reads student data from Supabase, builds features, runs the XGBoost model, "
        "and saves results to dropout_predictions table."
    ),
    tags=["Dropout Prediction"],
)
async def run_predictions(
    request: RunPredictionsRequest = RunPredictionsRequest(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    service: DropoutPredictionService = Depends(_get_service),
):
    try:
        batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Run in background
        background_tasks.add_task(
            _run_predictions_background,
            school_id=request.school_id,
            academic_year=request.academic_year,
            batch_id=batch_id,
            db_factory=None,
        )

        return RunPredictionsResponse(
            message="Prediction pipeline started successfully",
            batch_id=batch_id,
            total_students=0,  # Will be populated when background task runs
            high_risk_count=0,
            critical_risk_count=0,
            medium_risk_count=0,
            low_risk_count=0,
            started_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error("Failed to start predictions: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start prediction pipeline: {str(e)}",
        )


# ─── POST /run-predictions/sync ───────────────────────────────

@router.post(
    "/run-predictions/sync",
    response_model=dict,
    summary="Run predictions synchronously (for small datasets)",
    description="Runs the prediction pipeline inline — waits for completion.",
    tags=["Dropout Prediction"],
)
async def run_predictions_sync(
    request: RunPredictionsRequest = RunPredictionsRequest(),
    service: DropoutPredictionService = Depends(_get_service),
):
    """Synchronous version — useful for testing or small student counts."""
    try:
        result = await service.run_predictions(
            school_id=request.school_id,
            academic_year=request.academic_year,
        )
        return result

    except Exception as e:
        logger.error("Sync prediction failed: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Prediction pipeline failed: {str(e)}",
        )


# ─── GET /high-risk ───────────────────────────────────────────

@router.get(
    "/high-risk",
    response_model=HighRiskListResponse,
    summary="Get all high-risk students",
    description="Returns students with High or Critical dropout risk.",
    tags=["Dropout Prediction — HM Dashboard"],
)
async def get_high_risk_students(
    school_id: int | None = Query(None, description="Filter by school ID"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: DropoutPredictionService = Depends(_get_service),
):
    try:
        result = await service.get_high_risk_students(
            school_id=school_id,
            limit=limit,
            offset=offset,
        )
        return HighRiskListResponse(
            total=result["total"],
            students=[HighRiskStudentItem(**s) for s in result["students"]],
        )

    except Exception as e:
        logger.error("Failed to fetch high-risk students: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /student/{student_id} ────────────────────────────────

@router.get(
    "/student/{student_id}",
    response_model=StudentPredictionDetail,
    summary="Get prediction details for a student",
    description="Returns the latest dropout prediction for a specific student.",
    tags=["Dropout Prediction — HM Dashboard"],
)
async def get_student_prediction(
    student_id: int,
    service: DropoutPredictionService = Depends(_get_service),
):
    try:
        result = await service.get_student_prediction(student_id)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"No prediction found for student_id={student_id}",
            )
        return StudentPredictionDetail(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch prediction for student %d: %s", student_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /school/{school_id} ──────────────────────────────────

@router.get(
    "/school/{school_id}",
    response_model=SchoolDropoutDetailResponse,
    summary="School-level dropout analysis",
    description="Returns school summary + student-level dropout details for MEO dashboard.",
    tags=["Dropout Prediction — MEO Dashboard"],
)
async def get_school_analysis(
    school_id: int,
    service: DropoutPredictionService = Depends(_get_service),
):
    try:
        result = await service.get_school_analysis(school_id)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"No predictions found for school_id={school_id}",
            )

        summary = result["summary"]
        from app.schemas.dropout_prediction import (
            SchoolDropoutSummary,
            SchoolDropoutStudentItem,
        )

        return SchoolDropoutDetailResponse(
            summary=SchoolDropoutSummary(
                school_id=summary["school_id"],
                school_name=summary["school_name"],
                total_students=summary["total_students"],
                total_predictions=summary["total_predictions"],
                high_risk_count=summary["high_risk_count"],
                critical_risk_count=summary["critical_risk_count"],
                medium_risk_count=summary["medium_risk_count"],
                low_risk_count=summary["low_risk_count"],
                average_risk_score=summary["average_risk_score"],
                top_risk_factors=[],
                last_prediction_at=summary.get("last_prediction_at"),
            ),
            students=[SchoolDropoutStudentItem(**s) for s in result["students"]],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch school analysis %d: %s", school_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /mandal/{mandal_id} ──────────────────────────────────

@router.get(
    "/mandal/{mandal_id}",
    response_model=MandalDropoutSummary,
    summary="Mandal-level dropout analysis",
    description="Returns mandal-wide dropout statistics with school breakdowns.",
    tags=["Dropout Prediction — MEO Dashboard"],
)
async def get_mandal_analysis(
    mandal_id: int,
    service: DropoutPredictionService = Depends(_get_service),
):
    try:
        result = await service.get_mandal_analysis(mandal_id)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for mandal_id={mandal_id}",
            )

        from app.schemas.dropout_prediction import MandalSchoolItem

        return MandalDropoutSummary(
            mandal_id=result["mandal_id"],
            mandal_name=result["mandal_name"],
            district_name=result["district_name"],
            total_schools=result["total_schools"],
            total_students=result["total_students"],
            total_high_risk=result["total_high_risk"],
            total_critical_risk=result["total_critical_risk"],
            overall_average_risk=result["overall_average_risk"],
            schools=[MandalSchoolItem(**s) for s in result["schools"]],
            last_prediction_at=result.get("last_prediction_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch mandal analysis %d: %s", mandal_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /district/{district_id} ──────────────────────────────

@router.get(
    "/district/{district_id}",
    response_model=DistrictDropoutSummary,
    summary="District-level dropout analysis",
    description="Returns district-wide dropout statistics with mandal breakdowns.",
    tags=["Dropout Prediction — DEO Dashboard"],
)
async def get_district_analysis(
    district_id: int,
    service: DropoutPredictionService = Depends(_get_service),
):
    try:
        result = await service.get_district_analysis(district_id)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for district_id={district_id}",
            )

        from app.schemas.dropout_prediction import DistrictMandalItem

        return DistrictDropoutSummary(
            district_id=result["district_id"],
            district_name=result["district_name"],
            total_mandals=result["total_mandals"],
            total_schools=result["total_schools"],
            total_students=result["total_students"],
            total_high_risk=result["total_high_risk"],
            total_critical_risk=result["total_critical_risk"],
            overall_average_risk=result["overall_average_risk"],
            mandals=[DistrictMandalItem(**m) for m in result["mandals"]],
            last_prediction_at=result.get("last_prediction_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch district analysis %d: %s", district_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ─── POST /cron/daily ─────────────────────────────────────────

@router.post(
    "/cron/daily",
    response_model=dict,
    summary="Trigger daily dropout predictions (cron endpoint)",
    description=(
        "Cron-ready endpoint. Can be called by APScheduler, system cron, "
        "or any scheduler to run daily predictions for all active students."
    ),
    tags=["Dropout Prediction — Cron"],
)
async def trigger_daily_predictions(
    background_tasks: BackgroundTasks = BackgroundTasks(),
    service: DropoutPredictionService = Depends(_get_service),
):
    try:
        batch_id = f"daily_{datetime.utcnow().strftime('%Y%m%d')}"

        background_tasks.add_task(
            _run_predictions_background,
            school_id=None,
            academic_year=None,
            batch_id=batch_id,
            db_factory=None,
        )

        return {
            "message": "Daily prediction cron triggered",
            "batch_id": batch_id,
            "started_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error("Daily cron trigger failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET /school/{school_id}/classes-with-students ────────

@router.get(
    "/school/{school_id}/classes-with-students",
    response_model=dict,
    summary="Get classes that have students for a school",
    description="Returns a list of class levels that have active students in the given school.",
    tags=["Dropout Prediction — HM Dashboard"],
)
async def get_school_classes_with_students(
    school_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all classes that have active students for a school."""
    try:
        from sqlalchemy import select, func, and_
        from app.models.student import Student

        stmt = (
            select(Student.current_class, func.count(Student.id).label("count"))
            .where(
                and_(
                    Student.school_id == school_id,
                    Student.is_active == True,
                )
            )
            .group_by(Student.current_class)
            .order_by(Student.current_class)
        )
        result = await db.execute(stmt)
        rows = result.all()

        classes = [
            {"class_level": r.current_class, "student_count": r.count}
            for r in rows
        ]

        return {
            "school_id": school_id,
            "classes": classes,
        }
    except Exception as e:
        logger.error("Failed to fetch classes for school %d: %s", school_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── POST /predict-by-class ──────────────────────────────────

@router.post(
    "/predict-by-class",
    response_model=PredictByClassResponse,
    summary="Run dropout predictions for all students in a class",
    description=(
        "Headmaster selects a class → system fetches all students in that class "
        "from the database → runs ML predictions using stored features → "
        "returns results immediately. No Excel upload needed."
    ),
    tags=["Dropout Prediction — HM Dashboard"],
)
async def predict_by_class(
    request: PredictByClassRequest,
    current_user: User = Depends(get_current_user),
    service: DropoutPredictionService = Depends(_get_service),
):
    """
    Predict dropout risk for all students in a given school+class.

    This is the HM-friendly flow:
      1. HM selects a class (e.g., Class 10)
      2. System fetches all students in Class 10 from HM's school
      3. Reads pre-computed ML features from student_ml_input table
      4. Runs XGBoost predictions
      5. Returns enriched results with student names, risk levels, etc.

    No Excel/CSV upload required — data comes from the database.
    The school_id is derived from the authenticated user's token.
    """
    try:
        # Get school_id from authenticated user if not provided in request
        school_id = request.school_id or current_user.school_id
        if not school_id:
            raise HTTPException(
                status_code=400,
                detail="No school_id found. User is not associated with a school.",
            )

        logger.info(
            "Class prediction — user=%d school=%d class=%d",
            current_user.id, school_id, request.class_level,
        )

        result = await service.predict_by_class(
            school_id=school_id,
            class_level=request.class_level,
        )

        return PredictByClassResponse(
            batch_id=result["batch_id"],
            school_id=result["school_id"],
            class_level=result["class_level"],
            total_students=result["total_students"],
            high_risk_count=result["high_risk_count"],
            critical_risk_count=result["critical_risk_count"],
            medium_risk_count=result["medium_risk_count"],
            low_risk_count=result["low_risk_count"],
            students=[ClassPredictionStudentItem(**s) for s in result["students"]],
            message=result.get("message", ""),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Class prediction failed — class=%d: %s",
            request.class_level, str(e), exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Class prediction failed: {str(e)}",
        )


# ─── POST /model/reload ───────────────────────────────────────

@router.post(
    "/model/reload",
    response_model=MessageResponse,
    summary="Force-reload the ML model from disk",
    description="Call after retraining the model to pick up new model.pkl.",
    tags=["Dropout Prediction — Admin"],
)
async def reload_ml_model():
    try:
        _reload_model()
        return MessageResponse(message="Model reloaded successfully")
    except Exception as e:
        logger.error("Model reload failed: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
