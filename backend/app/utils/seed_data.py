"""
Seed script — creates initial demo data for development.
Run: python -m app.utils.seed_data
"""
import asyncio
from app.database.session import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.school import District, Mandal, School
from app.core.security import hash_password


DEMO_USERS = [
    {"email": "deo@district.gov.in",    "full_name": "Ravi Kumar DEO",    "role": UserRole.DEO,     "password": "Admin@123", "district_id": 1},
    {"email": "meo@mandal.gov.in",      "full_name": "Sunitha MEO",       "role": UserRole.MEO,     "password": "Admin@123", "mandal_id": 1},
    {"email": "hm@school.gov.in",       "full_name": "Lakshmi HM",        "role": UserRole.HM,      "password": "Admin@123", "school_id": 1},
    {"email": "teacher@school.gov.in",  "full_name": "Ramesh Teacher",    "role": UserRole.TEACHER, "password": "Admin@123", "school_id": 1},
    {"email": "student@school.gov.in",  "full_name": "Arjun Student",     "role": UserRole.STUDENT, "password": "Admin@123", "school_id": 1},
    {"email": "parent@school.gov.in",   "full_name": "Vijay Parent",      "role": UserRole.PARENT,  "password": "Admin@123"},
]


async def seed():
    async with AsyncSessionLocal() as db:
        # Seed district
        district = District(name="Krishna District", state="Andhra Pradesh")
        db.add(district)
        await db.flush()

        # Seed mandal
        mandal = Mandal(name="Vijayawada Urban", district_id=district.id)
        db.add(mandal)
        await db.flush()

        # Seed school
        school = School(
            dise_code="28110101001",
            name="ZPHS Venkatapuram",
            mandal_id=mandal.id,
            district_id=district.id,
            has_electricity=True,
            has_toilets=True,
            has_drinking_water=True,
            has_library=False,
            has_computer_lab=True,
            has_playground=True,
            total_students=450,
            total_teachers=14,
        )
        db.add(school)
        await db.flush()

        # Seed users
        for u in DEMO_USERS:
            user = User(
                email=u["email"],
                full_name=u["full_name"],
                hashed_password=hash_password(u["password"]),
                role=u["role"],
                is_active=True,
                is_verified=True,
                district_id=u.get("district_id", district.id),
                mandal_id=u.get("mandal_id"),
                school_id=u.get("school_id"),
            )
            db.add(user)

        await db.commit()
        print("✅ Seed data created successfully.")
        print("\nDemo login credentials:")
        for u in DEMO_USERS:
            print(f"  {u['role']:<10} → {u['email']} / {u['password']}")


if __name__ == "__main__":
    asyncio.run(seed())
