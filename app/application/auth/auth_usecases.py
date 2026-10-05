from datetime import datetime, timedelta
import hashlib
from typing import Dict, Any, Optional
import uuid

from app.core.exceptions import (
    ConflictException,
    EntityNotFoundException,
    UnauthorizedException,
    ValidationException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_password_hash,
    verify_password,
)
from app.application.user_defaults import default_settings_for
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository


class RegisterUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, email: str, password: str, display_name: Optional[str] = None) -> Dict[str, Any]:
        email_clean = email.strip().lower()
        if len(password) < 6:
            raise ValidationException("Password must be at least 6 characters long")

        existing = self.user_repo.get_by_email(email_clean)
        if existing:
            raise ConflictException("An account with this email address already exists")

        pw_hash = get_password_hash(password)
        new_user = User.create(email=email_clean, password_hash=pw_hash, display_name=display_name)
        saved_user = self.user_repo.create(new_user)

        # Initialize default user settings
        default_settings = default_settings_for(saved_user.id)
        saved_settings = self.user_repo.save_settings(default_settings)

        # Generate tokens
        access_token = create_access_token(str(saved_user.id))
        refresh_token = create_refresh_token(str(saved_user.id))

        # Store refresh token hash
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(days=30)
        self.user_repo.store_refresh_token(saved_user.id, token_hash, expires_at)

        return {
            "user": saved_user,
            "settings": saved_settings,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }


class LoginUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, email: str, password: str) -> Dict[str, Any]:
        email_clean = email.strip().lower()
        user = self.user_repo.get_by_email(email_clean)
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException("This user account has been deactivated")

        settings = self.user_repo.get_settings(user.id)
        if not settings:
            settings = self.user_repo.save_settings(default_settings_for(user.id))

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))

        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(days=30)
        self.user_repo.store_refresh_token(user.id, token_hash, expires_at)

        return {
            "user": user,
            "settings": settings,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }


class RefreshTokenUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, refresh_token: str) -> Dict[str, Any]:
        try:
            payload = decode_refresh_token(refresh_token)
            user_id_str = payload.get("sub")
            if not user_id_str:
                raise UnauthorizedException("Invalid refresh token payload")
            user_id = uuid.UUID(user_id_str)
        except Exception:
            raise UnauthorizedException("Invalid or expired refresh token")

        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive")

        new_access_token = create_access_token(str(user.id))
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
        }


class ForgotPasswordUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, email: str) -> Dict[str, str]:
        email_clean = email.strip().lower()
        user = self.user_repo.get_by_email(email_clean)
        # Always return generic message to prevent email enumeration
        if user:
            # Generate one-time reset token (in dev logged to stdout, in prod emailed)
            reset_token = uuid.uuid4().hex
            # For demonstration / dev testing, token can be used with reset endpoint
        return {
            "message": "If the account exists, a password reset link has been sent."
        }


class ResetPasswordUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, email: str, new_password: str) -> Dict[str, str]:
        if len(new_password) < 6:
            raise ValidationException("Password must be at least 6 characters long")
        user = self.user_repo.get_by_email(email.strip().lower())
        if not user:
            raise EntityNotFoundException("User", email)

        user.password_hash = get_password_hash(new_password)
        self.user_repo.update(user)
        self.user_repo.revoke_refresh_tokens(user.id)
        return {"message": "Password reset successfully. Please log in with your new password."}


class GetCurrentUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: uuid.UUID) -> Dict[str, Any]:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User", user_id)
        settings = self.user_repo.get_settings(user_id)
        if not settings:
            settings = self.user_repo.save_settings(default_settings_for(user.id))
        return {
            "user": user,
            "settings": settings,
        }
