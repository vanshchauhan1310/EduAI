from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database.session import get_db
from app.core.dependencies import get_current_user, require_hm
from app.models.user import User
from app.models.student import Student
from app.models.ai_insight import AIInsight, InsightType, InsightScope

router = APIRouter(prefix="/ai", tags=["AI Insights"])


class InsightActionRequest(BaseModel):
    action_notes: str


@router.get("/student/{student_id}/risk")
async def get_student_risk(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get AI-generated dropout risk assessment for a student."""
    from app.ai.dropout_predictor import DropoutPredictor
    predictor = DropoutPredictor(db)
    return await predictor.predict(student_id)


@router.post("/school/{school_id}/run-risk-scan")
async def run_school_risk_scan(
    school_id: int,
    current_user: User = Depends(require_hm),
    db: AsyncSession = Depends(get_db),
):
    """Run dropout risk assessment for all students in a school."""
    from app.ai.dropout_predictor import DropoutPredictor
    predictor = DropoutPredictor(db)

    students_result = await db.execute(
        select(Student).where(Student.school_id == school_id, Student.is_active == True)
    )
    students = list(students_result.scalars().all())

    results = []
    for student in students:
        result = await predictor.predict(student.id)
        results.append(result)

    high_risk = [r for r in results if r.get("risk_level") in ("HIGH", "CRITICAL")]
    return {
        "school_id": school_id,
        "students_scanned": len(results),
        "high_risk_count": len(high_risk),
        "results_summary": results[:10],
    }


@router.get("/school/{school_id}/health-score")
async def get_school_health_score(
    school_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get AI-computed health score for a school."""
    from app.ai.school_health_scorer import SchoolHealthScorer
    scorer = SchoolHealthScorer(db)
    return await scorer.compute(school_id)


@router.get("/student/{student_id}/recommendations")
async def get_student_recommendations(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get AI-generated learning recommendations for a student."""
    from app.ai.recommendation_engine import RecommendationEngine
    engine = RecommendationEngine(db)
    return await engine.get_student_recommendations(student_id)


@router.get("/insights/{scope}/{reference_id}")
async def get_insights(
    scope: InsightScope,
    reference_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all AI insights for a student, school, or district."""
    result = await db.execute(
        select(AIInsight).where(
            AIInsight.scope == scope,
            AIInsight.reference_id == reference_id,
        ).order_by(AIInsight.created_at.desc()).limit(20)
    )
    insights = result.scalars().all()
    return [
        {
            "id": i.id,
            "type": i.insight_type.value,
            "risk_score": i.risk_score,
            "confidence": i.confidence,
            "summary": i.summary,
            "recommendations": i.recommendations,
            "is_actioned": i.is_actioned,
            "created_at": str(i.created_at),
        }
        for i in insights
    ]


@router.post("/insights/{insight_id}/action")
async def mark_insight_actioned(
    insight_id: int,
    request: InsightActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark an AI insight as actioned/resolved."""
    from datetime import datetime, timezone
    result = await db.execute(select(AIInsight).where(AIInsight.id == insight_id))
    insight = result.scalar_one_or_none()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    insight.is_actioned = "1"
    insight.actioned_by_id = current_user.id
    insight.actioned_at = datetime.now(timezone.utc)
    insight.action_notes = request.action_notes
    await db.flush()
    return {"actioned": True}
