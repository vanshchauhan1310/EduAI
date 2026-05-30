"""
Auth routes — register, login, current user.
Mounted under /api/v1/auth.
"""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from database.db import get_db
from database.models import User
from governance import auth_service
from governance.schemas import UserRegister, Token, UserOut

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """Create a new user account."""
    return auth_service.register_user(data, db)


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    OAuth2 password login. Swagger's Authorize button posts here.
    `username` field = the user's email.
    """
    return auth_service.login_and_issue_token(
        email=form_data.username, password=form_data.password, db=db
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return current_user
