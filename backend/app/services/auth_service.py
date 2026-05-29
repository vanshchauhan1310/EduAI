from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import shortuuid

from app.core.config import settings
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest, TokenResponse, UserTokenPayload,
    ForgotPasswordRequest, ResetPasswordRequest, RefreshTokenRequest,
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def login(self, request: LoginRequest) -> TokenResponse:
        user = await self.user_repo.get_by_email(request.email)
        if not user or not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

        extra_claims = {
            "role": user.role.value,
            "school_id": user.school_id,
            "district_id": user.district_id,
            "mandal_id": user.mandal_id,
        }
        access_token = create_access_token(user.id, extra_claims)
        refresh_token = create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserTokenPayload(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role.value,
                school_id=user.school_id,
                district_id=user.district_id,
                mandal_id=user.mandal_id,
            ),
        )

    async def refresh(self, request: RefreshTokenRequest) -> TokenResponse:
        payload = decode_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        user = await self.user_repo.get_by_id(int(payload["sub"]))
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        extra_claims = {"role": user.role.value, "school_id": user.school_id}
        access_token = create_access_token(user.id, extra_claims)
        refresh_token = create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserTokenPayload(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role.value,
                school_id=user.school_id,
                district_id=user.district_id,
                mandal_id=user.mandal_id,
            ),
        )

    async def forgot_password(self, request: ForgotPasswordRequest) -> dict:
        user = await self.user_repo.get_by_email(request.email)
        if not user:
            # Return same response to avoid email enumeration
            return {"message": "If an account exists, a reset link has been sent."}

        token = shortuuid.uuid()
        user.reset_token = token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=2)
        await self.user_repo.update(user)

        # In production: send email with reset link
        # await email_service.send_password_reset(user.email, token)

        return {"message": "If an account exists, a reset link has been sent."}

    async def reset_password(self, request: ResetPasswordRequest) -> dict:
        user = await self.user_repo.get_by_reset_token(request.token)
        if not user or not user.reset_token_expires:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

        if user.reset_token_expires < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token has expired")

        user.hashed_password = hash_password(request.new_password)
        user.reset_token = None
        user.reset_token_expires = None
        await self.user_repo.update(user)

        return {"message": "Password reset successfully"}
