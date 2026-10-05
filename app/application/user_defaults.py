import uuid

from app.core.config import settings
from app.domain.entities.settings import UserSettings


def default_settings_for(user_id: uuid.UUID) -> UserSettings:
    """New-user settings taken from the active environment file."""
    return UserSettings.default_for_user(
        user_id,
        language_code=settings.DEFAULT_LANGUAGE,
        theme_mode=settings.DEFAULT_THEME_MODE,
        theme_color=settings.DEFAULT_THEME_COLOR,
        currency_code=settings.DEFAULT_CURRENCY,
        time_zone=settings.DEFAULT_TIME_ZONE,
        opening_balance=settings.DEFAULT_OPENING_BALANCE,
    )
