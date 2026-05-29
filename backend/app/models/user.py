from datetime import datetime
from enum import Enum
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.session import Base


class UserRole(str, Enum):
    DEO = "DEO"
    MEO = "MEO"
    HM = "HM"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"
    PARENT = "PARENT"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Hierarchical linkages
    district_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("districts.id"))
    mandal_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("mandals.id"))
    school_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("schools.id"))

    # FCM token for push notifications
    fcm_token: Mapped[str | None] = mapped_column(String(512))

    # Password reset
    reset_token: Mapped[str | None] = mapped_column(String(255))
    reset_token_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    teacher_profile: Mapped["Teacher"] = relationship("Teacher", back_populates="user", uselist=False)
    student_profile: Mapped["Student"] = relationship("Student", back_populates="user", uselist=False)
