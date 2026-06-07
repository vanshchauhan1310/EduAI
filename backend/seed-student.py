import sys; sys.path.insert(0, '.')
import asyncio
from app.database.session import AsyncSessionLocal
from app.models.school import District, Mandal, School
from app.models.student import Student, Gender, RiskLevel
from datetime import date

async def seed():
    async with AsyncSessionLocal() as db:
        # District
        d = District(name="Test District")
        db.add(d); await db.flush()
        # Mandal
        m = Mandal(name="Test Mandal", district_id=d.id)
        db.add(m); await db.flush()
        # School
        s = School(name="ZPHS Test School", dise_code="TEST001", mandal_id=m.id, district_id=d.id)
        db.add(s); await db.flush()
        # Students (high risk + low risk)
        s1 = Student(admission_no="STU001", first_name="John", last_name="Doe", gender=Gender.MALE, current_class=9, school_id=s.id, academic_year="2025-26", date_of_birth=date(2011, 5, 10))
        s2 = Student(admission_no="STU002", first_name="Jane", last_name="Smith", gender=Gender.FEMALE, current_class=8, school_id=s.id, academic_year="2025-26", date_of_birth=date(2012, 8, 15))
        db.add_all([s1, s2])
        await db.commit()
        print(f"Created district={d.id}, mandal={m.id}, school={s.id}, students=[{s1.id}, {s2.id}]")

asyncio.run(seed())
