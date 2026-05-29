"""
AI Recommendation Engine
Generates personalized learning and intervention recommendations using
student performance data and optionally OpenAI GPT.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.student import Student
from app.models.assessment import AssessmentResult, Assessment
from app.core.config import settings


SUBJECT_REMEDIAL_MAP = {
    "MATHEMATICS": ["Khan Academy exercises", "Vedic Maths worksheets", "Peer tutoring"],
    "SCIENCE": ["Lab practical sessions", "Video experiments", "Science quiz games"],
    "ENGLISH": ["Reading comprehension drills", "Dictation practice", "Story writing"],
    "TELUGU": ["Grammar worksheets", "Essay writing", "Poem recitation"],
    "SOCIAL": ["Map activities", "Current affairs quiz", "Project-based learning"],
}


class RecommendationEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_student_recommendations(self, student_id: int) -> dict:
        student_result = await self.db.execute(select(Student).where(Student.id == student_id))
        student = student_result.scalar_one_or_none()
        if not student:
            return {"error": "Student not found"}

        # Get weak subjects
        subject_perf = await self.db.execute(
            select(
                Assessment.subject,
                func.avg(AssessmentResult.percentage).label("avg_pct"),
            ).join(Assessment, AssessmentResult.assessment_id == Assessment.id).where(
                and_(
                    AssessmentResult.student_id == student_id,
                    AssessmentResult.is_absent == False,
                    AssessmentResult.percentage.isnot(None),
                )
            ).group_by(Assessment.subject)
        )
        subject_data = {row.subject: round(row.avg_pct, 1) for row in subject_perf.all()}

        weak_subjects = {s: p for s, p in subject_data.items() if p < 50}
        strong_subjects = {s: p for s, p in subject_data.items() if p >= 70}

        recommendations = []

        for subject, pct in weak_subjects.items():
            activities = SUBJECT_REMEDIAL_MAP.get(subject.upper(), ["Additional practice worksheets"])
            recommendations.append({
                "subject": subject,
                "current_average": pct,
                "priority": "HIGH" if pct < 35 else "MEDIUM",
                "interventions": activities[:2],
                "target_percentage": 50,
            })

        # Attendance-based recommendation
        if student.dropout_risk_score and student.dropout_risk_score > 0.5:
            recommendations.append({
                "type": "ATTENDANCE",
                "message": "Student needs immediate attendance counseling",
                "action": "Schedule parent meeting within 3 days",
                "priority": "CRITICAL",
            })

        # AI-enhanced recommendations (optional — requires OpenAI API key)
        ai_summary = None
        if settings.OPENAI_API_KEY and weak_subjects:
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                prompt = (
                    f"Student {student.full_name} (Class {student.current_class}) has weak performance "
                    f"in: {', '.join(f'{s} ({p}%)' for s, p in weak_subjects.items())}. "
                    f"Provide 3 specific, actionable teacher interventions in 2 sentences each."
                )
                response = await client.chat.completions.create(
                    model=settings.AI_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=settings.AI_TEMPERATURE,
                    max_tokens=300,
                )
                ai_summary = response.choices[0].message.content
            except Exception:
                ai_summary = None

        return {
            "student_id": student_id,
            "student_name": student.full_name,
            "subject_performance": subject_data,
            "weak_subjects": list(weak_subjects.keys()),
            "strong_subjects": list(strong_subjects.keys()),
            "recommendations": recommendations,
            "ai_enhanced_plan": ai_summary,
        }
