from datetime import datetime
from enum import Enum
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Enum as SAEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.session import Base


class SchoolType(str, Enum):
    GOVERNMENT = "GOVERNMENT"
    AIDED = "AIDED"
    PRIVATE = "PRIVATE"
    CENTRAL = "CENTRAL"


class MediumOfInstruction(str, Enum):
    TELUGU = "TELUGU"
    ENGLISH = "ENGLISH"
    HINDI = "HINDI"
    URDU = "URDU"


class District(Base):
    __tablename__ = "districts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    state: Mapped[str] = mapped_column(String(100), default="Andhra Pradesh")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    mandals: Mapped[list["Mandal"]] = relationship("Mandal", back_populates="district")


class Mandal(Base):
    __tablename__ = "mandals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("districts.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    district: Mapped[District] = relationship("District", back_populates="mandals")
    schools: Mapped[list["School"]] = relationship("School", back_populates="mandal")


class School(Base):
    __tablename__ = "schools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dise_code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    school_type: Mapped[SchoolType] = mapped_column(SAEnum(SchoolType), default=SchoolType.GOVERNMENT)
    medium: Mapped[MediumOfInstruction] = mapped_column(SAEnum(MediumOfInstruction), default=MediumOfInstruction.TELUGU)

    address: Mapped[str | None] = mapped_column(String(500))
    village: Mapped[str | None] = mapped_column(String(255))
    mandal_id: Mapped[int] = mapped_column(Integer, ForeignKey("mandals.id"), nullable=False)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("districts.id"), nullable=False)

    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    # Enrollment
    total_students: Mapped[int] = mapped_column(Integer, default=0)
    total_teachers: Mapped[int] = mapped_column(Integer, default=0)
    classes_offered: Mapped[str | None] = mapped_column(String(50))  # "1-10"

    # Infrastructure
    has_electricity: Mapped[bool] = mapped_column(Boolean, default=False)
    has_toilets: Mapped[bool] = mapped_column(Boolean, default=False)
    has_drinking_water: Mapped[bool] = mapped_column(Boolean, default=False)
    has_library: Mapped[bool] = mapped_column(Boolean, default=False)
    has_computer_lab: Mapped[bool] = mapped_column(Boolean, default=False)
    has_playground: Mapped[bool] = mapped_column(Boolean, default=False)

    # Health scoring (computed by AI)
    health_score: Mapped[float | None] = mapped_column(Float)
    health_score_updated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    mandal: Mapped[Mandal] = relationship("Mandal", back_populates="schools")
    students: Mapped[list["Student"]] = relationship("Student", back_populates="school")
    teachers: Mapped[list["Teacher"]] = relationship("Teacher", back_populates="school")
