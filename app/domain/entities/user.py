from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class User:
    id: uuid.UUID
    email: str
    password_hash: str
    display_name: Optional[str]
    is_active: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime
    avatar_path: Optional[str] = None

    @classmethod
    def create(
        cls,
        email: str,
        password_hash: str,
        display_name: Optional[str] = None,
    ) -> "User":
        now = datetime.utcnow()
        return cls(
            id=uuid.uuid4(),
            email=email.strip().lower(),
            password_hash=password_hash,
            display_name=display_name.strip() if display_name else None,
            is_active=True,
            email_verified=False,
            created_at=now,
            updated_at=now,
        )
