"""
FastAPI auth dependencies
=========================
Reusable dependencies that resolve the current user from a JWT bearer token and
enforce role-based access. Built on the shared sync `get_db` session so they
integrate directly with every EduSakhi and governance route.
"""

from typing import Iterable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core.roles import Role
from core.security import decode_access_token
from database.db import get_db
from database.models import User

# tokenUrl must match the login route path.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve and return the authenticated user, or raise 401."""
    payload = decode_access_token(token)
    if not payload:
        raise _CREDENTIALS_EXC

    user_id = payload.get("sub")
    if user_id is None:
        raise _CREDENTIALS_EXC

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise _CREDENTIALS_EXC
    return user


def require_roles(*allowed: Role):
    """
    Dependency factory: allow only the given roles.

        @router.get("/district", dependencies=[Depends(require_roles(Role.DEO))])
    """
    allowed_values = {r.value for r in allowed}

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not permitted to access this resource.",
            )
        return current_user

    return _checker
