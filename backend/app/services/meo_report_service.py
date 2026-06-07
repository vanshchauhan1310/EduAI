"""
MEO Report Generator Service.
Generates structured government-format reports from templates for MEO users.
Uses NVIDIA NIM AI to draft professional, realistic official reports.
"""
import shortuuid
from datetime import date
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.copilot import GeneratedMEOReport
from app.models.school import Mandal
from app.models.user import User
from app.schemas.copilot import (
    MEOReportGenerateRequest, MEOReportGenerateResponse,
    MEOReportHistoryItem, MEOTemplateInfo,
)
from app.utils.gemini_client import generate_text
from app.utils.meo_pdf_generator import generate_meo_report_pdf, generate_meo_report_docx


# ─── MEO Template Definitions ─────────────────────────────────────
# NOTE: mandal_name, district_name, and meo_name are auto-populated from
# the user's profile / database. They are NOT included as form fields.

MEO_REPORT_TEMPLATES: dict[str, dict] = {
    "early_warning": {
        "name": "Early Warning Briefing",
        "description": "Generate a formal early warning briefing on school health, attendance, dropout risks, and critical incidents for the mandal.",
        "fields": [
            {"key": "reporting_month", "label": "Reporting Month/Period",    "type": "text",   "required": True, "default": date.today().strftime("%B %Y")},
            {"key": "schools_monitored","label": "Number of Schools Monitored","type": "number","required": True},
            {"key": "critical_incidents","label": "Critical Incidents (if any)", "type": "textarea","required": False},
            {"key": "attendance_concern","label": "Attendance Concerns / Observations","type": "textarea","required": False},
            {"key": "dropout_alerts",  "label": "Dropout Risk Alerts",       "type": "textarea","required": False},
            {"key": "contact_phone",   "label": "MEO Contact Phone",        "type": "text",   "required": False},
        ],
    },
    "teacher_vacancy": {
        "name": "Teacher Vacancy & Deployment Report",
        "description": "Generate a detailed teacher vacancy analysis and deployment recommendation report for the mandal.",
        "fields": [
            {"key": "report_date",      "label": "Report Date",               "type": "date",   "required": True, "default": date.today().strftime("%Y-%m-%d")},
            {"key": "total_schools",    "label": "Total Schools in Mandal",   "type": "number", "required": True},
            {"key": "sanctioned_posts", "label": "Total Sanctioned Teacher Posts","type": "number","required": True},
            {"key": "filled_posts",     "label": "Currently Filled Posts",    "type": "number", "required": True},
            {"key": "vacant_posts",     "label": "Vacant Posts",              "type": "number", "required": True},
            {"key": "subject_shortages","label": "Subject-wise Shortages (e.g. Maths: 5, Science: 3)", "type": "textarea", "required": False},
        ],
    },
    "governance_communication": {
        "name": "Governance Communication Draft",
        "description": "Draft a formal governance communication / circular for distribution to all schools in the mandal.",
        "fields": [
            {"key": "communication_date",   "label": "Communication Date",        "type": "date",   "required": True, "default": date.today().strftime("%Y-%m-%d")},
            {"key": "subject",              "label": "Subject / Title",           "type": "text",   "required": True},
            {"key": "key_message",          "label": "Key Message / Purpose",     "type": "textarea","required": True},
            {"key": "target_audience",      "label": "Target Audience (e.g. All HM, All Teachers)", "type": "text", "required": True},
            {"key": "deadline_actions",     "label": "Action Deadlines (if any)", "type": "textarea","required": False},
            {"key": "meo_designation",      "label": "MEO Designation",           "type": "text",   "required": False, "default": "Mandal Education Officer"},
        ],
    },
    "cluster_briefing": {
        "name": "Cluster Governance Briefing",
        "description": "Generate a comprehensive cluster governance briefing with school health, attendance, teacher deployment and priority actions.",
        "fields": [
            {"key": "briefing_period",       "label": "Briefing Period",           "type": "text",   "required": True, "default": date.today().strftime("%B %Y")},
            {"key": "total_schools",         "label": "Total Schools in Cluster",  "type": "number", "required": True},
            {"key": "schools_visited",       "label": "Schools Visited This Period","type": "number","required": False},
            {"key": "key_achievements",      "label": "Key Achievements / Highlights", "type": "textarea","required": False},
            {"key": "key_challenges",        "label": "Key Challenges / Gaps",     "type": "textarea","required": False},
            {"key": "infrastructure_status", "label": "Infrastructure Status Summary", "type": "textarea","required": False},
            {"key": "deo_name",              "label": "DEO Name (for reference)",  "type": "text",   "required": False},
        ],
    },
}


# ─── MEO Prompt Templates ─────────────────────────────────────────

EARLY_WARNING_PROMPT = """You are a senior Mandal Education Officer for the Government of Andhra Pradesh, Department of School Education.

Generate a FORMAL GOVERNMENT EARLY WARNING BRIEFING REPORT based on the following details:

Mandal: {mandal_name}
District: {district_name}
Reporting Period: {reporting_month}
MEO Name: {meo_name}

Schools Monitored: {schools_monitored}
Critical Incidents Reported: {critical_incidents}
Attendance Observations: {attendance_concern}
Dropout Risk Alerts: {dropout_alerts}

OUTPUT FORMAT — Generate a structured government report with the following sections:
1. HEADER: Government of Andhra Pradesh, Department of School Education — Early Warning Briefing
2. REFERENCE NUMBER and DATE
3. MANDAL OVERVIEW: Brief summary of the mandal's current education status
4. EARLY WARNING SIGNALS: List specific risk signals identified (attendance drops, dropout risks, critical incidents)
5. URGENT ACTIONS REQUIRED (NEXT 7 DAYS): Bulleted list of immediate actions
6. RECOMMENDED MONITORING CHECKPOINTS: Key indicators to track
7. ESCALATION NOTES: When and how to escalate to DEO / District Office
8. SIGNATURE BLOCK: MEO Name, Designation, Date

Use formal government English language throughout. Return the complete report as plain text with clear section headings. Do NOT wrap in JSON or markdown fences."""


TEACHER_VACANCY_PROMPT = """You are a senior teacher deployment advisor for the Government of Andhra Pradesh, Department of School Education.

Generate a FORMAL GOVERNMENT TEACHER VACANCY & DEPLOYMENT REPORT based on the following details:

Mandal: {mandal_name}
District: {district_name}
Report Date: {report_date}
MEO Name: {meo_name}

Total Schools in Mandal: {total_schools}
Sanctioned Teacher Posts: {sanctioned_posts}
Currently Filled Posts: {filled_posts}
Vacant Posts: {vacant_posts}
Subject-wise Shortages: {subject_shortages}

OUTPUT FORMAT — Generate a structured government report with the following sections:
1. HEADER: Government of Andhra Pradesh, Department of School Education — Teacher Vacancy & Deployment Report
2. REFERENCE NUMBER and DATE
3. EXECUTIVE SUMMARY: Concise overview of the staffing situation
4. VACANCY ANALYSIS BY SCHOOL CATEGORY: Break down vacancies across primary, upper primary, high schools
5. SUBJECT-WISE SHORTAGE ANALYSIS: Specific subjects affected and severity
6. RECOMMENDED DEPLOYMENT STRATEGY: Specific recommendations for redistribution, recruitment priority, and temporary arrangements
7. TIMELINE FOR ACTION: Suggested timeline for filling vacancies (immediate, 30 days, 60 days)
8. STAKEHOLDER COMMUNICATION NOTES: Points for communicating with DEO, HR, and school HMs
9. SIGNATURE BLOCK: MEO Name, Designation, Date

Use formal government language. Return the complete report as plain text with clear section headings. Do NOT wrap in JSON or markdown fences."""


GOVERNANCE_COMMUNICATION_PROMPT = """You are a senior government communication officer for the Government of Andhra Pradesh, Department of School Education.

Draft a FORMAL GOVERNANCE COMMUNICATION / CIRCULAR based on the following details:

Mandal: {mandal_name}
District: {district_name}
Communication Date: {communication_date}
Subject: {subject}
Key Message: {key_message}
Target Audience: {target_audience}
Action Deadlines: {deadline_actions}
Issuing Officer: {meo_name}
Officer Designation: {meo_designation}

OUTPUT FORMAT — Generate a formal circular/communication with the following structure:
1. HEADER: Government of Andhra Pradesh, Department of School Education — OFFICIAL CIRCULAR
2. CIRCULAR REFERENCE NUMBER and DATE
3. TO: All Headmasters / Teachers / Officers in {mandal_name} Mandal
4. SUBJECT: [The subject line]
5. BACKGROUND / PREAMBLE: 2-3 sentences context
6. KEY INSTRUCTIONS / MESSAGE BODY: Numbered points with clear directives
7. COMPLIANCE AND DEADLINES: Specific action items with timelines
8. CONTACT / QUERIES: MEO office contact information
9. SIGNATURE BLOCK: MEO Name, Designation, Office Seal line

Use formal, authoritative government language. Return the complete circular as plain text. Do NOT wrap in JSON or markdown fences."""


CLUSTER_BRIEFING_PROMPT = """You are a senior governance analyst preparing a cluster briefing for the Government of Andhra Pradesh, Department of School Education.

Generate a COMPREHENSIVE CLUSTER GOVERNANCE BRIEFING based on the following details:

Cluster/Mandal: {mandal_name}
District: {district_name}
Briefing Period: {briefing_period}
MEO Name: {meo_name}
DEO Name: {deo_name}

Total Schools: {total_schools}
Schools Visited: {schools_visited}
Key Achievements: {key_achievements}
Key Challenges: {key_challenges}
Infrastructure Status: {infrastructure_status}

OUTPUT FORMAT — Generate a structured governance briefing with the following sections:
1. HEADER: Government of Andhra Pradesh, Department of School Education — CLUSTER GOVERNANCE BRIEFING
2. REFERENCE NUMBER and DATE
3. CURRENT STATUS HIGHLIGHTS: Positive developments and achievements in the cluster
4. SCHOOL HEALTH OVERVIEW: Summary of school health scores, attendance rates, and performance indicators
5. MAJOR RISKS AND VULNERABILITIES: List of key concerns requiring attention
6. TEACHER DEPLOYMENT STATUS: Staffing situation overview
7. RECOMMENDED GOVERNANCE FOCUS AREAS: Priority areas for the next period
8. SUGGESTED NEXT STEPS: Actionable items for MEO and DEO
9. SIGNATURE BLOCK: MEO Name, Designation, Date

Use formal government style. Return the complete briefing as plain text with clear section headings. Do NOT wrap in JSON or markdown fences."""


def _build_reference_number(report_type: str) -> str:
    prefix_map = {
        "early_warning":          "EDU/MEO/EW",
        "teacher_vacancy":        "EDU/MEO/TV",
        "governance_communication": "EDU/MEO/GC",
        "cluster_briefing":       "EDU/MEO/CB",
    }
    prefix = prefix_map.get(report_type, "EDU/MEO/GEN")
    year = date.today().year
    uid = shortuuid.ShortUUID().random(length=5).upper()
    return f"{prefix}/{year}/{uid}"


PROMPT_MAP = {
    "early_warning": EARLY_WARNING_PROMPT,
    "teacher_vacancy": TEACHER_VACANCY_PROMPT,
    "governance_communication": GOVERNANCE_COMMUNICATION_PROMPT,
    "cluster_briefing": CLUSTER_BRIEFING_PROMPT,
}


class MEOReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def list_templates(self) -> list[MEOTemplateInfo]:
        return [
            MEOTemplateInfo(
                key=k, name=v["name"],
                description=v["description"], fields=v["fields"],
            )
            for k, v in MEO_REPORT_TEMPLATES.items()
        ]

    async def _resolve_mandal(self, mandal_id: int | None, user: User) -> tuple[int, str]:
        resolved_id = mandal_id or user.mandal_id
        if not resolved_id:
            raise HTTPException(status_code=400, detail="Mandal assignment is required for MEO report features.")
        mandal = await self.db.get(Mandal, resolved_id)
        mandal_name = mandal.name if mandal else f"Mandal {resolved_id}"
        return resolved_id, mandal_name

    async def generate(self, request: MEOReportGenerateRequest, user: User) -> MEOReportGenerateResponse:
        template = MEO_REPORT_TEMPLATES.get(request.report_type)
        if not template:
            raise HTTPException(status_code=400, detail=f"Unknown MEO report type: {request.report_type}")

        prompt_template = PROMPT_MAP.get(request.report_type)
        if not prompt_template:
            raise HTTPException(status_code=500, detail=f"Prompt template not found for: {request.report_type}")

        # Resolve mandal and district for auto-filling user profile info
        mandal_id, mandal_name = await self._resolve_mandal(None, user)
        mandal_obj = await self.db.get(Mandal, mandal_id)
        district_name = ""
        if mandal_obj and mandal_obj.district_id:
            from app.models.school import District
            district_result = await self.db.execute(select(District).where(District.id == mandal_obj.district_id))
            district_obj = district_result.scalar_one_or_none()
            district_name = district_obj.name if district_obj else ""

        # Auto-populate user profile fields into template fields
        # These fields are NOT shown on the form; they are fetched server-side
        fields = request.template_fields.copy()
        fields["mandal_name"] = mandal_name
        fields["district_name"] = district_name
        fields["meo_name"] = user.full_name

        # Build prompt with template fields
        try:
            prompt = prompt_template.format(**fields)
        except KeyError as e:
            raise HTTPException(status_code=400, detail=f"Missing required field: {e}")

        # Generate content via AI
        content = await generate_text(prompt)
        ref_no = _build_reference_number(request.report_type)

        # Save to database
        record = GeneratedMEOReport(
            user_id=user.id,
            report_type=request.report_type,
            mandal_id=mandal_id,
            mandal_name=mandal_name,
            template_fields=fields,
            content=content,
            reference_number=ref_no,
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)

        return MEOReportGenerateResponse(
            id=record.id,
            report_type=record.report_type,
            mandal_id=record.mandal_id,
            mandal_name=record.mandal_name,
            reference_number=ref_no,
            content=content,
            created_at=str(record.created_at),
        )

    async def get_by_id(self, report_id: int, user: User) -> MEOReportGenerateResponse:
        result = await self.db.execute(
            select(GeneratedMEOReport).where(
                GeneratedMEOReport.id == report_id,
                GeneratedMEOReport.user_id == user.id,
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            raise HTTPException(status_code=404, detail="MEO report not found")
        return MEOReportGenerateResponse(
            id=record.id,
            report_type=record.report_type,
            mandal_id=record.mandal_id,
            mandal_name=record.mandal_name,
            reference_number=record.reference_number or "",
            content=record.content,
            created_at=str(record.created_at),
        )

    async def get_history(self, user: User, limit: int = 20) -> list[MEOReportHistoryItem]:
        result = await self.db.execute(
            select(GeneratedMEOReport)
            .where(GeneratedMEOReport.user_id == user.id)
            .order_by(desc(GeneratedMEOReport.created_at))
            .limit(limit)
        )
        return [
            MEOReportHistoryItem(
                id=r.id,
                report_type=r.report_type,
                reference_number=r.reference_number,
                mandal_name=r.mandal_name,
                created_at=str(r.created_at),
            )
            for r in result.scalars().all()
        ]

    async def export_pdf(self, report_id: int, user: User) -> bytes:
        resp = await self.get_by_id(report_id, user)
        return generate_meo_report_pdf(resp.content, resp.report_type, resp.reference_number)

    async def export_docx(self, report_id: int, user: User) -> bytes:
        resp = await self.get_by_id(report_id, user)
        return generate_meo_report_docx(resp.content, resp.report_type, resp.reference_number)