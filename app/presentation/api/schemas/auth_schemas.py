from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    display_name: Optional[str] = Field(None, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: Optional[str]
    is_active: bool
    email_verified: bool
    created_at: datetime
    has_avatar: bool = False


class UserSettingsResponse(BaseModel):
    language_code: str
    theme_mode: str
    theme_color: str
    currency_code: str
    time_zone: str = "Asia/Kolkata"
    opening_balance: float


def user_to_response(user) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        email_verified=user.email_verified,
        created_at=user.created_at,
        has_avatar=bool(user.avatar_path),
    )


def settings_to_response(settings) -> UserSettingsResponse:
    return UserSettingsResponse(
        language_code=settings.language_code,
        theme_mode=settings.theme_mode,
        theme_color=settings.theme_color,
        currency_code=settings.currency_code,
        time_zone=settings.time_zone,
        opening_balance=float(settings.opening_balance),
    )


class AuthResponse(BaseModel):
    user: UserResponse
    settings: UserSettingsResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
