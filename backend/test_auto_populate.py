"""
Quick test for auto-populate feature.
Crete a student and verify student_ml_input gets populated.
"""
import sys; sys.path.insert(0, '.')
import asyncio
from datetime import date
from sqlalchemy import text, select
from app.database.session import AsyncSessionLocal
from app.models.school import District, Mandal, School
from app.models.student import Student, Gender
from app.models.student_ml_input import StudentMLInput

async def test():
    async with AsyncSessionLocal() as db:
        # First ensure we have a school
        result = await db.execute(text("SELECT id FROM schools LIMIT 1"))
        school_row = result.first()
        if not school_row:
            d = District(name="Auto District")
            db.add(d); await db.flush()
            m = Mandal(name="Auto Mandal", district_id=d.id)
            db.add(m); await db.flush()
            s = School(name="Auto School", dise_code="AUTO001", mandal_id=m.id, district_id=d.id)
            db.add(s); await db.flush()
            school_id = s.id
        else:
            school_id = school_row[0]

        # Create student — auto-populate should fire here
        stu = Student(
            admission_no="AUTOTEST001",
            first_name="Auto",
            last_name="Test",
            gender=Gender.MALE,
            current_class=9,
            school_id=school_id,
            academic_year="2025-26",
            date_of_birth=date(2011, 5, 10),
            is_active=True
        )
        db.add(stu)
        await db.commit()
        await db.refresh(stu)
        print(f"✅ Student created: id={stu.id}")

        # Check student_ml_input
        from app.models.student_ml_input import StudentMLInput
        from sqlalchemy import select
        result = await db.execute(
            select(StudentMLInput).where(StudentMLInput.student_id == stu.id)
        )
        ml = result.scalar_one_or_none()
        if ml:
            print(f"✅ student_ml_input auto-populated!")
            print(f"   gender={ml.gender}, class_level={ml.class_level}")
            print(f"   attendance_pct={ml.attendance_pct}, avg_marks={ml.avg_marks}")
            print(f"   health_risk={ml.health_risk}, scholarship={ml.scholarship}")
        else:
            print("❌ student_ml_input NOT found!")

asyncio.run(test())