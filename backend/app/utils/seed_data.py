"""
Seed script — create demo data so you can log in immediately.
Run from the backend/ folder:

    python -m app.utils.seed_data

Creates (idempotent — safe to run again):
  • A school
  • A DEO admin       : deo@eduai.in     / admin123
  • A teacher         : teacher@eduai.in / teach123
  • An EduSakhi student profile + a STUDENT login (student@eduai.in / learn123)
"""

from core.security import hash_password
from core.roles import Role
from database.db import SessionLocal, create_tables
from database.models import (
    User, School, Student, District, Mandal, Teacher,
)


def _get_or_create_user(db, email, **fields):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user, False
    user = User(email=email, **fields)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, True


def seed():
    create_tables()
    db = SessionLocal()
    try:
        # ── District → Mandal hierarchy ───────────────────────────────────────
        district = db.query(District).filter(District.name == "Demo District").first()
        if not district:
            district = District(name="Demo District", state="Andhra Pradesh")
            db.add(district)
            db.commit()
            db.refresh(district)

        mandal = db.query(Mandal).filter(Mandal.name == "Demo Mandal").first()
        if not mandal:
            mandal = Mandal(name="Demo Mandal", district_id=district.id)
            db.add(mandal)
            db.commit()
            db.refresh(mandal)

        # ── School ────────────────────────────────────────────────────────────
        school = db.query(School).filter(School.name == "Govt High School, Demo").first()
        if not school:
            school = School(
                name="Govt High School, Demo",
                dise_code="DEMO0001", udise_code="DEMO0001",
                district="Demo District", mandal="Demo Mandal",
                district_id=district.id, mandal_id=mandal.id,
                health_score=72.0,
            )
            db.add(school)
            db.commit()
            db.refresh(school)

        # ── EduSakhi student profile ──────────────────────────────────────────
        student = db.query(Student).filter(Student.name == "Demo Student").first()
        if not student:
            student = Student(
                name="Demo Student", age=15, grade="10",
                school=school.name, school_id=school.id,
                admission_no="ADM001", risk_level="LOW",
                language_preference="both",
            )
            db.add(student)
            db.commit()
            db.refresh(student)

        # ── Teacher record ────────────────────────────────────────────────────
        if not db.query(Teacher).filter(Teacher.employee_id == "EMP001").first():
            db.add(Teacher(
                employee_id="EMP001", school_id=school.id, name="Demo Teacher",
                subject_area="Science", teacher_type="regular",
            ))
            db.commit()

        # ── Users ─────────────────────────────────────────────────────────────
        _get_or_create_user(
            db, "deo@eduai.in",
            name="District Officer", role=Role.DEO.value,
            hashed_password=hash_password("admin123"), is_active=1,
        )
        _get_or_create_user(
            db, "teacher@eduai.in",
            name="Demo Teacher", role=Role.TEACHER.value,
            hashed_password=hash_password("teach123"),
            school_id=school.id, is_active=1,
        )
        _get_or_create_user(
            db, "student@eduai.in",
            name="Demo Student", role=Role.STUDENT.value,
            hashed_password=hash_password("learn123"),
            school_id=school.id, student_id=student.id, is_active=1,
        )

        print("[OK] Seed complete.")
        print("   DEO     : deo@eduai.in     / admin123")
        print("   Teacher : teacher@eduai.in / teach123")
        print("   Student : student@eduai.in / learn123")
        print(f"   School id={school.id}, EduSakhi student id={student.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
