"""
MEO Assistant Service.
Provides AI-generated mandal-level guidance and briefings for MEO users.
"""

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.school import Mandal
from app.models.user import User
from app.schemas.copilot import MEOAssistantRequest, MEOAssistantResponse
from app.utils.gemini_client import generate_text


EARLY_WARNING_PROMPT = """You are an expert Mandal Education Officer working for the Government of Andhra Pradesh.
Mandal: {mandal_name} ({mandal_id})

Task: Generate an early warning briefing covering potential school health, attendance, dropout risk, teacher absence, and critical incidents.
Include:
- the most urgent risk signals for the mandal
- quick actions that must be taken in the next 7 days
- escalation guidance for the DEO and district offices
- recommended monitoring checkpoints

Context:
{context}

Output:
Provide a clear, structured early warning briefing in English. Do not include JSON or markdown fences. Return plain text only."""

TEACHER_VACANCY_PROMPT = """You are a teacher deployment advisor for Andhra Pradesh education administration.
Mandal: {mandal_name} ({mandal_id})

Task: Create a pragmatic teacher vacancy and deployment plan for this mandal.
Include:
- current vacancy priorities by school type
- recommended postings and redistribution strategy
- actions for faster recruitment or redeployment
- stakeholder communication points for principals and HR teams

Context:
{context}

Output:
Provide the guidance in English as a clear advisory note. Return plain text only."""

GOVERNANCE_COMMUNICATION_PROMPT = """You are an expert government communication officer for Andhra Pradesh education governance.
Mandal: {mandal_name} ({mandal_id})

Task: Draft a formal communication message that the MEO can use to share governance updates with schools, district officers, and field staff.
Include:
- objective of the communication
- key points and required actions
- stakeholders and timelines
- tone suitable for official government correspondence

Context:
{context}

Output:
Return the draft message in English as plain text only."""

CLUSTER_BRIEFING_PROMPT = """You are a senior governance analyst preparing a cluster briefing for Andhra Pradesh education officials.
Mandal: {mandal_name} ({mandal_id})

Task: Produce a concise cluster governance briefing summarizing school health, attendance, teacher deployment, and priority actions.
Include:
- current status highlights
- major risks and vulnerabilities
- recommended governance focus areas
- suggested next steps for the MEO and DEO

Context:
{context}

Output:
Return the briefing in English as a single narrative with clear sections. Do not use JSON or markdown fences."""


class MEOAssistantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _resolve_mandal(self, mandal_id: int | None, user: User) -> tuple[int, str]:
        resolved_id = mandal_id or user.mandal_id
        if not resolved_id:
            raise HTTPException(status_code=400, detail="Mandal assignment is required for MEO assistant features.")

        mandal = await self.db.get(Mandal, resolved_id)
        mandal_name = mandal.name if mandal else f"Mandal {resolved_id}"
        return resolved_id, mandal_name

    async def _build_prompt(self, template: str, mandal_id: int, mandal_name: str, context: str | None) -> str:
        normalized_context = context.strip() if context else "No additional context provided."
        return template.format(mandal_name=mandal_name, mandal_id=mandal_id, context=normalized_context)

    async def generate_early_warning(self, request: MEOAssistantRequest, user: User) -> MEOAssistantResponse:
        mandal_id, mandal_name = await self._resolve_mandal(request.mandal_id, user)
        prompt = await self._build_prompt(EARLY_WARNING_PROMPT, mandal_id, mandal_name, request.context)
        content = await generate_text(prompt)
        return MEOAssistantResponse(mandal_id=mandal_id, mandal_name=mandal_name, content=content)

    async def generate_teacher_vacancy_assistant(self, request: MEOAssistantRequest, user: User) -> MEOAssistantResponse:
        mandal_id, mandal_name = await self._resolve_mandal(request.mandal_id, user)
        prompt = await self._build_prompt(TEACHER_VACANCY_PROMPT, mandal_id, mandal_name, request.context)
        content = await generate_text(prompt)
        return MEOAssistantResponse(mandal_id=mandal_id, mandal_name=mandal_name, content=content)

    async def generate_governance_communication(self, request: MEOAssistantRequest, user: User) -> MEOAssistantResponse:
        mandal_id, mandal_name = await self._resolve_mandal(request.mandal_id, user)
        prompt = await self._build_prompt(GOVERNANCE_COMMUNICATION_PROMPT, mandal_id, mandal_name, request.context)
        content = await generate_text(prompt)
        return MEOAssistantResponse(mandal_id=mandal_id, mandal_name=mandal_name, content=content)

    async def generate_cluster_briefing(self, request: MEOAssistantRequest, user: User) -> MEOAssistantResponse:
        mandal_id, mandal_name = await self._resolve_mandal(request.mandal_id, user)
        prompt = await self._build_prompt(CLUSTER_BRIEFING_PROMPT, mandal_id, mandal_name, request.context)
        content = await generate_text(prompt)
        return MEOAssistantResponse(mandal_id=mandal_id, mandal_name=mandal_name, content=content)
