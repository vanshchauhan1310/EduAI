"""
Admin Copilot API routes.
All endpoints require authentication; HM, MEO, and DEO roles are allowed.
"""
from fastapi import APIRouter, Depends, File, UploadFile, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO

from app.database.session import get_db
from app.core.dependencies import get_current_user, require_exact_meo, require_hm
from app.models.user import User
from app.schemas.copilot import (
    LetterGenerateRequest, LetterGenerateResponse,
    ReportGenerateRequest, ReportGenerateResponse,
    SchoolHealthAnalyzerRequest, SchoolHealthAnalyzerResponse,
    MEOAssistantRequest, MEOAssistantResponse,
    TranslateRequest, TranslateResponse,
    CircularSummaryResponse,
    MEOReportGenerateRequest, MEOReportGenerateResponse,
    MEOReportHistoryItem, MEOTemplateInfo,
)
from app.services.circular_service import CircularService
from app.services.letter_service import LetterService
from app.services.report_service import ReportService
from app.services.school_health_analyzer_service import SchoolHealthAnalyzerService
from app.services.meo_assistant_service import MEOAssistantService
from app.services.meo_report_service import MEOReportService
from app.services.translation_service import TranslationService

router = APIRouter(prefix="/copilot", tags=["Admin Copilot"])


# ─── Circular Summarization ──────────────────────────────────────

@router.post("/summarize-circular", response_model=CircularSummaryResponse, status_code=201)
async def summarize_circular(
    file: UploadFile = File(..., description="Government circular PDF"),
    current_user: User = Depends(require_hm),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF circular and receive an AI-generated structured summary."""
    service = CircularService(db)
    return await service.summarize(file, current_user)


@router.get("/circulars/history")
async def circular_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_hm),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve summarization history for the current user."""
    service = CircularService(db)
    return await service.get_history(current_user, limit)


@router.get("/circulars/{summary_id}", response_model=CircularSummaryResponse)
async def get_circular_summary(
    summary_id: int,
    current_user: User = Depends(require_hm),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a previously generated circular summary."""
    service = CircularService(db)
    return await service.get_by_id(summary_id, current_user)


@router.get("/circulars/{summary_id}/export/pdf")
async def export_circular_pdf(
    summary_id: int,
    current_user: User = Depends(require_hm),
    db: AsyncSession = Depends(get_db),
):
    """Download a circular summary as a formatted PDF."""
    service = CircularService(db)
    pdf_bytes = await service.export_pdf(summary_id, current_user)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=circular_summary_{summary_id}.pdf"},
    )


# ─── Letter Generator ────────────────────────────────────────────

@router.get("/letters/templates")
async def list_letter_templates(current_user: User = Depends(require_hm)):
    """List all available letter templates with their required fields."""
    service = LetterService(None)  # type: ignore
    return service.list_templates()


@router.post("/generate-letter", response_model=LetterGenerateResponse, status_code=201)
async def generate_letter(
    request: LetterGenerateRequest,
    current_user: User = Depends(require_hm),
    db: AsyncSession = Depends(get_db),
):
    """Generate an official government letter from a selected template."""
    service = LetterService(db)
    return await service.generate(request, current_user)


@router.get("/letters/history")
async def letter_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_hm),
    db: AsyncSession = Depends(get_db),
):
    """Get generated letters history."""
    service = LetterService(db)
    return await service.get_history(current_user, limit)


@router.get("/letters/{letter_id}", response_model=LetterGenerateResponse)
async def get_letter(
    letter_id: int,
    current_user: User = Depends(require_hm),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a previously generated letter."""
    service = LetterService(db)
    return await service.get_by_id(letter_id, current_user)


@router.post("/export-letter/pdf")
async def export_letter_pdf(
    letter_id: int = Query(...),
    current_user: User = Depends(require_hm),
    db: AsyncSession = Depends(get_db),
):
    """Export a generated letter as PDF."""
    service = LetterService(db)
    pdf_bytes = await service.export_pdf(letter_id, current_user)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=letter_{letter_id}.pdf"},
    )


@router.post("/export-letter/docx")
async def export_letter_docx(
    letter_id: int = Query(...),
    current_user: User = Depends(require_hm),
    db: AsyncSession = Depends(get_db),
):
    """Export a generated letter as editable DOCX."""
    service = LetterService(db)
    docx_bytes = await service.export_docx(letter_id, current_user)
    return StreamingResponse(
        BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=letter_{letter_id}.docx"},
    )


# ─── Report Generator ────────────────────────────────────────────

@router.post("/generate-report", response_model=ReportGenerateResponse, status_code=201)
async def generate_report(
    request: ReportGenerateRequest,
    current_user: User = Depends(require_hm),
    db: AsyncSession = Depends(get_db),
):
    """Generate an analytics report from live database data using AI narration."""
    service = ReportService(db)
    return await service.generate(request, current_user)


@router.get("/reports/history")
async def report_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_hm),
    db: AsyncSession = Depends(get_db),
):
    """Get report generation history."""
    service = ReportService(db)
    return await service.get_history(current_user, limit)


@router.get("/reports/{report_id}", response_model=ReportGenerateResponse)
async def get_report(
    report_id: int,
    current_user: User = Depends(require_hm),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a previously generated report."""
    service = ReportService(db)
    return await service.get_by_id(report_id, current_user)


@router.get("/reports/{report_id}/export/pdf")
async def export_report_pdf(
    report_id: int,
    current_user: User = Depends(require_hm),
    db: AsyncSession = Depends(get_db),
):
    """Export a report as a structured PDF."""
    service = ReportService(db)
    pdf_bytes = await service.export_pdf(report_id, current_user)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"},
    )


@router.get("/reports/{report_id}/export/docx")
async def export_report_docx(
    report_id: int,
    current_user: User = Depends(require_hm),
    db: AsyncSession = Depends(get_db),
):
    """Export a report as an editable DOCX."""
    service = ReportService(db)
    docx_bytes = await service.export_docx(report_id, current_user)
    return StreamingResponse(
        BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.docx"},
    )


# ─── School Health Analyzer ───────────────────────────────────────

@router.post("/school-health-analyzer", response_model=SchoolHealthAnalyzerResponse, status_code=201)
async def analyze_school_health(
    request: SchoolHealthAnalyzerRequest,
    current_user: User = Depends(require_exact_meo),
    db: AsyncSession = Depends(get_db),
):
    """Generate a combined school health analysis for a cluster of MEO schools."""
    service = SchoolHealthAnalyzerService(db)
    return await service.analyze(request, current_user)


@router.get("/school-health-analyses")
async def school_health_analysis_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_exact_meo),
    db: AsyncSession = Depends(get_db),
):
    """Get school health analysis history."""
    from sqlalchemy import select as sel
    from app.models.copilot import GeneratedSchoolHealthAnalysis
    result = await db.execute(
        sel(GeneratedSchoolHealthAnalysis)
        .where(GeneratedSchoolHealthAnalysis.user_id == current_user.id)
        .order_by(GeneratedSchoolHealthAnalysis.created_at.desc())
        .limit(limit)
    )
    records = result.scalars().all()
    return [
        {
            "id": r.id,
            "mandal_id": r.mandal_id,
            "mandal_name": r.mandal_name,
            "selected_school_count": r.selected_school_count,
            "created_at": str(r.created_at),
        }
        for r in records
    ]


@router.get("/school-health-analyses/{analysis_id}", response_model=SchoolHealthAnalyzerResponse)
async def get_school_health_analysis(
    analysis_id: int,
    current_user: User = Depends(require_exact_meo),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a previously generated school health analysis."""
    from sqlalchemy import select as sel
    from app.models.copilot import GeneratedSchoolHealthAnalysis
    result = await db.execute(
        sel(GeneratedSchoolHealthAnalysis).where(
            GeneratedSchoolHealthAnalysis.id == analysis_id,
            GeneratedSchoolHealthAnalysis.user_id == current_user.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="School health analysis not found")
    return SchoolHealthAnalyzerResponse(
        id=record.id,
        mandal_id=record.mandal_id,
        mandal_name=record.mandal_name or '',
        selected_school_count=record.selected_school_count,
        cluster_insights=record.cluster_insights or '',
        strengths=record.strengths or [],
        concerns=record.concerns or [],
        recommendations=record.recommendations or [],
        action_plan=record.action_plan or [],
        top_school=record.top_school or '',
        most_at_risk_school=record.most_at_risk_school or '',
        school_breakdown=record.school_breakdown or [],
    )


@router.get("/school-health-analyses/{analysis_id}/export/pdf")
async def export_school_health_analysis_pdf(
    analysis_id: int,
    current_user: User = Depends(require_exact_meo),
    db: AsyncSession = Depends(get_db),
):
    """Export school health analysis as PDF."""
    from sqlalchemy import select as sel
    from app.models.copilot import GeneratedSchoolHealthAnalysis
    from app.utils.meo_pdf_generator import generate_school_health_pdf
    result = await db.execute(
        sel(GeneratedSchoolHealthAnalysis).where(
            GeneratedSchoolHealthAnalysis.id == analysis_id,
            GeneratedSchoolHealthAnalysis.user_id == current_user.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")
    report_data = {
        "mandal_name": record.mandal_name or '',
        "selected_school_count": record.selected_school_count,
        "cluster_insights": record.cluster_insights or '',
        "strengths": record.strengths or [],
        "concerns": record.concerns or [],
        "recommendations": record.recommendations or [],
        "action_plan": record.action_plan or [],
        "top_school": record.top_school or '',
        "most_at_risk_school": record.most_at_risk_school or '',
        "school_breakdown": record.school_breakdown or [],
    }
    pdf_bytes = generate_school_health_pdf(report_data)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=school_health_analysis_{analysis_id}.pdf"},
    )


@router.get("/school-health-analyses/{analysis_id}/export/docx")
async def export_school_health_analysis_docx(
    analysis_id: int,
    current_user: User = Depends(require_exact_meo),
    db: AsyncSession = Depends(get_db),
):
    """Export school health analysis as editable DOCX."""
    from sqlalchemy import select as sel
    from app.models.copilot import GeneratedSchoolHealthAnalysis
    from app.utils.meo_pdf_generator import generate_school_health_docx
    result = await db.execute(
        sel(GeneratedSchoolHealthAnalysis).where(
            GeneratedSchoolHealthAnalysis.id == analysis_id,
            GeneratedSchoolHealthAnalysis.user_id == current_user.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")
    report_data = {
        "mandal_name": record.mandal_name or '',
        "selected_school_count": record.selected_school_count,
        "cluster_insights": record.cluster_insights or '',
        "strengths": record.strengths or [],
        "concerns": record.concerns or [],
        "recommendations": record.recommendations or [],
        "action_plan": record.action_plan or [],
        "top_school": record.top_school or '',
        "most_at_risk_school": record.most_at_risk_school or '',
        "school_breakdown": record.school_breakdown or [],
    }
    docx_bytes = generate_school_health_docx(report_data)
    return StreamingResponse(
        BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=school_health_analysis_{analysis_id}.docx"},
    )


# ─── MEO Assistant (Legacy) ───────────────────────────────────────

@router.post("/early-warning-assistant", response_model=MEOAssistantResponse, status_code=201)
async def early_warning_assistant(
    request: MEOAssistantRequest,
    current_user: User = Depends(require_exact_meo),
    db: AsyncSession = Depends(get_db),
):
    """Generate a mandal-level early warning briefing for the MEO user."""
    service = MEOAssistantService(db)
    return await service.generate_early_warning(request, current_user)


@router.post("/teacher-vacancy-assistant", response_model=MEOAssistantResponse, status_code=201)
async def teacher_vacancy_assistant(
    request: MEOAssistantRequest,
    current_user: User = Depends(require_exact_meo),
    db: AsyncSession = Depends(get_db),
):
    """Generate teacher vacancy and deployment guidance for the MEO user."""
    service = MEOAssistantService(db)
    return await service.generate_teacher_vacancy_assistant(request, current_user)


@router.post("/governance-communication-assistant", response_model=MEOAssistantResponse, status_code=201)
async def governance_communication_assistant(
    request: MEOAssistantRequest,
    current_user: User = Depends(require_exact_meo),
    db: AsyncSession = Depends(get_db),
):
    """Generate a communication draft for MEO governance messaging."""
    service = MEOAssistantService(db)
    return await service.generate_governance_communication(request, current_user)


@router.post("/cluster-governance-briefing", response_model=MEOAssistantResponse, status_code=201)
async def cluster_governance_briefing(
    request: MEOAssistantRequest,
    current_user: User = Depends(require_exact_meo),
    db: AsyncSession = Depends(get_db),
):
    """Generate a cluster governance briefing for MEO review."""
    service = MEOAssistantService(db)
    return await service.generate_cluster_briefing(request, current_user)


# ─── MEO Template-based Report Generator ─────────────────────────

@router.get("/meo-reports/templates", response_model=list[MEOTemplateInfo])
async def list_meo_report_templates(
    current_user: User = Depends(require_exact_meo),
):
    """List all available MEO report templates with their required fields."""
    service = MEOReportService(None)  # type: ignore
    return service.list_templates()


@router.post("/meo-reports/generate", response_model=MEOReportGenerateResponse, status_code=201)
async def generate_meo_report(
    request: MEOReportGenerateRequest,
    current_user: User = Depends(require_exact_meo),
    db: AsyncSession = Depends(get_db),
):
    """Generate an official MEO report from a selected template using AI."""
    service = MEOReportService(db)
    return await service.generate(request, current_user)


@router.get("/meo-reports/history", response_model=list[MEOReportHistoryItem])
async def meo_report_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_exact_meo),
    db: AsyncSession = Depends(get_db),
):
    """Get MEO report generation history."""
    service = MEOReportService(db)
    return await service.get_history(current_user, limit)


@router.get("/meo-reports/{report_id}", response_model=MEOReportGenerateResponse)
async def get_meo_report(
    report_id: int,
    current_user: User = Depends(require_exact_meo),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a previously generated MEO report."""
    service = MEOReportService(db)
    return await service.get_by_id(report_id, current_user)


@router.get("/meo-reports/{report_id}/export/pdf")
async def export_meo_report_pdf(
    report_id: int,
    current_user: User = Depends(require_exact_meo),
    db: AsyncSession = Depends(get_db),
):
    """Export an MEO report as PDF."""
    service = MEOReportService(db)
    pdf_bytes = await service.export_pdf(report_id, current_user)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=meo_report_{report_id}.pdf"},
    )


@router.get("/meo-reports/{report_id}/export/docx")
async def export_meo_report_docx(
    report_id: int,
    current_user: User = Depends(require_exact_meo),
    db: AsyncSession = Depends(get_db),
):
    """Export an MEO report as editable DOCX."""
    service = MEOReportService(db)
    docx_bytes = await service.export_docx(report_id, current_user)
    return StreamingResponse(
        BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=meo_report_{report_id}.docx"},
    )


# ─── Translation ─────────────────────────────────────────────────

@router.post("/translate", response_model=TranslateResponse, status_code=201)
async def translate_text(
    request: TranslateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Translate text between Telugu and English."""
    service = TranslationService(db)
    return await service.translate(request, current_user)


@router.get("/translations/history")
async def translation_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get translation history for the current user."""
    service = TranslationService(db)
    return await service.get_history(current_user, limit)