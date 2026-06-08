"""
Career & Skill Recommender (Use Case 07) — combines a short in-app aptitude/interest
survey with the student's real academic performance and attendance signals, then asks
the existing NVIDIA NIM AI integration (app.utils.gemini_client) to produce structured,
personalised stream/career/skill/scholarship recommendations grounded in Telangana's
labour-market sectors (BFSI, IT, Pharma, Manufacturing).
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import Assessment, AssessmentResult
from app.models.attendance import Attendance, AttendanceReferenceType, AttendanceStatus
from app.models.student import Student
from app.utils.gemini_client import generate_json

# ─── Survey Questions ─────────────────────────────────────────────
# Static single-choice questions — no DB table needed, returned as-is by the API.

SURVEY_QUESTIONS = [
    {
        "question_id": "q1_interest_domain",
        "question_text": "Which of these activities sounds most interesting to you?",
        "options": [
            "Solving maths problems or building/fixing gadgets",
            "Running a shop, managing money, or planning a business",
            "Drawing, designing, writing, or performing",
            "Helping classmates, teaching, or organising community events",
            "Working with your hands — crafts, machines, fieldwork",
        ],
    },
    {
        "question_id": "q2_favourite_subject",
        "question_text": "Which subject do you enjoy the most?",
        "options": ["Mathematics", "Science", "Social Studies", "Languages", "Computer Science / IT"],
    },
    {
        "question_id": "q3_work_style",
        "question_text": "How do you prefer to work on a task?",
        "options": [
            "Alone, focused on details and data",
            "In a team, talking and coordinating with people",
            "A mix — sometimes alone, sometimes in a group",
            "Outdoors or moving around rather than at a desk",
        ],
    },
    {
        "question_id": "q4_problem_approach",
        "question_text": "When you face a tricky problem, what do you usually do first?",
        "options": [
            "Break it into steps and analyse it logically",
            "Look for a creative or out-of-the-box solution",
            "Ask others for their opinions and discuss it",
            "Try it out hands-on and learn by doing",
        ],
    },
    {
        "question_id": "q5_future_environment",
        "question_text": "Which work environment appeals to you most?",
        "options": [
            "An office with computers and technology",
            "A bank, company, or business setting",
            "A hospital, lab, or pharmacy",
            "A factory, workshop, or construction site",
            "A school, NGO, or government office",
        ],
    },
    {
        "question_id": "q6_strength",
        "question_text": "What would your friends say is your biggest strength?",
        "options": [
            "Good at numbers and logical thinking",
            "Good at communicating and convincing people",
            "Creative and imaginative",
            "Caring and good at helping others",
            "Practical and good at fixing/making things",
        ],
    },
    {
        "question_id": "q7_after_class10",
        "question_text": "After Class 10, which path sounds most appealing?",
        "options": [
            "Continue with Science (MPC/BiPC)",
            "Continue with Commerce",
            "Continue with Arts/Humanities",
            "Join a vocational/ITI/diploma course",
            "Not sure yet — I want guidance",
        ],
    },
    {
        "question_id": "q8_motivation",
        "question_text": "What matters most to you in a future career?",
        "options": [
            "High earning potential and growth",
            "Job security and stability",
            "Making a difference in society",
            "Doing creative or hands-on work I enjoy",
        ],
    },
]

_QUESTION_LOOKUP = {q["question_id"]: q for q in SURVEY_QUESTIONS}


# ─── Real-Data Signal Aggregation ─────────────────────────────────

async def aggregate_student_signals(db: AsyncSession, student: Student) -> dict:
    """Combine the student's real subject-wise performance and attendance into a compact dict."""
    perf_rows = (
        await db.execute(
            select(
                Assessment.subject,
                func.avg(AssessmentResult.percentage).label("avg_pct"),
                func.count(AssessmentResult.id).label("attempts"),
            )
            .join(Assessment, AssessmentResult.assessment_id == Assessment.id)
            .where(AssessmentResult.student_id == student.id, AssessmentResult.is_absent.is_(False))
            .group_by(Assessment.subject)
        )
    ).all()

    subject_performance = [
        {
            "subject": row.subject,
            "average_percentage": round(row.avg_pct, 1) if row.avg_pct is not None else None,
            "attempts": row.attempts,
        }
        for row in perf_rows
    ]

    attendance_rows = (
        await db.execute(
            select(Attendance.status, func.count(Attendance.id).label("count"))
            .where(
                Attendance.reference_type == AttendanceReferenceType.STUDENT,
                Attendance.reference_id == student.id,
            )
            .group_by(Attendance.status)
        )
    ).all()

    status_counts = {row.status.value if hasattr(row.status, "value") else row.status: row.count for row in attendance_rows}
    total_days = sum(status_counts.values())
    present_days = status_counts.get(AttendanceStatus.PRESENT.value, 0) + status_counts.get(AttendanceStatus.LATE.value, 0)
    attendance_percentage = round((present_days / total_days) * 100, 1) if total_days else None

    return {
        "current_class": student.current_class,
        "section": student.section,
        "category": student.category,
        "subject_performance": subject_performance,
        "attendance_percentage": attendance_percentage,
        "attendance_total_days": total_days,
    }


# ─── Prompt Construction ──────────────────────────────────────────

RECOMMENDATION_PROMPT = """You are an expert career and education counsellor for school students in Telangana, India,
with deep knowledge of the local labour market — especially the BFSI (banking/financial services/insurance),
IT, pharmaceutical, and manufacturing sectors that dominate hiring in the region.

A Class {current_class} student has completed an aptitude & interest survey and has the following real
academic record. Use ALL of this information together to produce a personalised, realistic, and
encouraging set of recommendations.

STUDENT PROFILE:
{profile_formatted}

SURVEY RESPONSES (interest & aptitude indicators):
{survey_formatted}

REAL ACADEMIC SIGNALS:
{signals_formatted}

Return a structured JSON object with EXACTLY these keys:
- "summary": a warm, personalised 2-3 sentence overview connecting the student's interests, strengths
  and academic record to their potential
- "recommended_streams": array of objects {{"stream": string (e.g. "MPC", "BiPC", "CEC", "HEC",
  "Vocational/ITI"), "match_percent": integer 0-100, "why": short reason grounded in the student's
  survey answers and academic signals}} — provide 2-3 ranked options
- "career_paths": array of objects {{"title": string, "sector": one of "BFSI"|"IT"|"Pharma"|
  "Manufacturing"|"Education"|"Public Service", "description": short 1-2 sentence explanation of why
  this fits and what it involves}} — provide 3-4 paths reflecting Telangana's real job market
- "skill_courses": array of objects {{"name": string, "provider": short string (e.g. "NSDC", "Telangana
  Skill Academy", "Coursera", "ITI"), "duration": short string (e.g. "3 months", "6 weeks")}} —
  provide 3-4 practical, accessible courses
- "scholarships": array of objects {{"name": string, "eligibility": short string, "how_to_apply": short
  string}} — provide 2-3 real-style Telangana/Government of India scholarship schemes relevant to the
  student's category and class

Be specific, encouraging, and grounded in the data provided. Return ONLY valid JSON, no markdown."""


def _format_profile(student: Student) -> str:
    return (
        f"- Name: {student.full_name}\n"
        f"- Class: {student.current_class}{(' - ' + student.section) if student.section else ''}\n"
        f"- Category: {student.category or 'Not specified'}"
    )


def _format_survey(survey_responses: list[dict]) -> str:
    lines = []
    for response in survey_responses:
        question = _QUESTION_LOOKUP.get(response.get("question_id"))
        question_text = question["question_text"] if question else response.get("question_id", "Unknown question")
        lines.append(f"- {question_text} → {response.get('answer')}")
    return "\n".join(lines) if lines else "- No survey responses recorded"


def _format_signals(signals: dict) -> str:
    lines = [f"- Attendance: {signals.get('attendance_percentage')}% over {signals.get('attendance_total_days')} recorded days"]
    subject_performance = signals.get("subject_performance") or []
    if subject_performance:
        lines.append("- Subject-wise average performance:")
        for entry in subject_performance:
            lines.append(f"   • {entry['subject']}: {entry['average_percentage']}% (across {entry['attempts']} assessment(s))")
    else:
        lines.append("- Subject-wise performance: no graded assessments on record yet")
    return "\n".join(lines)


def build_recommendation_prompt(student: Student, survey_responses: list[dict], signals: dict) -> str:
    return RECOMMENDATION_PROMPT.format(
        current_class=student.current_class,
        profile_formatted=_format_profile(student),
        survey_formatted=_format_survey(survey_responses),
        signals_formatted=_format_signals(signals),
    )


# ─── AI Generation ────────────────────────────────────────────────

REQUIRED_RECOMMENDATION_KEYS = (
    "summary",
    "recommended_streams",
    "career_paths",
    "skill_courses",
    "scholarships",
)


async def generate_recommendation(student: Student, survey_responses: list[dict], signals: dict) -> dict:
    prompt = build_recommendation_prompt(student, survey_responses, signals)
    recommendation = await generate_json(prompt)

    missing = [key for key in REQUIRED_RECOMMENDATION_KEYS if key not in recommendation]
    if missing:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI response missing expected fields: {', '.join(missing)}. Please try regenerating.",
        )

    return recommendation
