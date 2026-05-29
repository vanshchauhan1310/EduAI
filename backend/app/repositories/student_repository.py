from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models.student import Student, RiskLevel
from app.schemas.student import StudentFilterRequest


class StudentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, student_id: int) -> Student | None:
        result = await self.db.execute(select(Student).where(Student.id == student_id))
        return result.scalar_one_or_none()

    async def get_by_admission_no(self, admission_no: str) -> Student | None:
        result = await self.db.execute(select(Student).where(Student.admission_no == admission_no))
        return result.scalar_one_or_none()

    async def list_filtered(self, filters: StudentFilterRequest) -> tuple[list[Student], int]:
        query = select(Student)
        count_query = select(func.count(Student.id))

        conditions = [Student.is_active == filters.is_active]
        if filters.school_id:
            conditions.append(Student.school_id == filters.school_id)
        if filters.class_grade:
            conditions.append(Student.current_class == filters.class_grade)
        if filters.section:
            conditions.append(Student.section == filters.section)
        if filters.risk_level:
            conditions.append(Student.risk_level == filters.risk_level)
        if filters.gender:
            conditions.append(Student.gender == filters.gender)
        if filters.academic_year:
            conditions.append(Student.academic_year == filters.academic_year)

        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))

        total = (await self.db.execute(count_query)).scalar_one()

        offset = (filters.page - 1) * filters.page_size
        query = query.offset(offset).limit(filters.page_size).order_by(Student.first_name)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_high_risk_students(self, school_id: int) -> list[Student]:
        result = await self.db.execute(
            select(Student).where(
                and_(
                    Student.school_id == school_id,
                    Student.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]),
                    Student.is_active == True,
                )
            )
        )
        return list(result.scalars().all())

    async def create(self, student: Student) -> Student:
        self.db.add(student)
        await self.db.flush()
        await self.db.refresh(student)
        return student

    async def update(self, student: Student) -> Student:
        await self.db.flush()
        await self.db.refresh(student)
        return student

    async def count_by_school(self, school_id: int) -> int:
        result = await self.db.execute(
            select(func.count(Student.id)).where(
                and_(Student.school_id == school_id, Student.is_active == True)
            )
        )
        return result.scalar_one()
