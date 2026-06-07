"""
Automated Report Generator Service.
Fetches real data from PostgreSQL, sends to NVIDIA NIM for narrative generation,
exports structured JSON + PDF.
"""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import date, timedelta

from app.models.copilot import GeneratedReport
from app.models.user import User
from app.models.school import School
from app.models.student import Student, RiskLevel
from app.models.teacher import Teacher
from app.models.attendance import Attendance, AttendanceStatus, AttendanceReferenceType
from app.models.assessment import AssessmentResult, Assessment
from app.schemas.copilot import (
    ReportGenerateRequest, ReportGenerateResponse,
    ReportContentJSON, ReportHistoryItem,
)
from app.utils.gemini_client import generate_json, REPORT_GENERATION_PROMPT
from app.utils.pdf_generator import generate_report_pdf
from app.utils.docx_generator import generate_report_docx


def _normalize_list_items(value):
    if value is None:
        return []
    if isinstance(value, str):
        lines = [line.strip() for line in value.replace("\r", "").split("\n") if line.strip()]
        return [line.lstrip("-• ") for line in lines]
    if isinstance(value, list):
        normalized = []
        for item in value:
            if isinstance(item, str):
                normalized.append(item.strip())
            elif isinstance(item, dict):
                action_text = None
                if isinstance(item.get("action"), str):
                    action_text = item["action"].strip()
                elif isinstance(item.get("recommendation"), str):
                    action_text = item["recommendation"].strip()
                elif item:
                    first_value = next(iter(item.values()))
                    action_text = str(first_value).strip()
                normalized.append(action_text or str(item).strip())
            else:
                normalized.append(str(item).strip())
        return [item for item in normalized if item]
    return [str(value).strip()]


REPORT_TYPE_LABELS = {
    "school_performance":  "School Academic Performance Report",
    "attendance":          "Attendance Analytics Report",
    "teacher_performance": "Teacher Performance Report",
    "school_health":       "School Health Assessment Report",
}


async def _fetch_school_performance_data(db: AsyncSession, scope: str, scope_id: int, academic_year: str) -> dict:
    query = select(Student).where(Student.is_active == True, Student.academic_year == academic_year)
    if scope == "school":
        query = query.where(Student.school_id == scope_id)
    elif scope == "mandal":
        query = query.join(School).where(School.mandal_id == scope_id)
    elif scope == "district":
        query = query.join(School).where(School.district_id == scope_id)

    students_result = await db.execute(query)
    students = students_result.scalars().all()
    total = len(students)

    risk_counts = {}
    for level in RiskLevel:
        risk_counts[level.value] = sum(1 for s in students if s.risk_level == level)

    avg_risk = (
        sum(s.dropout_risk_score or 0 for s in students) / total if total else 0
    )

    # Assessment average
    assess_result = await db.execute(
        select(func.avg(AssessmentResult.percentage)).where(
            AssessmentResult.percentage.isnot(None),
            AssessmentResult.is_absent == False,
        )
    )
    avg_pct = assess_result.scalar_one_or_none() or 0

    return {
        "scope": scope, "scope_id": scope_id, "academic_year": academic_year,
        "total_students": total,
        "risk_distribution": risk_counts,
        "average_dropout_risk": round(avg_risk, 3),
        "average_assessment_percentage": round(avg_pct, 1),
        "high_risk_students": risk_counts.get("HIGH", 0) + risk_counts.get("CRITICAL", 0),
    }


async def _fetch_attendance_data(db: AsyncSession, scope: str, scope_id: int) -> dict:
    to_date = date.today()
    from_date = to_date - timedelta(days=30)

    base_filter = [
        Attendance.date >= from_date,
        Attendance.reference_type == AttendanceReferenceType.STUDENT,
    ]
    if scope == "school":
        base_filter.append(Attendance.school_id == scope_id)
    elif scope in ("mandal", "district"):
        # Join through school
        base_filter.append(
            Attendance.school_id.in_(
                select(School.id).where(
                    School.mandal_id == scope_id if scope == "mandal"
                    else School.district_id == scope_id
                )
            )
        )

    totals = await db.execute(
        select(
            func.count(Attendance.id).label("total"),
            func.sum((Attendance.status == AttendanceStatus.PRESENT).cast(int)).label("present"),
            func.sum((Attendance.status == AttendanceStatus.ABSENT).cast(int)).label("absent"),
        ).where(and_(*base_filter))
    )
    row = totals.one()
    total = row.total or 1
    present = row.present or 0
    absent = row.absent or 0

    return {
        "period": f"{from_date} to {to_date}",
        "total_records": total,
        "present_count": present,
        "absent_count": absent,
        "attendance_rate": round((present / total) * 100, 2),
    }


async def _fetch_teacher_performance_data(db: AsyncSession, scope: str, scope_id: int) -> dict:
    query = select(Teacher).where(Teacher.is_active == True)
    if scope == "school":
        query = query.where(Teacher.school_id == scope_id)
    result = await db.execute(query)
    teachers = result.scalars().all()

    avg_att = sum(t.average_attendance_pct or 0 for t in teachers) / max(len(teachers), 1)
    avg_perf = sum(t.performance_score or 0 for t in teachers) / max(len(teachers), 1)
    low_att = [t for t in teachers if (t.average_attendance_pct or 100) < 80]

    return {
        "total_teachers": len(teachers),
        "average_attendance_pct": round(avg_att, 1),
        "average_performance_score": round(avg_perf, 1),
        "teachers_below_80pct_attendance": len(low_att),
        "teacher_types": {
            t_type: sum(1 for t in teachers if t.teacher_type.value == t_type)
            for t_type in ["PERMANENT", "CONTRACT", "GUEST"]
        },
    }


async def _fetch_school_health_data(db: AsyncSession, scope: str, scope_id: int) -> dict:
    query = select(School).where(School.is_active == True)
    if scope == "school":
        query = query.where(School.id == scope_id)
    elif scope == "mandal":
        query = query.where(School.mandal_id == scope_id)
    elif scope == "district":
        query = query.where(School.district_id == scope_id)

    result = await db.execute(query)
    schools = result.scalars().all()

    health_scores = [s.health_score for s in schools if s.health_score is not None]
    avg_health = sum(health_scores) / max(len(health_scores), 1)

    graded = {"A": 0, "B": 0, "C": 0, "D": 0}
    for score in health_scores:
        if score >= 80:   graded["A"] += 1
        elif score >= 65: graded["B"] += 1
        elif score >= 50: graded["C"] += 1
        else:             graded["D"] += 1

    infra_stats = {
        "with_electricity":    sum(1 for s in schools if s.has_electricity),
        "with_toilets":        sum(1 for s in schools if s.has_toilets),
        "with_water":          sum(1 for s in schools if s.has_drinking_water),
        "with_computer_lab":   sum(1 for s in schools if s.has_computer_lab),
        "with_library":        sum(1 for s in schools if s.has_library),
        "with_playground":     sum(1 for s in schools if s.has_playground),
    }

    return {
        "total_schools": len(schools),
        "average_health_score": round(avg_health, 1),
        "grade_distribution": graded,
        "infrastructure_stats": infra_stats,
        "schools_needing_attention": graded["C"] + graded["D"],
    }


FETCHER_MAP = {
    "school_performance":  _fetch_school_performance_data,
    "attendance":          _fetch_attendance_data,
    "teacher_performance": _fetch_teacher_performance_data,
    "school_health":       _fetch_school_health_data,
}


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate(self, request: ReportGenerateRequest, user: User) -> ReportGenerateResponse:
        fetcher = FETCHER_MAP.get(request.report_type)
        if not fetcher:
            raise HTTPException(status_code=400, detail=f"Unknown report type: {request.report_type}")

        label = REPORT_TYPE_LABELS.get(request.report_type, request.report_type)

        if request.report_type in ("school_performance", "school_health"):
            raw_data = await fetcher(self.db, request.report_scope, request.scope_id, request.academic_year)
        else:
            raw_data = await fetcher(self.db, request.report_scope, request.scope_id)

        data_formatted = "\n".join(f"  {k}: {v}" for k, v in raw_data.items())
        prompt = REPORT_GENERATION_PROMPT.format(
            report_type_name=label,
            data_formatted=data_formatted,
        )

        content_dict = await generate_json(prompt)

        try:
            content_json = ReportContentJSON(**content_dict)
        except Exception:
            content_json = ReportContentJSON(
                executive_summary=content_dict.get("executive_summary", ""),
                kpi_analysis=content_dict.get("kpi_analysis", ""),
                trends=content_dict.get("trends", ""),
                risks=content_dict.get("risks", ""),
                recommendations=_normalize_list_items(content_dict.get("recommendations", [])),
                action_plan=_normalize_list_items(content_dict.get("action_plan", [])),
            )

        plain_text = (
            f"EXECUTIVE SUMMARY\n{content_json.executive_summary}\n\n"
            f"KPI ANALYSIS\n{content_json.kpi_analysis}\n\n"
            f"TRENDS\n{content_json.trends}\n\n"
            f"RISKS\n{content_json.risks}\n\n"
            f"RECOMMENDATIONS\n" + "\n".join(f"• {r}" for r in content_json.recommendations) + "\n\n"
            f"ACTION PLAN\n" + "\n".join(f"• {a}" for a in content_json.action_plan)
        )

        record = GeneratedReport(
            user_id=user.id,
            report_type=request.report_type,
            report_scope=request.report_scope,
            scope_id=request.scope_id,
            content=plain_text,
            content_json=content_json.model_dump(),
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)

        return ReportGenerateResponse(
            id=record.id,
            report_type=record.report_type,
            report_scope=record.report_scope or "",
            content=plain_text,
            content_json=content_json,
            created_at=str(record.created_at),
        )

    async def get_by_id(self, report_id: int, user: User) -> ReportGenerateResponse:
        result = await self.db.execute(
            select(GeneratedReport).where(
                GeneratedReport.id == report_id,
                GeneratedReport.user_id == user.id,
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            raise HTTPException(status_code=404, detail="Report not found")
        return ReportGenerateResponse(
            id=record.id,
            report_type=record.report_type,
            report_scope=record.report_scope or "",
            content=record.content,
            content_json=ReportContentJSON(**record.content_json) if record.content_json else None,
            created_at=str(record.created_at),
        )

    async def get_history(self, user: User, limit: int = 20) -> list[ReportHistoryItem]:
        result = await self.db.execute(
            select(GeneratedReport)
            .where(GeneratedReport.user_id == user.id)
            .order_by(desc(GeneratedReport.created_at))
            .limit(limit)
        )
        return [
            ReportHistoryItem(id=r.id, report_type=r.report_type, report_scope=r.report_scope or "", created_at=str(r.created_at))
            for r in result.scalars().all()
        ]

    async def export_pdf(self, report_id: int, user: User) -> bytes:
        resp = await self.get_by_id(report_id, user)
        return generate_report_pdf(
            resp.report_type, resp.content,
            resp.content_json.model_dump() if resp.content_json else None,
        )

    async def export_docx(self, report_id: int, user: User) -> bytes:
        resp = await self.get_by_id(report_id, user)
        return generate_report_docx(
            resp.report_type, resp.content,
            resp.content_json.model_dump() if resp.content_json else None,
        )
