import re

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.ai.school_health_scorer import SchoolHealthScorer
from app.models.copilot import GeneratedSchoolHealthAnalysis
from sqlalchemy.orm import selectinload
from app.models.school import School, Mandal
from app.models.user import User
from app.schemas.copilot import (
    SchoolHealthAnalyzerRequest,
    SchoolHealthAnalyzerResponse,
    SchoolHealthAnalyzerSchoolSummary,
)
from app.utils.gemini_client import generate_json


SCHOOL_HEALTH_ANALYZER_PROMPT = """You are an expert mandal-level education analyst for Andhra Pradesh.

You are given a group of up to five schools and their school health metrics.
Generate a combined cluster-level school health analysis that includes:
- strengths across the selected schools
- concerns to address immediately
- clear recommendations for the mandal education officer
- an action plan with timelines and next steps
- a brief comparison summary showing which school is strongest and which needs most attention

INPUT SCHOOLS:
{schools_summary}

Return ONLY valid JSON with exactly these keys:
- "cluster_insights": string
- "strengths": array of strings
- "concerns": array of strings
- "recommendations": array of strings
- "action_plan": array of strings
- "top_school": string
- "most_at_risk_school": string
"""


def _normalize_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        result = []
        for item in value:
            if isinstance(item, str):
                result.append(item.strip())
            elif isinstance(item, dict):
                text = item.get('text') or item.get('action') or item.get('recommendation')
                if isinstance(text, str):
                    result.append(text.strip())
                else:
                    result.append(str(item).strip())
            else:
                result.append(str(item).strip())
        return [entry for entry in result if entry]
    if isinstance(value, str):
        return [line.strip() for line in value.split('\n') if line.strip()]
    return [str(value).strip()]


def _parse_percentage(value: str) -> float:
    if not value:
        return 0.0
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(value))
    if not match:
        return 0.0
    number = float(match.group(1))
    return number / 100.0 if '%' in str(value) else number


def _parse_ratio(value: str) -> float:
    if not value:
        return 0.0
    if ':' in value:
        parts = value.split(':')
        try:
            return float(parts[1])
        except ValueError:
            return 0.0
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(value))
    return float(match.group(1)) if match else 0.0


def _parse_fraction(value: str) -> float:
    if not value or '/' not in value:
        return 0.0
    parts = value.split('/')
    try:
        numerator = float(re.search(r"([0-9]+(?:\.[0-9]+)?)", parts[0]).group(1))
        denominator = float(re.search(r"([0-9]+(?:\.[0-9]+)?)", parts[1]).group(1))
        return numerator / denominator if denominator else 0.0
    except Exception:
        return 0.0


def _parse_high_risk_count(value: str) -> int:
    if not value:
        return 0
    match = re.search(r"([0-9]+)\s+high-risk", str(value))
    return int(match.group(1)) if match else 0


class SchoolHealthAnalyzerService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.scorer = SchoolHealthScorer(db)

    async def analyze(self, request: SchoolHealthAnalyzerRequest, user: User) -> SchoolHealthAnalyzerResponse:
        mandal_id = request.mandal_id or user.mandal_id
        if not mandal_id:
            raise HTTPException(status_code=400, detail="Mandal ID is required for school health analysis.")

        schools_result = await self.db.execute(
            select(School).options(selectinload(School.mandal)).where(School.mandal_id == mandal_id, School.is_active == True)
        )
        schools = schools_result.scalars().all()
        if not schools:
            raise HTTPException(status_code=404, detail="No active schools found for the selected mandal.")

        selected = []
        if request.school_ids:
            selected_ids = set(request.school_ids)
            selected = [school for school in schools if school.id in selected_ids]
            if len(selected) != len(selected_ids):
                raise HTTPException(status_code=400, detail="One or more selected schools are not available in this mandal.")
        else:
            selected = sorted(
                schools,
                key=lambda s: s.health_score if s.health_score is not None else 0,
                reverse=True,
            )[:5]

        if len(selected) == 0:
            raise HTTPException(status_code=400, detail="Select at least one school for analysis.")

        if len(selected) > 5:
            selected = selected[:5]

        school_metrics = []
        school_breakdown = []
        for school in selected:
            score_data = await self.scorer.compute(school.id)
            attendance_value = score_data.get('breakdown', {}).get('student_attendance_rate', {}).get('value', '0%')
            dropout_value = score_data.get('breakdown', {}).get('dropout_rate', {}).get('value', '0%')
            infra_value = score_data.get('breakdown', {}).get('infrastructure_score', {}).get('value', '0/6 amenities')
            teacher_ratio_value = score_data.get('breakdown', {}).get('teacher_student_ratio', {}).get('value', '1:30')
            high_risk_value = score_data.get('breakdown', {}).get('high_risk_student_ratio', {}).get('value', '0 high-risk / 0 total')

            attendance_rate = _parse_percentage(attendance_value)
            teacher_ratio = _parse_ratio(teacher_ratio_value)
            infrastructure_score = _parse_fraction(infra_value)
            high_risk_count = _parse_high_risk_count(high_risk_value)

            school_metrics.append(
                f"{school.name} ({school.dise_code}): health score {score_data['health_score']} grade {score_data['grade']}, attendance {attendance_rate:.0%}, teachers {score_data['total_teachers']}, students {score_data['total_students']}, PTR 1:{teacher_ratio:.1f}, infra {infra_value}"
            )
            school_breakdown.append(SchoolHealthAnalyzerSchoolSummary(
                school_id=school.id,
                school_name=school.name,
                dise_code=school.dise_code,
                health_score=score_data['health_score'],
                attendance_rate=attendance_rate,
                dropout_risk_count=high_risk_count,
                total_students=score_data['total_students'],
                total_teachers=score_data['total_teachers'],
                teacher_student_ratio=teacher_ratio,
                infrastructure_score=infrastructure_score,
                mandal_name=school.mandal.name if school.mandal else '',
            ))

        schools_summary_text = '\n'.join(f"- {line}" for line in school_metrics)
        prompt = SCHOOL_HEALTH_ANALYZER_PROMPT.format(schools_summary=schools_summary_text)

        content = await generate_json(prompt)

        # Save the analysis to DB for export
        record = GeneratedSchoolHealthAnalysis(
            user_id=user.id,
            mandal_id=mandal_id,
            mandal_name=selected[0].mandal.name if selected and selected[0].mandal else '',
            selected_school_count=len(selected),
            cluster_insights=content.get('cluster_insights', ''),
            strengths=content.get('strengths', []),
            concerns=content.get('concerns', []),
            recommendations=content.get('recommendations', []),
            action_plan=content.get('action_plan', []),
            top_school=content.get('top_school', ''),
            most_at_risk_school=content.get('most_at_risk_school', ''),
            school_breakdown=[s.model_dump() for s in school_breakdown],
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)

        return SchoolHealthAnalyzerResponse(
            id=record.id,
            mandal_id=mandal_id,
            mandal_name=selected[0].mandal.name if selected and selected[0].mandal else '',
            selected_school_count=len(selected),
            school_breakdown=school_breakdown,
            cluster_insights=content.get('cluster_insights', ''),
            strengths=_normalize_list(content.get('strengths', [])),
            concerns=_normalize_list(content.get('concerns', [])),
            recommendations=_normalize_list(content.get('recommendations', [])),
            action_plan=_normalize_list(content.get('action_plan', [])),
            top_school=content.get('top_school', ''),
            most_at_risk_school=content.get('most_at_risk_school', ''),
        )
