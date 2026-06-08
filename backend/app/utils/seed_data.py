"""
Seed script — creates initial demo data for development.
Run: python -m app.utils.seed_data
"""
import asyncio
from sqlalchemy import select, func
from app.database.session import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.school import District, Mandal, School, SchoolType, MediumOfInstruction
from app.core.security import hash_password


DEMO_USERS = [
    {"email": "deo@district.gov.in",    "full_name": "Ravi Kumar DEO",    "role": UserRole.DEO,     "password": "Admin@123"},
    {"email": "meo@mandal.gov.in",      "full_name": "Sunitha MEO",       "role": UserRole.MEO,     "password": "Admin@123"},
    {"email": "hm@school.gov.in",       "full_name": "Lakshmi HM",        "role": UserRole.HM,      "password": "Admin@123"},
    {"email": "teacher@school.gov.in",  "full_name": "Ramesh Teacher",    "role": UserRole.TEACHER, "password": "Admin@123"},
    {"email": "student@school.gov.in",  "full_name": "Arjun Student",     "role": UserRole.STUDENT, "password": "Admin@123"},
    {"email": "parent@school.gov.in",   "full_name": "Vijay Parent",      "role": UserRole.PARENT,  "password": "Admin@123"},
]


async def get_or_create(session, model, lookup: dict, defaults: dict | None = None):
    stmt = select(model).filter_by(**lookup)
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()
    if instance:
        return instance, False

    params = {**lookup, **(defaults or {})}
    instance = model(**params)
    session.add(instance)
    await session.flush()
    return instance, True


async def seed():
    async with AsyncSessionLocal() as db:
        district, _ = await get_or_create(
            db,
            District,
            {"name": "Krishna District"},
            {"state": "Andhra Pradesh"},
        )

        mandal, _ = await get_or_create(
            db,
            Mandal,
            {"name": "Vijayawada Urban", "district_id": district.id},
        )

        school_defaults = {
            "name": "ZPHS Venkatapuram",
            "school_type": SchoolType.GOVERNMENT,
            "medium": MediumOfInstruction.TELUGU,
            "mandal_id": mandal.id,
            "district_id": district.id,
            "has_electricity": True,
            "has_toilets": True,
            "has_drinking_water": True,
            "has_library": False,
            "has_computer_lab": True,
            "has_playground": True,
            "total_students": 450,
            "total_teachers": 14,
        }
        school, _ = await get_or_create(db, School, {"dise_code": "28110101001"}, school_defaults)

        for u in DEMO_USERS:
            email_norm = (u["email"] or "").strip().lower()
            mandal_id = u.get("mandal_id")
            school_id = u.get("school_id")
            district_id = u.get("district_id", district.id)

            if u["role"] == UserRole.MEO:
                mandal_id = mandal_id or mandal.id
            if u["role"] in {UserRole.HM, UserRole.TEACHER, UserRole.STUDENT}:
                school_id = school_id or school.id
                mandal_id = mandal_id or mandal.id

            stmt = select(User).where(func.lower(User.email) == email_norm)
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()
            if existing_user:
                existing_user.full_name = u["full_name"]
                existing_user.hashed_password = hash_password(u["password"])
                existing_user.role = u["role"]
                existing_user.is_active = True
                existing_user.is_verified = True
                existing_user.district_id = district_id
                existing_user.mandal_id = mandal_id
                existing_user.school_id = school_id
            else:
                user = User(
                    email=email_norm,
                    full_name=u["full_name"],
                    hashed_password=hash_password(u["password"]),
                    role=u["role"],
                    is_active=True,
                    is_verified=True,
                    district_id=district_id,
                    mandal_id=mandal_id,
                    school_id=school_id,
                )
                db.add(user)

        await db.commit()
        print("✅ Seed data created successfully.")
        print("\nDemo login credentials:")
        for u in DEMO_USERS:
            print(f"  {u['role']:<10} → {u['email']} / {u['password']}")


if __name__ == "__main__":
    asyncio.run(seed())
