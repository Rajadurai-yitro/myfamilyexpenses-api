from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)


class UpdateSettingsRequest(BaseModel):
    language_code: Optional[str] = Field(None, max_length=10)
    theme_mode: Optional[str] = Field(None, max_length=20)
    theme_color: Optional[str] = Field(None, max_length=20)
    currency_code: Optional[str] = Field(None, max_length=10)
    time_zone: Optional[str] = Field(None, max_length=64)
    opening_balance: Optional[Decimal] = Field(None, ge=0)
