import os
from decimal import Decimal
from pathlib import Path
from typing import List, Union

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[2]

_ENV_FILES = {
    "dev": ".env.dev",
    "development": ".env.dev",
    "staging": ".env.staging",
    "stage": ".env.staging",
    "prod": ".env.prod",
    "production": ".env.prod",
}

_LOCKED_ENVS = {"staging", "stage", "prod", "production"}
_PLACEHOLDER_MARKERS = ("replace-with", "change_in_production", "change-in-production")


def _env_files() -> tuple[str, ...]:
    """Pick the shared env file from APP_ENV, then an optional local .env override."""
    app_env = os.getenv("APP_ENV", "dev").strip().lower()
    names: list[str] = []
    named = _ENV_FILES.get(app_env)
    if named:
        names.append(named)
    # Gitignored. Use this for real staging/prod secrets on a machine.
    names.append(".env")
    return tuple(str(_BACKEND_ROOT / name) for name in names)


class Settings(BaseSettings):
    APP_NAME: str = "Expense Tracker API"
    APP_ENV: str = "dev"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = "sqlite:///./expenses.db"

    # Security
    JWT_SECRET: str = "default_development_secret_key_please_change_in_production"
    JWT_REFRESH_SECRET: str = "default_development_refresh_secret_key_please_change"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day for convenience in dev
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = ["*"]

    # Defaults applied to a new user's settings row.
    DEFAULT_CURRENCY: str = "INR"
    SUPPORTED_CURRENCIES: str = "INR,USD,EUR,GBP"
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: str = "en,ta"
    DEFAULT_THEME_MODE: str = "light"
    DEFAULT_THEME_COLOR: str = "purple"
    DEFAULT_OPENING_BALANCE: Decimal = Decimal("0.00")
    DEFAULT_TIME_ZONE: str = "Asia/Kolkata"
    SUPPORTED_TIME_ZONES: str = (
        "UTC,Asia/Kolkata,Asia/Dubai,Asia/Singapore,Asia/Tokyo,"
        "Europe/London,Europe/Paris,America/New_York,America/Los_Angeles"
    )

    # Optional Email Settings
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "noreply@expensetracker.local"

    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @field_validator("DEFAULT_CURRENCY", mode="before")
    @classmethod
    def normalize_currency(cls, v: str) -> str:
        return str(v).strip().upper()

    @field_validator("DEFAULT_LANGUAGE", "DEFAULT_THEME_MODE", mode="before")
    @classmethod
    def normalize_lower(cls, v: str) -> str:
        return str(v).strip().lower()

    @field_validator("DEFAULT_THEME_COLOR", mode="before")
    @classmethod
    def normalize_theme_color(cls, v: str) -> str:
        return str(v).strip().lower()

    @property
    def supported_currencies(self) -> List[str]:
        return [c.strip().upper() for c in self.SUPPORTED_CURRENCIES.split(",") if c.strip()]

    @property
    def supported_languages(self) -> List[str]:
        return [c.strip().lower() for c in self.SUPPORTED_LANGUAGES.split(",") if c.strip()]

    @property
    def supported_time_zones(self) -> List[str]:
        return [zone.strip() for zone in self.SUPPORTED_TIME_ZONES.split(",") if zone.strip()]

    @model_validator(mode="after")
    def check_environment(self) -> "Settings":
        if self.DEFAULT_THEME_MODE not in {"light", "dark", "system"}:
            raise ValueError("DEFAULT_THEME_MODE must be light, dark, or system")
        if self.DEFAULT_CURRENCY not in self.supported_currencies:
            raise ValueError(
                f"DEFAULT_CURRENCY {self.DEFAULT_CURRENCY} is not in SUPPORTED_CURRENCIES"
            )
        if self.DEFAULT_LANGUAGE not in self.supported_languages:
            raise ValueError(
                f"DEFAULT_LANGUAGE {self.DEFAULT_LANGUAGE} is not in SUPPORTED_LANGUAGES"
            )

        if self.APP_ENV.strip().lower() not in _LOCKED_ENVS:
            return self

        secrets = f"{self.JWT_SECRET} {self.JWT_REFRESH_SECRET}".lower()
        if any(marker in secrets for marker in _PLACEHOLDER_MARKERS) or len(self.JWT_SECRET) < 32:
            raise ValueError(
                "Set real JWT_SECRET and JWT_REFRESH_SECRET in the host environment "
                "or in backend/.env before running staging or prod."
            )
        if self.DATABASE_URL.startswith("sqlite") or "USER:PASSWORD" in self.DATABASE_URL:
            raise ValueError(
                "Set a real DATABASE_URL in the host environment or in backend/.env "
                "before running staging or prod."
            )
        return self


settings = Settings()
