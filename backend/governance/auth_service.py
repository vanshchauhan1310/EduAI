"""
Auth service — registration & login business logic.
Operates on the shared sync `Session` from database.db.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.security import hash_password, verify_password, create_access_token
from database.models import User
from governance.schemas import UserRegister


def register_user(data: UserRegister, db: Session) -> User:
    """Create a new user, rejecting duplicate emails."""
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    user = User(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=data.role.value,
        school_id=data.school_id,
        student_id=data.student_id,
        is_active=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(email: str, password: str, db: Session) -> User:
    """Verify credentials and return the user, or raise 401."""
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is disabled.",
        )
    return user


def login_and_issue_token(email: str, password: str, db: Session) -> dict:
    """Authenticate and return a token payload dict."""
    user = authenticate(email, password, db)
    token = create_access_token(subject=user.id, role=user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
        "name": user.name,
    }
