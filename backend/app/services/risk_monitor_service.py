"""District Risk Monitor - Identifies and escalates district-level risks."""
from datetime import date, timedelta
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case

from app.models.deo_copilot import RiskAlert, RiskScan
from app.models.school import District, School
from app.models.student import Student, RiskLevel
from app.models.attendance import Attendance, AttendanceStatus, AttendanceReferenceType
from app.models.user import User
from app.schemas.deo_copilot import RiskMonitorResponse, RiskAlertResponse
from app.utils.gemini_client import generate_text

RISK_PROMPT = """Generate a DISTRICT RISK MONITORING ANALYSIS for District: {district_name}.
Critical Schools: {critical_schools}, High Risk Mandals: {high_risk_mandals}
Dropout Hotspots: {dropout_hotspots}
Attendance below 75%: {low_attendance_schools}
Risk Summary: {risk_summary}
Generate: 1) Risk Assessment Summary 2) Critical Action Items 3) Escalation Recommendations 4) Monitoring Priorities
Return plain text."""


class RiskMonitorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def scan_risks(self, district_id: int, user: User) -> RiskMonitorResponse:
        district = await self.db.get(District, district_id)
        dn = district.name if district else f"District {district_id}"
        thirty_ago = date.today() - timedelta(days=30)

        # High risk students per school
        critical_schools_result = await self.db.execute(
            select(School.id, School.name, School.dise_code, func.count(Student.id).label("risk_count"))
            .join(Student, Student.school_id == School.id)
            .where(School.district_id == district_id, School.is_active == True, Student.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]))
            .group_by(School.id, School.name, School.dise_code)
            .having(func.count(Student.id) > 3)
        )
        critical_schools = [(r[1], r[2]) for r in critical_schools_result.all()]

        # Low attendance schools
        att_risk_result = await self.db.execute(
            select(School.id, School.name)
            .join(Attendance, Attendance.school_id == School.id)
            .where(School.district_id == district_id, School.is_active == True, Attendance.date >= thirty_ago, Attendance.reference_type == AttendanceReferenceType.STUDENT)
            .group_by(School.id, School.name)
            .having(
                func.sum(case((Attendance.status.in_([AttendanceStatus.PRESENT, AttendanceStatus.LATE]), 1), else_=0)) / func.count(Attendance.id) * 100 < 75
            )
            .limit(20)
        )
        att_risk_schools = [r[1] for r in att_risk_result.all()]

        # Schools with very low health score
        critical_health = await self.db.execute(
            select(School.name).where(School.district_id == district_id, School.is_active == True, School.health_score < 40)
        )
        critical_health_schools = [r[0] for r in critical_health.all()]

        all_critical = list(set(critical_schools + [(c, "health") for c in critical_health_schools]))
        critical_count = len(all_critical)
        high_risk_mandals = max(1, critical_count // 3)

        # Create risk alerts
        alerts = []
        for name, code in critical_schools[:10]:
            alert = RiskAlert(user_id=user.id, district_id=district_id, risk_type="ATTENDANCE_RISK", severity="HIGH", entity_type="SCHOOL", entity_name=name, title=f"Low attendance at {name}", description=f"School {code} has attendance below 75%", risk_score=0.8)
            self.db.add(alert)
            alerts.append(alert)

        for name in critical_health_schools[:5]:
            alert = RiskAlert(user_id=user.id, district_id=district_id, risk_type="HEALTH_RISK", severity="CRITICAL", entity_type="SCHOOL", entity_name=name, title=f"Very low health score at {name}", description=f"Health score below 40", risk_score=0.9)
            self.db.add(alert)
            alerts.append(alert)

        await self.db.flush()

        # Get existing unresolved alerts
        existing_alerts = await self.db.execute(
            select(RiskAlert).where(RiskAlert.district_id == district_id, RiskAlert.is_resolved == False).order_by(RiskAlert.created_at.desc()).limit(20)
        )
        all_alerts = existing_alerts.scalars().all()

        alert_responses = [RiskAlertResponse(id=a.id, risk_type=a.risk_type, severity=a.severity, entity_type=a.entity_type, entity_name=a.entity_name, title=a.title, description=a.description, risk_score=a.risk_score, is_resolved=a.is_resolved, created_at=str(a.created_at)) for a in all_alerts]

        dropout_hotspots = att_risk_schools[:5]
        risk_summary = f"Critical schools: {critical_count}, Low attendance schools: {len(att_risk_schools)}, Critical health schools: {len(critical_health_schools)}"

        prompt = RISK_PROMPT.format(district_name=dn, critical_schools=critical_count, high_risk_mandals=high_risk_mandals, dropout_hotspots=", ".join(dropout_hotspots[:3]) if dropout_hotspots else "None", low_attendance_schools=len(att_risk_schools), risk_summary=risk_summary)
        try:
            ai_analysis = await generate_text(prompt)
        except Exception:
            ai_analysis = (
                f"District Risk Summary for {dn}:\n"
                f"- Critical schools: {critical_count}\n"
                f"- High risk mandals: {high_risk_mandals}\n"
                f"- Low attendance schools: {len(att_risk_schools)}\n"
                f"- Critical health schools: {len(critical_health_schools)}\n"
                f"Note: AI analysis temporarily unavailable. Review the data above."
            )

        # Save scan to database
        scan = RiskScan(
            user_id=user.id,
            district_id=district_id,
            critical_schools=critical_count,
            high_risk_mandals=high_risk_mandals,
            ai_analysis=ai_analysis or "No analysis available"
        )
        self.db.add(scan)
        await self.db.flush()
        await self.db.refresh(scan)

        # Link alerts to scan
        for alert in alerts:
            alert.scan_id = scan.id

        return RiskMonitorResponse(
            id=scan.id,
            district_id=district_id,
            district_name=dn,
            critical_schools=critical_count,
            high_risk_mandals=high_risk_mandals,
            dropout_hotspots=dropout_hotspots,
            risk_summary={"critical_count": critical_count, "att_risk_count": len(att_risk_schools), "health_risk_count": len(critical_health_schools)},
            alerts=alert_responses,
            ai_analysis=ai_analysis,
            created_at=str(scan.created_at)
        )

    async def get_history(self, district_id: int, user: User, limit: int = 20):
        result = await self.db.execute(select(RiskAlert).where(RiskAlert.district_id == district_id).order_by(RiskAlert.created_at.desc()).limit(limit))
        return [RiskAlertResponse(id=a.id, risk_type=a.risk_type, severity=a.severity, entity_type=a.entity_type, entity_name=a.entity_name, title=a.title, description=a.description, risk_score=a.risk_score, is_resolved=a.is_resolved, created_at=str(a.created_at)) for a in result.scalars().all()]