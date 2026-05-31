from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import date, timedelta

from app.database.session import get_db
from app.core.dependencies import require_meo, require_deo, get_current_user
from app.models.user import User
from app.models.student import Student, RiskLevel
from app.models.school import School
from app.models.attendance import Attendance, AttendanceStatus, AttendanceReferenceType

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/district/{district_id}/overview")
async def district_overview(
    district_id: int,
    current_user: User = Depends(require_deo),
    db: AsyncSession = Depends(get_db),
):
    """District-level governance overview for DEO dashboard."""
    total_schools = (await db.execute(
        select(func.count(School.id)).where(School.district_id == district_id, School.is_active == True)
    )).scalar_one()

    total_students = (await db.execute(
        select(func.count(Student.id)).join(School).where(
            School.district_id == district_id, Student.is_active == True
        )
    )).scalar_one()

    high_risk_count = (await db.execute(
        select(func.count(Student.id)).join(School).where(
            School.district_id == district_id,
            Student.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]),
            Student.is_active == True,
        )
    )).scalar_one()

    today = date.today()
    start_of_month = today.replace(day=1)
    attendance_data = await db.execute(
        select(
            func.count(Attendance.id).label("total"),
    func.sum(func.IF(Attendance.status == AttendanceStatus.PRESENT, 1, 0)).label("present"),
        ).join(School, Attendance.school_id == School.id).where(
            and_(
                School.district_id == district_id,
                Attendance.date >= start_of_month,
                Attendance.reference_type == AttendanceReferenceType.STUDENT,
            )
        )
    )
    att_row = attendance_data.one()
    attendance_rate = round((att_row.present / att_row.total * 100) if att_row.total else 0, 2)

    return {
        "district_id": district_id,
        "total_schools": total_schools,
        "total_students": total_students,
        "high_risk_students": high_risk_count,
        "attendance_rate_this_month": attendance_rate,
        "dropout_risk_rate": round((high_risk_count / total_students * 100) if total_students else 0, 2),
    }


@router.get("/mandal/{mandal_id}/overview")
async def mandal_overview(
    mandal_id: int,
    current_user: User = Depends(require_meo),
    db: AsyncSession = Depends(get_db),
):
    """Mandal/Cluster level overview for MEO dashboard."""
    schools_result = await db.execute(
        select(School).where(School.mandal_id == mandal_id, School.is_active == True)
    )
    schools = list(schools_result.scalars().all())
    school_ids = [s.id for s in schools]

    students_count = (await db.execute(
        select(func.count(Student.id)).where(
            Student.school_id.in_(school_ids), Student.is_active == True
        )
    )).scalar_one()

    high_risk = (await db.execute(
        select(func.count(Student.id)).where(
            Student.school_id.in_(school_ids),
            Student.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]),
        )
    )).scalar_one()

    schools_summary = []
    for s in schools:
        student_count = (await db.execute(
            select(func.count(Student.id)).where(Student.school_id == s.id, Student.is_active == True)
        )).scalar_one()
        schools_summary.append({
            "school_id": s.id,
            "name": s.name,
            "dise_code": s.dise_code,
            "total_students": student_count,
            "health_score": s.health_score,
        })

    return {
        "mandal_id": mandal_id,
        "total_schools": len(schools),
        "total_students": students_count,
        "high_risk_students": high_risk,
        "schools": sorted(schools_summary, key=lambda x: x["health_score"] or 0),
    }


@router.get("/school/{school_id}/performance")
async def school_performance(
    school_id: int,
    academic_year: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """School-level academic performance summary for HM dashboard."""
    total_students = (await db.execute(
        select(func.count(Student.id)).where(
            Student.school_id == school_id,
            Student.academic_year == academic_year,
            Student.is_active == True,
        )
    )).scalar_one()

    risk_breakdown = await db.execute(
        select(Student.risk_level, func.count(Student.id).label("count")).where(
            Student.school_id == school_id, Student.academic_year == academic_year
        ).group_by(Student.risk_level)
    )
    risk_data = {row.risk_level.value: row.count for row in risk_breakdown.all()}

    today = date.today()
    att_summary = await db.execute(
        select(
            Attendance.status, func.count(Attendance.id).label("count")
        ).where(
            and_(
                Attendance.school_id == school_id,
                Attendance.date >= today - timedelta(days=30),
                Attendance.reference_type == AttendanceReferenceType.STUDENT,
            )
        ).group_by(Attendance.status)
    )
    att_data = {row.status.value: row.count for row in att_summary.all()}
    total_att = sum(att_data.values())
    present_att = att_data.get("PRESENT", 0) + att_data.get("LATE", 0)
    att_rate = round((present_att / total_att * 100) if total_att else 0, 2)

    return {
        "school_id": school_id,
        "academic_year": academic_year,
        "total_students": total_students,
        "attendance_rate_30d": att_rate,
        "risk_breakdown": risk_data,
    }
