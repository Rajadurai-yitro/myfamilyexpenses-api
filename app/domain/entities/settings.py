from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid


@dataclass
class UserSettings:
    user_id: uuid.UUID
    language_code: str
    theme_mode: str
    theme_color: str
    currency_code: str
    time_zone: str
    opening_balance: Decimal
    created_at: datetime
    updated_at: datetime

    @classmethod
    def default_for_user(
        cls,
        user_id: uuid.UUID,
        *,
        language_code: str = "en",
        theme_mode: str = "system",
        theme_color: str = "indigo",
        currency_code: str = "INR",
        time_zone: str = "Asia/Kolkata",
        opening_balance: Optional[Decimal] = None,
    ) -> "UserSettings":
        now = datetime.utcnow()
        return cls(
            user_id=user_id,
            language_code=language_code,
            theme_mode=theme_mode,
            theme_color=theme_color,
            currency_code=currency_code,
            time_zone=time_zone,
            opening_balance=opening_balance if opening_balance is not None else Decimal("0.00"),
            created_at=now,
            updated_at=now,
        )
