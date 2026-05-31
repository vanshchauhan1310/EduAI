"""Governance Communication Service - Generate official district communications."""
from datetime import date
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.deo_copilot import DistrictCommunication
from app.models.school import District
from app.models.user import User
from app.schemas.deo_copilot import (
    CommunicationGenerateRequest, CommunicationGenerateResponse,
    CommunicationHistoryItem, CommunicationTemplateInfo,
)
from app.utils.gemini_client import generate_text

COMMUNICATION_TEMPLATES = {
    "notice_to_meos": {"name": "Notice to MEOs", "description": "Official notice for Mandal Education Officers", "fields": [
        {"key": "subject", "label": "Subject", "type": "text", "required": True},
        {"key": "message", "label": "Message/Instructions", "type": "textarea", "required": True},
        {"key": "deadline", "label": "Deadline", "type": "date", "required": False},
        {"key": "priority", "label": "Priority", "type": "select", "options": ["URGENT", "HIGH", "MEDIUM"], "required": True},
    ]},
    "compliance_reminder": {"name": "Compliance Reminder", "description": "Send compliance deadline reminders", "fields": [
        {"key": "compliance_type", "label": "Compliance Type", "type": "text", "required": True},
        {"key": "deadline", "label": "Compliance Deadline", "type": "date", "required": True},
        {"key": "details", "label": "Details", "type": "textarea", "required": True},
        {"key": "target_audience", "label": "Target Audience", "type": "text", "required": True},
    ]},
    "district_circular": {"name": "District Circular", "description": "Issue a formal district circular", "fields": [
        {"key": "subject", "label": "Subject", "type": "text", "required": True},
        {"key": "content", "label": "Circular Content", "type": "textarea", "required": True},
        {"key": "target_audience", "label": "Target Audience", "type": "text", "required": True},
        {"key": "priority", "label": "Priority", "type": "select", "options": ["URGENT", "HIGH", "MEDIUM"], "required": True},
    ]},
    "attendance_directive": {"name": "Attendance Improvement Directive", "description": "Mandate attendance improvement measures", "fields": [
        {"key": "mandal_names", "label": "Affected Mandals", "type": "textarea", "required": True},
        {"key": "current_rate", "label": "Current Attendance Rate (%)", "type": "number", "required": True},
        {"key": "target_rate", "label": "Target Attendance Rate (%)", "type": "number", "required": True},
        {"key": "deadline", "label": "Improvement Deadline", "type": "date", "required": True},
    ]},
    "teacher_deployment_order": {"name": "Teacher Deployment Order", "description": "Issue teacher deployment instructions", "fields": [
        {"key": "subject", "label": "Order Subject", "type": "text", "required": True},
        {"key": "deployment_details", "label": "Deployment Details", "type": "textarea", "required": True},
        {"key": "effective_date", "label": "Effective Date", "type": "date", "required": True},
        {"key": "priority", "label": "Priority", "type": "select", "options": ["URGENT", "HIGH", "MEDIUM"], "required": True},
    ]},
    "inspection_directive": {"name": "Inspection Directive", "description": "Schedule and mandate inspections", "fields": [
        {"key": "inspection_type", "label": "Inspection Type", "type": "text", "required": True},
        {"key": "target_schools", "label": "Target Schools/Mandals", "type": "textarea", "required": True},
        {"key": "inspection_date", "label": "Inspection Date", "type": "date", "required": True},
        {"key": "inspectors", "label": "Designated Inspectors", "type": "textarea", "required": False},
    ]},
    "scheme_review_notice": {"name": "Scheme Review Notice", "description": "Call for scheme implementation review", "fields": [
        {"key": "scheme_name", "label": "Scheme Name", "type": "text", "required": True},
        {"key": "review_period", "label": "Review Period", "type": "text", "required": True},
        {"key": "target_audience", "label": "Target Audience", "type": "text", "required": True},
        {"key": "specific_instructions", "label": "Specific Instructions", "type": "textarea", "required": False},
    ]},
    "escalation_communication": {"name": "Escalation Communication", "description": "Escalate critical issues to higher authorities", "fields": [
        {"key": "issue_title", "label": "Issue Title", "type": "text", "required": True},
        {"key": "issue_details", "label": "Issue Details", "type": "textarea", "required": True},
        {"key": "severity", "label": "Severity", "type": "select", "options": ["CRITICAL", "HIGH", "MEDIUM"], "required": True},
        {"key": "action_taken", "label": "Action Already Taken", "type": "textarea", "required": False},
    ]},
}

COMMUNICATION_PROMPT = """You are a DEO AI communication assistant for Government of Andhra Pradesh. Generate an OFFICIAL {communication_type} communication.
District: {district_name}, Date: {comm_date}
Communication Type: {communication_type}
Priority: {priority}
Target Audience: {target_audience}
Input Details:
{input_details}
Generate a formal government communication with:
1) Header (GOVERNMENT OF ANDHRA PRADESH)
2) Reference Number (auto-generate)
3) Subject line
4) To/From/Date
5) Body content with clear instructions
6) Action required and deadlines
7) Signature block
Use formal, authoritative government language. Return plain text only."""


def _build_reference_number(comm_type: str) -> str:
    import uuid
    prefix_map = {
        "notice_to_meos": "DEO/NOT",
        "compliance_reminder": "DEO/COM",
        "district_circular": "DEO/CIR",
        "attendance_directive": "DEO/ATT",
        "teacher_deployment_order": "DEO/DEP",
        "inspection_directive": "DEO/INS",
        "scheme_review_notice": "DEO/SCR",
        "escalation_communication": "DEO/ESC",
    }
    short_id = uuid.uuid4().hex[:5].upper()
    return f"{prefix_map.get(comm_type, 'DEO/GEN')}/{date.today().year}/{short_id}"


class CommunicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def list_templates(self) -> list[CommunicationTemplateInfo]:
        return [CommunicationTemplateInfo(key=k, name=v["name"], description=v["description"], fields=v["fields"]) for k, v in COMMUNICATION_TEMPLATES.items()]

    async def generate(self, request: CommunicationGenerateRequest, user: User) -> CommunicationGenerateResponse:
        template = COMMUNICATION_TEMPLATES.get(request.communication_type)
        if not template:
            raise HTTPException(status_code=400, detail=f"Unknown template: {request.communication_type}")

        # Get district name
        district_id = user.district_id
        district = await self.db.get(District, district_id) if district_id else None
        district_name = district.name if district else "District"

        fields = request.template_fields
        comm_type_display = template["name"]
        priority = fields.get("priority", "HIGH")
        target_audience = fields.get("target_audience", "All MEOs and HMs")
        input_details = "\n".join(f"- {k}: {v}" for k, v in fields.items() if v)

        prompt = COMMUNICATION_PROMPT.format(
            communication_type=comm_type_display, district_name=district_name,
            comm_date=date.today().strftime("%d-%m-%Y"), priority=priority,
            target_audience=target_audience, input_details=input_details,
        )
        subject = fields.get("subject", fields.get("issue_title", fields.get("scheme_name", comm_type_display)))
        try:
            content = await generate_text(prompt)
        except Exception:
            content = (
                f"OFFICIAL COMMUNICATION - {comm_type_display}\n\n"
                f"GOVERNMENT OF ANDHRA PRADESH\n"
                f"District Education Officer - {district_name}\n\n"
                f"Date: {date.today().strftime('%d-%m-%Y')}\n"
                f"Priority: {priority}\n"
                f"To: {target_audience}\n\n"
                f"Subject: {subject}\n\n"
                f"Details:\n{input_details}\n\n"
                f"Note: AI-generated detailed communication temporarily unavailable."
            )
        ref_no = _build_reference_number(request.communication_type)

        record = DistrictCommunication(
            user_id=user.id, district_id=district_id or 0,
            communication_type=request.communication_type,
            subject=subject, priority=priority,
            target_audience=target_audience, content=content,
            reference_number=ref_no,
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)

        return CommunicationGenerateResponse(
            id=record.id, communication_type=record.communication_type,
            subject=record.subject, priority=record.priority,
            target_audience=record.target_audience, content=content,
            reference_number=ref_no, created_at=str(record.created_at),
        )

    async def get_history(self, user: User, limit: int = 20):
        result = await self.db.execute(
            select(DistrictCommunication).where(DistrictCommunication.user_id == user.id)
            .order_by(DistrictCommunication.created_at.desc()).limit(limit)
        )
        return [CommunicationHistoryItem(id=r.id, communication_type=r.communication_type, subject=r.subject, priority=r.priority, created_at=str(r.created_at)) for r in result.scalars().all()]