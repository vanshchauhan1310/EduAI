"""
Official Letter Generator Service.
Uses NVIDIA NIM to draft government-format letters from structured templates.
"""
import shortuuid
from datetime import date
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.copilot import GeneratedLetter
from app.models.user import User
from app.schemas.copilot import (
    LetterGenerateRequest, LetterGenerateResponse,
    LetterHistoryItem, LetterTemplateInfo,
)
from app.utils.gemini_client import generate_text, LETTER_GENERATION_PROMPT
from app.utils.pdf_generator import generate_letter_pdf
from app.utils.docx_generator import generate_letter_docx


# ─── Template Definitions ────────────────────────────────────────

LETTER_TEMPLATES: dict[str, dict] = {
    "leave_approval": {
        "name": "Leave Approval Letter",
        "description": "Approve or acknowledge a teacher's leave request",
        "fields": [
            {"key": "teacher_name",  "label": "Teacher Name",        "type": "text",   "required": True},
            {"key": "designation",   "label": "Designation",         "type": "text",   "required": True},
            {"key": "leave_type",    "label": "Leave Type",          "type": "select", "options": ["Casual Leave", "Medical Leave", "Earned Leave", "Maternity Leave"], "required": True},
            {"key": "leave_days",    "label": "Number of Days",       "type": "number", "required": True},
            {"key": "from_date",     "label": "From Date",           "type": "date",   "required": True},
            {"key": "to_date",       "label": "To Date",             "type": "date",   "required": True},
            {"key": "reason",        "label": "Reason",              "type": "textarea","required": True},
            {"key": "school_name",   "label": "School Name",         "type": "text",   "required": True},
            {"key": "hm_name",       "label": "Headmaster Name",     "type": "text",   "required": True},
        ],
    },
    "teacher_transfer": {
        "name": "Teacher Transfer Request",
        "description": "Request transfer of a teacher to another school",
        "fields": [
            {"key": "teacher_name",    "label": "Teacher Name",         "type": "text", "required": True},
            {"key": "current_school",  "label": "Current School",       "type": "text", "required": True},
            {"key": "requested_school","label": "Requested School",     "type": "text", "required": True},
            {"key": "designation",     "label": "Designation",          "type": "text", "required": True},
            {"key": "years_of_service","label": "Years of Service",     "type": "number","required": True},
            {"key": "reason",          "label": "Reason for Transfer",  "type": "textarea","required": True},
            {"key": "applicant_name",  "label": "Applicant Name",       "type": "text", "required": True},
        ],
    },
    "infrastructure_request": {
        "name": "Infrastructure Request",
        "description": "Request budget or infrastructure improvements for school",
        "fields": [
            {"key": "school_name",       "label": "School Name",            "type": "text",    "required": True},
            {"key": "infrastructure_item","label": "Infrastructure Item",    "type": "text",    "required": True},
            {"key": "quantity",           "label": "Quantity",              "type": "number",  "required": True},
            {"key": "estimated_cost",     "label": "Estimated Cost (₹)",    "type": "number",  "required": True},
            {"key": "justification",      "label": "Justification",         "type": "textarea","required": True},
            {"key": "district",           "label": "District",              "type": "text",    "required": True},
            {"key": "hm_name",            "label": "Headmaster Name",       "type": "text",    "required": True},
        ],
    },
    "parent_notice": {
        "name": "Parent Notice",
        "description": "Issue an official notice to a student's parents/guardians",
        "fields": [
            {"key": "school_name",    "label": "School Name",        "type": "text",    "required": True},
            {"key": "student_name",   "label": "Student Name",       "type": "text",    "required": True},
            {"key": "class_grade",    "label": "Class",              "type": "text",    "required": True},
            {"key": "notice_subject", "label": "Subject of Notice",  "type": "text",    "required": True},
            {"key": "notice_details", "label": "Notice Details",     "type": "textarea","required": True},
            {"key": "meeting_date",   "label": "Meeting Date (if any)","type": "date",  "required": False},
            {"key": "hm_name",        "label": "Headmaster Name",    "type": "text",    "required": True},
        ],
    },
    "scholarship_recommendation": {
        "name": "Scholarship Recommendation",
        "description": "Recommend a student for a scholarship programme",
        "fields": [
            {"key": "student_name",       "label": "Student Name",           "type": "text",   "required": True},
            {"key": "class_grade",         "label": "Class",                 "type": "text",   "required": True},
            {"key": "academic_percentage", "label": "Academic Percentage (%)", "type": "number","required": True},
            {"key": "family_income",       "label": "Annual Family Income (₹)","type": "number","required": True},
            {"key": "scholarship_name",    "label": "Scholarship Name",      "type": "text",   "required": True},
            {"key": "scholarship_amount",  "label": "Scholarship Amount (₹)","type": "number", "required": False},
            {"key": "school_name",         "label": "School Name",           "type": "text",   "required": True},
            {"key": "hm_name",             "label": "Headmaster Name",       "type": "text",   "required": True},
        ],
    },
    "compliance_submission": {
        "name": "Compliance Submission",
        "description": "Submit compliance reports to education authorities",
        "fields": [
            {"key": "compliance_type",     "label": "Compliance Type",       "type": "text",    "required": True},
            {"key": "submission_period",   "label": "Submission Period",     "type": "text",    "required": True},
            {"key": "status",              "label": "Compliance Status",     "type": "select",  "options": ["Complied", "Partially Complied", "Not Complied"], "required": True},
            {"key": "details",             "label": "Details / Remarks",     "type": "textarea","required": True},
            {"key": "school_name",         "label": "School Name",           "type": "text",    "required": True},
            {"key": "authority_name",      "label": "Submitting Authority",  "type": "text",    "required": True},
            {"key": "hm_name",             "label": "Headmaster Name",       "type": "text",    "required": True},
        ],
    },
    "budget_request": {
        "name": "Budget Request",
        "description": "Request budget allocation for school expenditure heads",
        "fields": [
            {"key": "school_name",           "label": "School Name",              "type": "text",    "required": True},
            {"key": "budget_head",           "label": "Budget Head",             "type": "text",    "required": True},
            {"key": "amount_requested",      "label": "Amount Requested (₹)",    "type": "number",  "required": True},
            {"key": "previous_year_amount",  "label": "Previous Year Amount (₹)","type": "number",  "required": False},
            {"key": "purpose",               "label": "Purpose",                 "type": "text",    "required": True},
            {"key": "justification",         "label": "Detailed Justification",  "type": "textarea","required": True},
            {"key": "hm_name",               "label": "Headmaster Name",         "type": "text",    "required": True},
        ],
    },
}


def _build_reference_number(letter_type: str) -> str:
    prefix_map = {
        "leave_approval":          "EDU/LA",
        "teacher_transfer":        "EDU/TT",
        "infrastructure_request":  "EDU/IR",
        "parent_notice":           "EDU/PN",
        "scholarship_recommendation": "EDU/SR",
        "compliance_submission":   "EDU/CS",
        "budget_request":          "EDU/BR",
    }
    prefix = prefix_map.get(letter_type, "EDU/GEN")
    year = date.today().year
    uid = shortuuid.ShortUUID().random(length=5).upper()
    return f"{prefix}/{year}/{uid}"


class LetterService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def list_templates(self) -> list[LetterTemplateInfo]:
        return [
            LetterTemplateInfo(
                key=k, name=v["name"],
                description=v["description"], fields=v["fields"],
            )
            for k, v in LETTER_TEMPLATES.items()
        ]

    async def generate(self, request: LetterGenerateRequest, user: User) -> LetterGenerateResponse:
        template = LETTER_TEMPLATES.get(request.letter_type)
        if not template:
            raise HTTPException(status_code=400, detail=f"Unknown letter type: {request.letter_type}")

        fields_formatted = "\n".join(
            f"  {k}: {v}" for k, v in request.template_fields.items()
        )
        prompt = LETTER_GENERATION_PROMPT.format(
            letter_type_name=template["name"],
            fields_formatted=fields_formatted,
        )

        content = await generate_text(prompt)
        ref_no = _build_reference_number(request.letter_type)

        record = GeneratedLetter(
            user_id=user.id,
            letter_type=request.letter_type,
            template_fields=request.template_fields,
            content=content,
            reference_number=ref_no,
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)

        return LetterGenerateResponse(
            id=record.id,
            letter_type=record.letter_type,
            reference_number=ref_no,
            content=content,
            created_at=str(record.created_at),
        )

    async def get_by_id(self, letter_id: int, user: User) -> LetterGenerateResponse:
        result = await self.db.execute(
            select(GeneratedLetter).where(
                GeneratedLetter.id == letter_id,
                GeneratedLetter.user_id == user.id,
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            raise HTTPException(status_code=404, detail="Letter not found")
        return LetterGenerateResponse(
            id=record.id,
            letter_type=record.letter_type,
            reference_number=record.reference_number or "",
            content=record.content,
            created_at=str(record.created_at),
        )

    async def get_history(self, user: User, limit: int = 20) -> list[LetterHistoryItem]:
        result = await self.db.execute(
            select(GeneratedLetter)
            .where(GeneratedLetter.user_id == user.id)
            .order_by(desc(GeneratedLetter.created_at))
            .limit(limit)
        )
        return [
            LetterHistoryItem(
                id=r.id,
                letter_type=r.letter_type,
                reference_number=r.reference_number,
                created_at=str(r.created_at),
            )
            for r in result.scalars().all()
        ]

    async def export_pdf(self, letter_id: int, user: User) -> bytes:
        resp = await self.get_by_id(letter_id, user)
        return generate_letter_pdf(resp.content, resp.reference_number)

    async def export_docx(self, letter_id: int, user: User) -> bytes:
        resp = await self.get_by_id(letter_id, user)
        return generate_letter_docx(resp.content, resp.reference_number)
