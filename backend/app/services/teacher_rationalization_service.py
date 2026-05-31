"""Teacher Rationalization Service - Optimize teacher allocation across district."""
from datetime import date
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.deo_copilot import TeacherRationalization, TeacherRationalizationPlan
from app.models.school import District, School
from app.models.teacher import Teacher
from app.models.student import Student
from app.models.user import User
from app.schemas.deo_copilot import TeacherRationalizationResponse, RationalizationSchoolResult
from app.utils.gemini_client import generate_text

RATIONALIZATION_PROMPT = """Generate TEACHER RATIONALIZATION RECOMMENDATIONS for District: {district_name}.
Schools with deficit: {deficit_schools}, Schools with surplus: {surplus_schools}
Total surplus: {total_surplus}, Total deficit: {total_deficit}
Key shortages: {key_shortages}
Generate: 1) Transfer Suggestions 2) Deployment Plan 3) Priority Schools 4) Subject Allocation
Return plain text."""


class TeacherRationalizationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(self, district_id: int, user: User, save_plan: bool = True) -> TeacherRationalizationResponse:
        district = await self.db.get(District, district_id)
        dn = district.name if district else f"District {district_id}"

        # Get schools with teacher data
        schools_result = await self.db.execute(
            select(School).where(School.district_id == district_id, School.is_active == True)
        )
        schools = schools_result.scalars().all()
        school_ids = [s.id for s in schools]

        # Batch query: count students per school (single query instead of N queries)
        student_counts = {}
        if school_ids:
            sc_result = await self.db.execute(
                select(Student.school_id, func.count(Student.id).label("cnt"))
                .where(Student.school_id.in_(school_ids), Student.is_active == True)
                .group_by(Student.school_id)
            )
            student_counts = {r[0]: r[1] for r in sc_result.all()}

        # Batch query: count teachers per school (single query instead of N queries)
        teacher_counts = {}
        if school_ids:
            tc_result = await self.db.execute(
                select(Teacher.school_id, func.count(Teacher.id).label("cnt"))
                .where(Teacher.school_id.in_(school_ids), Teacher.is_active == True)
                .group_by(Teacher.school_id)
            )
            teacher_counts = {r[0]: r[1] for r in tc_result.all()}

        results = []
        total_surplus = 0
        total_deficit = 0

        for school in schools:
            student_count = student_counts.get(school.id, 0)
            teacher_count = teacher_counts.get(school.id, 0)

            # PTR: ideal is 1:30
            required = max(2, student_count // 30)
            shortage = max(0, required - teacher_count)
            surplus = max(0, teacher_count - required)
            total_surplus += surplus
            total_deficit += shortage

            priority = "HIGH" if shortage > 3 else ("MEDIUM" if shortage > 0 else ("SURPLUS" if surplus > 2 else "OK"))

            results.append(RationalizationSchoolResult(
                school_id=school.id, school_name=school.name, dise_code=school.dise_code,
                enrollment=student_count, current_teachers=teacher_count, required_teachers=required,
                shortage=shortage, surplus=surplus, subject_gaps=[], priority=priority,
            ))

        deficit_schools = sum(1 for r in results if r.shortage > 0)
        surplus_schools = sum(1 for r in results if r.surplus > 0)
        key_shortages = f"{deficit_schools} schools need teachers, {surplus_schools} have surplus"

        prompt = RATIONALIZATION_PROMPT.format(district_name=dn, deficit_schools=deficit_schools, surplus_schools=surplus_schools, total_surplus=total_surplus, total_deficit=total_deficit, key_shortages=key_shortages)
        try:
            ai_content = await generate_text(prompt)
        except Exception:
            ai_content = (
                f"Teacher Rationalization Recommendations for {dn}:\n\n"
                f"Summary: {deficit_schools} schools need teachers, {surplus_schools} have surplus teachers. "
                f"Total surplus: {total_surplus}, Total deficit: {total_deficit}.\n\n"
                f"Key Findings:\n"
                f"- {deficit_schools} schools have teacher shortages\n"
                f"- {surplus_schools} schools have surplus teachers\n"
                f"- Net position: {'Surplus' if total_surplus > total_deficit else 'Deficit'} of {abs(total_surplus - total_deficit)} teachers\n\n"
                f"Recommendation: Initiate teacher transfer process to balance allocation across the district.\n\n"
                f"Note: AI-generated detailed recommendations temporarily unavailable."
            )

        sorted_schools = sorted(results, key=lambda x: (-x.shortage, x.surplus))
        plan_id = None

        # Save a TeacherRationalizationPlan so export/share works
        if save_plan:
            try:
                plan = TeacherRationalizationPlan(
                    user_id=user.id,
                    district_id=district_id,
                    total_surplus=total_surplus,
                    total_deficit=total_deficit,
                    schools_analyzed=len(results),
                    ai_recommendations=ai_content,
                    plan_data={
                        "schools": [
                            {
                                "school_id": s.school_id, "school_name": s.school_name,
                                "dise_code": s.dise_code, "enrollment": s.enrollment,
                                "current_teachers": s.current_teachers, "required_teachers": s.required_teachers,
                                "shortage": s.shortage, "surplus": s.surplus,
                                "subject_gaps": s.subject_gaps, "priority": s.priority,
                            }
                            for s in sorted_schools
                        ],
                        "deficit_schools": deficit_schools,
                        "surplus_schools": surplus_schools,
                        "district_name": dn,
                    },
                )
                self.db.add(plan)
                await self.db.flush()
                await self.db.refresh(plan)
                plan_id = plan.id

                # Also save individual school rationalization records linked to the plan
                for school in sorted_schools[:10]:
                    rec = TeacherRationalization(
                        plan_id=plan.id,
                        user_id=user.id, district_id=district_id,
                        school_id=school.school_id, school_name=school.school_name,
                        enrollment=school.enrollment, current_teachers=school.current_teachers,
                        required_teachers=school.required_teachers, shortage=school.shortage,
                        surplus=school.surplus, subject_gaps=school.subject_gaps,
                        recommendations=[], ai_content=ai_content,
                    )
                    self.db.add(rec)
                await self.db.flush()
            except Exception:
                plan_id = None

        return TeacherRationalizationResponse(
            id=plan_id,
            district_id=district_id, district_name=dn,
            total_surplus=total_surplus, total_deficit=total_deficit,
            schools_analyzed=len(results), schools=sorted_schools,
            ai_recommendations=ai_content, created_at=str(date.today()),
        )

    async def generate_plan(self, district_id: int, user: User, context: str = "") -> TeacherRationalizationResponse:
        return await self.analyze(district_id, user, save_plan=True)
