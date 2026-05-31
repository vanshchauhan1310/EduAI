"""DEO Admin Copilot API routes - District Intelligence, Risk Monitor, Teacher Rationalization, Communications."""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO

from app.database.session import get_db
from app.core.dependencies import get_current_user, require_deo
from app.models.user import User
from app.schemas.deo_copilot import (
    DistrictBriefResponse, RiskMonitorResponse,
    TeacherRationalizationResponse, RationalizationPlanRequest,
    CommunicationGenerateRequest, CommunicationGenerateResponse,
    CommunicationTemplateInfo, CommunicationHistoryItem,
)
from app.services.district_intelligence_service import DistrictIntelligenceService
from app.services.risk_monitor_service import RiskMonitorService
from app.services.teacher_rationalization_service import TeacherRationalizationService
from app.services.communication_service import CommunicationService
from app.utils.deo_pdf_generator import generate_deo_report_pdf, generate_deo_report_docx

router = APIRouter(prefix="/deo", tags=["DEO Admin Copilot"])


# ─── Module 1: District Intelligence Briefing ─────────────────────

@router.post("/intelligence-brief", response_model=DistrictBriefResponse, status_code=201)
async def generate_intelligence_brief(
    district_id: int, current_user: User = Depends(require_deo), db: AsyncSession = Depends(get_db),
):
    """Generate an AI-powered district intelligence briefing."""
    service = DistrictIntelligenceService(db)
    return await service.generate_brief(district_id, current_user)


@router.get("/intelligence-history", response_model=list[DistrictBriefResponse])
async def intelligence_history(
    district_id: int, limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_deo), db: AsyncSession = Depends(get_db),
):
    service = DistrictIntelligenceService(db)
    return await service.get_history(district_id, current_user, limit)


@router.get("/intelligence/{brief_id}", response_model=DistrictBriefResponse)
async def get_intelligence_brief(
    brief_id: int, current_user: User = Depends(require_deo), db: AsyncSession = Depends(get_db),
):
    service = DistrictIntelligenceService(db)
    return await service.get_by_id(brief_id, current_user)


# ─── Module 2: Mandal Performance ─────────────────────────────────

@router.get("/mandal-performance")
async def mandal_performance(
    district_id: int, current_user: User = Depends(require_deo), db: AsyncSession = Depends(get_db),
):
    """Get performance metrics for all mandals in the district."""
    from sqlalchemy import select, func
    from app.models.school import Mandal, School
    from app.models.student import Student, RiskLevel

    mandals = (await db.execute(select(Mandal).where(Mandal.district_id == district_id))).scalars().all()
    results = []
    for m in mandals:
        schools = (await db.execute(select(School).where(School.mandal_id == m.id, School.is_active == True))).scalars().all()
        school_count = len(schools)
        total_students = 0
        avg_health = 0
        for s in schools:
            sc = (await db.execute(select(func.count(Student.id)).where(Student.school_id == s.id, Student.is_active == True))).scalar_one() or 0
            total_students += sc
            avg_health += (s.health_score or 50)
        avg_health = round(avg_health / max(1, school_count), 1)
        results.append({
            "mandal_id": m.id, "mandal_name": m.name,
            "schools": school_count, "students": total_students,
            "avg_health_score": avg_health,
        })
    results.sort(key=lambda x: x["avg_health_score"], reverse=True)
    best = results[0]["mandal_name"] if results else "N/A"
    worst = results[-1]["mandal_name"] if results else "N/A"
    return {"district_id": district_id, "mandals": results, "best_performing": best, "worst_performing": worst}


# ─── Module 3: District Risk Monitor ──────────────────────────────

@router.post("/risk-monitor", response_model=RiskMonitorResponse, status_code=201)
async def scan_risk_monitor(
    district_id: int, current_user: User = Depends(require_deo), db: AsyncSession = Depends(get_db),
):
    """Scan district for risks and generate AI analysis."""
    service = RiskMonitorService(db)
    return await service.scan_risks(district_id, current_user)


@router.get("/risk-history")
async def risk_history(
    district_id: int, limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_deo), db: AsyncSession = Depends(get_db),
):
    service = RiskMonitorService(db)
    return await service.get_history(district_id, current_user, limit)


# ─── Module 4: Teacher Rationalization ────────────────────────────

@router.get("/teacher-rationalization", response_model=TeacherRationalizationResponse)
async def get_teacher_rationalization(
    district_id: int, current_user: User = Depends(require_deo), db: AsyncSession = Depends(get_db),
):
    """Analyze teacher allocation across the district and save a plan for export."""
    service = TeacherRationalizationService(db)
    return await service.analyze(district_id, current_user, save_plan=True)


@router.post("/generate-rationalization-plan", response_model=TeacherRationalizationResponse, status_code=201)
async def generate_rationalization_plan(
    request: RationalizationPlanRequest, current_user: User = Depends(require_deo), db: AsyncSession = Depends(get_db),
):
    """Generate and save a teacher rationalization plan."""
    service = TeacherRationalizationService(db)
    district_id = request.district_id or current_user.district_id
    return await service.generate_plan(district_id, current_user, request.context or "")


# ─── Module 5: Governance Communication Assistant ─────────────────

@router.get("/communication-templates", response_model=list[CommunicationTemplateInfo])
async def list_communication_templates(current_user: User = Depends(require_deo)):
    """List all available communication templates."""
    service = CommunicationService(None)  # type: ignore
    return service.list_templates()


@router.post("/generate-communication", response_model=CommunicationGenerateResponse, status_code=201)
async def generate_communication(
    request: CommunicationGenerateRequest, current_user: User = Depends(require_deo), db: AsyncSession = Depends(get_db),
):
    """Generate an official communication from a template."""
    service = CommunicationService(db)
    return await service.generate(request, current_user)


@router.get("/communication-history", response_model=list[CommunicationHistoryItem])
async def communication_history(
    limit: int = Query(20, ge=1, le=100), current_user: User = Depends(require_deo), db: AsyncSession = Depends(get_db),
):
    service = CommunicationService(db)
    return await service.get_history(current_user, limit)


# ─── Export Endpoints ─────────────────────────────────────────────

@router.get("/intelligence-brief/{brief_id}/export/{format}")
async def export_intelligence_brief(
    brief_id: int, format: str,
    current_user: User = Depends(require_deo), db: AsyncSession = Depends(get_db),
):
    """Export intelligence brief as PDF or DOCX."""
    service = DistrictIntelligenceService(db)
    brief = await service.get_by_id(brief_id, current_user)
    
    content = brief.content.get("ai_briefing", "") if brief.content else ""
    title = f"District Intelligence Brief - {brief.district_name}"
    reference = f"BRIEF-{brief_id}"
    
    if format.lower() == "pdf":
        pdf_bytes = generate_deo_report_pdf(content, "intelligence_brief", title, reference)
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=intelligence_brief_{brief_id}.pdf"})
    elif format.lower() == "docx":
        docx_bytes = generate_deo_report_docx(content, "intelligence_brief", title, reference)
        return Response(content=docx_bytes, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f"attachment; filename=intelligence_brief_{brief_id}.docx"})
    return Response(status_code=400, content="Invalid format")


@router.get("/mandal-performance/export/{format}")
async def export_mandal_performance(
    district_id: int, format: str,
    current_user: User = Depends(require_deo), db: AsyncSession = Depends(get_db),
):
    """Export mandal performance report as PDF or DOCX."""
    from sqlalchemy import select, func
    from app.models.school import Mandal, School
    from app.models.student import Student
    
    mandals = (await db.execute(select(Mandal).where(Mandal.district_id == district_id))).scalars().all()
    results = []
    for m in mandals:
        schools = (await db.execute(select(School).where(School.mandal_id == m.id, School.is_active == True))).scalars().all()
        school_count = len(schools)
        total_students = 0
        avg_health = 0
        for s in schools:
            sc = (await db.execute(select(func.count(Student.id)).where(Student.school_id == s.id, Student.is_active == True))).scalar_one() or 0
            total_students += sc
            avg_health += (s.health_score or 50)
        avg_health = round(avg_health / max(1, school_count), 1)
        results.append({"mandal_name": m.name, "schools": school_count, "students": total_students, "avg_health_score": avg_health})
    
    results.sort(key=lambda x: x["avg_health_score"], reverse=True)
    
    content_lines = [
        f"District ID: {district_id}",
        "",
        "BEST PERFORMING:",
        f"  {results[0]['mandal_name']} (Score: {results[0]['avg_health_score']})" if results else "  N/A",
        "",
        "NEEDS ATTENTION:",
        f"  {results[-1]['mandal_name']} (Score: {results[-1]['avg_health_score']})" if results else "  N/A",
        "",
        "MANDAL RANKINGS:",
    ]
    for i, m in enumerate(results):
        content_lines.append(f"  #{i+1} {m['mandal_name']} - Schools: {m['schools']} | Students: {m['students']} | Score: {m['avg_health_score']}")
    
    content = "\n".join(content_lines)
    title = "Mandal Performance Report"
    
    if format.lower() == "pdf":
        pdf_bytes = generate_deo_report_pdf(content, "mandal_performance", title)
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=mandal_performance_{district_id}.pdf"})
    elif format.lower() == "docx":
        docx_bytes = generate_deo_report_docx(content, "mandal_performance", title)
        return Response(content=docx_bytes, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f"attachment; filename=mandal_performance_{district_id}.docx"})
    return Response(status_code=400, content="Invalid format")


@router.get("/risk-monitor/{scan_id}/export/{format}")
async def export_risk_monitor(
    scan_id: int, format: str,
    current_user: User = Depends(require_deo), db: AsyncSession = Depends(get_db),
):
    """Export risk monitor report as PDF or DOCX."""
    from sqlalchemy import select
    from app.models.deo_copilot import RiskScan, RiskAlert
    
    scan = await db.get(RiskScan, scan_id)
    if not scan or scan.user_id != current_user.id:
        return Response(status_code=404, content="Not found")
    
    alerts = (await db.execute(select(RiskAlert).where(RiskAlert.scan_id == scan_id).limit(10))).scalars().all()
    
    content_lines = [
        f"District Risk Monitor Report",
        f"Date: {scan.created_at.strftime('%d-%m-%Y')}" if scan.created_at else "",
        "",
        "RISK SUMMARY:",
        f"  Critical Schools: {scan.critical_schools}",
        f"  High Risk Mandals: {scan.high_risk_mandals}",
        "",
        "AI RISK ANALYSIS:",
        scan.ai_analysis or "No analysis available",
        "",
        "ACTIVE ALERTS:",
    ]
    for a in alerts:
        content_lines.append(f"  [{a.severity}] {a.title}")
        if a.description:
            content_lines.append(f"    {a.description}")
    
    content = "\n".join(content_lines)
    title = "District Risk Monitor Report"
    reference = f"RISK-{scan_id}"
    
    if format.lower() == "pdf":
        pdf_bytes = generate_deo_report_pdf(content, "risk_monitor", title, reference)
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=risk_monitor_{scan_id}.pdf"})
    elif format.lower() == "docx":
        docx_bytes = generate_deo_report_docx(content, "risk_monitor", title, reference)
        return Response(content=docx_bytes, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f"attachment; filename=risk_monitor_{scan_id}.docx"})
    return Response(status_code=400, content="Invalid format")


@router.get("/teacher-rationalization/{plan_id}/export/{format}")
async def export_teacher_rationalization(
    plan_id: int, format: str,
    current_user: User = Depends(require_deo), db: AsyncSession = Depends(get_db),
):
    """Export teacher rationalization report as PDF or DOCX."""
    from app.models.deo_copilot import TeacherRationalizationPlan
    
    plan = await db.get(TeacherRationalizationPlan, plan_id)
    if not plan or plan.user_id != current_user.id:
        return Response(status_code=404, content="Not found")
    
    plan_data = plan.plan_data or {}
    schools = plan_data.get("schools", [])
    district_name = plan_data.get("district_name", "")
    
    content_lines = [
        f"Teacher Rationalization Report",
        f"District: {district_name}" if district_name else "",
        f"Date: {plan.created_at.strftime('%d-%m-%Y')}" if plan.created_at else "",
        "",
        "SUMMARY:",
        f"  Surplus Teachers: {plan.total_surplus}",
        f"  Deficit Teachers: {plan.total_deficit}",
        f"  Schools Analyzed: {plan.schools_analyzed}",
        "",
        "AI RECOMMENDATIONS:",
        plan.ai_recommendations or "No recommendations available",
        "",
        "SCHOOL DETAILS:",
    ]
    for s in schools[:20]:
        content_lines.append(f"  {s.get('school_name', '')} [{s.get('priority', '')}]")
        content_lines.append(f"    Students: {s.get('enrollment', 0)} | Teachers: {s.get('current_teachers', 0)} | Required: {s.get('required_teachers', 0)} | Shortage: {s.get('shortage', 0)} | Surplus: {s.get('surplus', 0)}")
    
    content = "\n".join(content_lines)
    title = f"Teacher Rationalization Report - {district_name}" if district_name else "Teacher Rationalization Report"
    reference = f"TR-{plan_id}"
    
    if format.lower() == "pdf":
        pdf_bytes = generate_deo_report_pdf(content, "teacher_rationalization", title, reference)
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=teacher_rationalization_{plan_id}.pdf"})
    elif format.lower() == "docx":
        docx_bytes = generate_deo_report_docx(content, "teacher_rationalization", title, reference)
        return Response(content=docx_bytes, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f"attachment; filename=teacher_rationalization_{plan_id}.docx"})
    return Response(status_code=400, content="Invalid format")


@router.get("/communication/{comm_id}/export/{format}")
async def export_communication(
    comm_id: int, format: str,
    current_user: User = Depends(require_deo), db: AsyncSession = Depends(get_db),
):
    """Export communication as PDF or DOCX."""
    from app.models.deo_copilot import DistrictCommunication
    
    comm = await db.get(DistrictCommunication, comm_id)
    if not comm or comm.user_id != current_user.id:
        return Response(status_code=404, content="Not found")
    
    content_lines = [
        f"Official Communication",
        f"Subject: {comm.subject}",
        f"Reference: {comm.reference_number}",
        f"Priority: {comm.priority}",
        f"Date: {comm.created_at.strftime('%d-%m-%Y')}" if comm.created_at else "",
        f"To: {comm.target_audience}",
        "",
        comm.content or "No content available",
    ]
    content = "\n".join(content_lines)
    title = comm.subject or "Official Communication"
    reference = comm.reference_number
    
    if format.lower() == "pdf":
        pdf_bytes = generate_deo_report_pdf(content, "communication", title, reference)
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=communication_{comm_id}.pdf"})
    elif format.lower() == "docx":
        docx_bytes = generate_deo_report_docx(content, "communication", title, reference)
        return Response(content=docx_bytes, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f"attachment; filename=communication_{comm_id}.docx"})
    return Response(status_code=400, content="Invalid format")