from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


# ─── Circular Summarization ───────────────────────────────────────

class CircularSummaryJSON(BaseModel):
    summary: str
    key_instructions: list[str]
    action_items: list[str]
    deadlines: list[str]
    responsible_officers: list[str]
    compliance_requirements: list[str]


class CircularSummaryResponse(BaseModel):
    id: int
    file_name: str
    summary_json: CircularSummaryJSON
    created_at: str

    model_config = {"from_attributes": True}


class CircularSummaryListItem(BaseModel):
    id: int
    file_name: str
    summary_preview: str
    created_at: str


# ─── Letter Generator ─────────────────────────────────────────────

class LetterTemplateInfo(BaseModel):
    key: str
    name: str
    description: str
    fields: list[dict[str, Any]]


class LetterGenerateRequest(BaseModel):
    letter_type: str = Field(..., description="Template key, e.g. 'leave_approval'")
    template_fields: dict[str, Any] = Field(..., description="Dynamic form values")
    language: str = Field(default="English", description="Output language: English or Telugu")


class LetterGenerateResponse(BaseModel):
    id: int
    letter_type: str
    reference_number: str
    content: str
    created_at: str

    model_config = {"from_attributes": True}


class LetterHistoryItem(BaseModel):
    id: int
    letter_type: str
    reference_number: str | None
    created_at: str


# ─── Report Generator ────────────────────────────────────────────

class ReportSection(BaseModel):
    title: str
    content: str


class ReportContentJSON(BaseModel):
    executive_summary: str
    kpi_analysis: str
    trends: str
    risks: str
    recommendations: list[str]
    action_plan: list[str]


class ReportGenerateRequest(BaseModel):
    report_type: str = Field(..., description="school_performance | attendance | teacher_performance | school_health")
    report_scope: str = Field(..., description="school | mandal | district")
    scope_id: int = Field(..., description="The ID of the school/mandal/district")
    academic_year: str = Field(default="2024-25")
    language: str = Field(default="English", description="Output language: English or Telugu")


class ReportGenerateResponse(BaseModel):
    id: int
    report_type: str
    report_scope: str
    content: str
    content_json: ReportContentJSON | None
    created_at: str

    model_config = {"from_attributes": True}


class ReportHistoryItem(BaseModel):
    id: int
    report_type: str
    report_scope: str
    created_at: str


class SchoolHealthAnalyzerSchoolSummary(BaseModel):
    school_id: int
    school_name: str
    dise_code: str
    health_score: float
    attendance_rate: float
    dropout_risk_count: int
    total_students: int
    total_teachers: int
    teacher_student_ratio: float
    infrastructure_score: float
    mandal_name: str


class SchoolHealthAnalyzerRequest(BaseModel):
    mandal_id: int | None = Field(None, description="Mandal ID for the selected MEO cluster")
    school_ids: list[int] | None = Field(None, description="Optional selected school IDs, up to 5 schools")


class SchoolHealthAnalyzerResponse(BaseModel):
    id: int | None = None
    mandal_id: int
    mandal_name: str
    selected_school_count: int
    cluster_insights: str
    strengths: list[str]
    concerns: list[str]
    recommendations: list[str]
    action_plan: list[str]
    top_school: str
    most_at_risk_school: str
    school_breakdown: list[SchoolHealthAnalyzerSchoolSummary]

    model_config = {"from_attributes": True}


class MEOAssistantRequest(BaseModel):
    mandal_id: int | None = Field(None, description="Mandal ID for the current MEO user")
    context: str | None = Field(None, description="Optional description of the current issue or objectives")


class MEOAssistantResponse(BaseModel):
    mandal_id: int
    mandal_name: str | None = None
    content: str

    model_config = {"from_attributes": True}


# ─── Translation ──────────────────────────────────────────────────

class TranslateRequest(BaseModel):
    source_language: str = Field(..., description="Telugu or English")
    target_language: str = Field(..., description="Telugu or English")
    text: str = Field(..., description="Text to translate", max_length=10000)


class TranslateResponse(BaseModel):
    id: int
    source_language: str
    target_language: str
    source_text: str
    translated_text: str
    word_count: int
    created_at: str

    model_config = {"from_attributes": True}


class TranslationHistoryItem(BaseModel):
    id: int
    type: str = "text"
    source_language: str
    target_language: str
    preview: str
    word_count: int | None
    created_at: str


# ─── Document Translation ─────────────────────────────────────────

class DocumentTranslateResponse(BaseModel):
    id: int | None = None
    file_name: str
    file_type: str
    source_language: str
    target_language: str
    original_text: str
    translated_text: str
    original_length: int
    translated_length: int
    word_count: int
    document_type: str | None = None
    created_at: str | None = None


class DocumentTranslationHistoryItem(BaseModel):
    id: int
    type: str = "document"
    file_name: str
    file_type: str | None = None
    document_type: str | None = None
    source_language: str
    target_language: str
    preview: str
    word_count: int | None
    created_at: str


# ─── MEO Template Reports ──────────────────────────────────────────

class MEOTemplateInfo(BaseModel):
    key: str
    name: str
    description: str
    fields: list[dict[str, Any]]


class MEOReportGenerateRequest(BaseModel):
    report_type: str = Field(..., description="Template key, e.g. 'early_warning'")
    template_fields: dict[str, Any] = Field(..., description="Dynamic form values for the template")
    language: str = Field(default="English", description="Output language: English or Telugu")


class MEOReportGenerateResponse(BaseModel):
    id: int
    report_type: str
    mandal_id: int
    mandal_name: str | None = None
    reference_number: str
    content: str
    created_at: str

    model_config = {"from_attributes": True}


class MEOReportHistoryItem(BaseModel):
    id: int
    report_type: str
    reference_number: str | None
    mandal_name: str | None = None
    created_at: str
