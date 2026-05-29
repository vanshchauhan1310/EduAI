from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.repositories.student_repository import StudentRepository
from app.schemas.student import StudentCreateRequest, StudentUpdateRequest, StudentResponse, StudentFilterRequest


class StudentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = StudentRepository(db)

    async def create_student(self, request: StudentCreateRequest) -> StudentResponse:
        existing = await self.repo.get_by_admission_no(request.admission_no)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Student with admission number {request.admission_no} already exists",
            )

        student = Student(**request.model_dump())
        saved = await self.repo.create(student)
        return StudentResponse.model_validate(saved)

    async def update_student(self, student_id: int, request: StudentUpdateRequest) -> StudentResponse:
        student = await self.repo.get_by_id(student_id)
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

        update_data = request.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(student, field, value)

        updated = await self.repo.update(student)
        return StudentResponse.model_validate(updated)

    async def get_student(self, student_id: int) -> StudentResponse:
        student = await self.repo.get_by_id(student_id)
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
        return StudentResponse.model_validate(student)

    async def list_students(self, filters: StudentFilterRequest) -> dict:
        students, total = await self.repo.list_filtered(filters)
        return {
            "items": [StudentResponse.model_validate(s) for s in students],
            "total": total,
            "page": filters.page,
            "page_size": filters.page_size,
            "pages": -(-total // filters.page_size),
        }

    async def mark_dropout(self, student_id: int, reason: str, dropout_date: str) -> StudentResponse:
        from datetime import date
        student = await self.repo.get_by_id(student_id)
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

        student.is_active = False
        student.dropout_reason = reason
        student.dropout_date = date.fromisoformat(dropout_date)
        updated = await self.repo.update(student)
        return StudentResponse.model_validate(updated)

    async def get_high_risk_students(self, school_id: int) -> list[StudentResponse]:
        students = await self.repo.get_high_risk_students(school_id)
        return [StudentResponse.model_validate(s) for s in students]
