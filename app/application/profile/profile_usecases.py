from decimal import Decimal
from typing import Optional
import uuid

from app.application.user_defaults import default_settings_for
from app.core.config import settings as app_settings
from app.core.exceptions import EntityNotFoundException, ValidationException
from app.domain.entities.settings import UserSettings
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.storage.avatar_storage import delete_avatar, save_avatar


class ProfileUseCases:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def update_profile(self, user_id: uuid.UUID, display_name: Optional[str]) -> dict:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User", user_id)
        user.display_name = display_name.strip() if display_name else None
        updated_user = self.user_repo.update(user)
        return {"user": updated_user}

    def update_settings(
        self,
        user_id: uuid.UUID,
        language_code: Optional[str] = None,
        theme_mode: Optional[str] = None,
        theme_color: Optional[str] = None,
        currency_code: Optional[str] = None,
        time_zone: Optional[str] = None,
        opening_balance: Optional[Decimal] = None,
    ) -> UserSettings:
        settings = self.user_repo.get_settings(user_id)
        if not settings:
            settings = default_settings_for(user_id)

        if language_code:
            code = language_code.strip().lower()
            if code not in app_settings.supported_languages:
                allowed = ", ".join(app_settings.supported_languages)
                raise ValidationException(f"language_code must be one of: {allowed}")
            settings.language_code = code
        if theme_mode:
            if theme_mode not in ("light", "dark", "system"):
                raise ValidationException("theme_mode must be one of 'light', 'dark', 'system'")
            settings.theme_mode = theme_mode
        if theme_color:
            settings.theme_color = theme_color.strip()
        if currency_code:
            code = currency_code.strip().upper()
            if code not in app_settings.supported_currencies:
                allowed = ", ".join(app_settings.supported_currencies)
                raise ValidationException(f"currency_code must be one of: {allowed}")
            settings.currency_code = code
        if time_zone:
            zone = time_zone.strip()
            if zone not in app_settings.supported_time_zones:
                allowed = ", ".join(app_settings.supported_time_zones)
                raise ValidationException(f"time_zone must be one of: {allowed}")
            settings.time_zone = zone
        if opening_balance is not None:
            settings.opening_balance = round(Decimal(str(opening_balance)), 2)

        return self.user_repo.save_settings(settings)

    def set_avatar(self, user_id: uuid.UUID, data: bytes, content_type: Optional[str]) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User", user_id)
        try:
            path = save_avatar(user_id, data, content_type)
        except ValueError as exc:
            raise ValidationException(str(exc)) from exc
        if user.avatar_path and user.avatar_path != path:
            delete_avatar(user.avatar_path)
        return self.user_repo.set_avatar_path(user_id, path)

    def clear_avatar(self, user_id: uuid.UUID) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User", user_id)
        delete_avatar(user.avatar_path)
        return self.user_repo.set_avatar_path(user_id, None)

    def delete_account(self, user_id: uuid.UUID) -> bool:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User", user_id)
        delete_avatar(user.avatar_path)
        return self.user_repo.delete(user_id)
