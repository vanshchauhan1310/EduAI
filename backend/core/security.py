"""
Security helpers — password hashing & JWT
=========================================
Used by the governance auth layer. Pure functions, no DB access, so they can be
imported anywhere (including EduSakhi modules) without circular imports.
"""

from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from core.config import settings


# ── Passwords ─────────────────────────────────────────────────────────────────
# We use the `bcrypt` library directly (passlib is unmaintained and breaks with
# bcrypt 5.x). bcrypt only considers the first 72 bytes, so we truncate to avoid
# the ValueError raised by bcrypt 5+ on longer inputs.
def _to_72_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:72]


def hash_password(plain_password: str) -> str:
    hashed = bcrypt.hashpw(_to_72_bytes(plain_password), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            _to_72_bytes(plain_password), hashed_password.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


# ── JWT ───────────────────────────────────────────────────────────────────────
def create_access_token(
    subject: str,
    role: str,
    expires_minutes: Optional[int] = None,
) -> str:
    """
    Create a signed JWT.

    subject : usually the user id (as a string)
    role    : the user's role (DEO, TEACHER, STUDENT, ...)
    """
    expire = datetime.utcnow() + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(subject), "role": role, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Return the token payload, or None if invalid/expired."""
    try:
        return jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        return None
