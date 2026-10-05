from dataclasses import dataclass
from datetime import datetime
import uuid


@dataclass
class Category:
    id: uuid.UUID
    name_key: str
    icon_key: str
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    kind: str = "debit"

    @classmethod
    def create(
        cls,
        name_key: str,
        icon_key: str,
        sort_order: int = 0,
        is_active: bool = True,
        kind: str = "debit",
    ) -> "Category":
        now = datetime.utcnow()
        return cls(
            id=uuid.uuid4(),
            name_key=name_key.strip().lower(),
            icon_key=icon_key.strip(),
            sort_order=sort_order,
            is_active=is_active,
            kind=kind.strip().lower(),
            created_at=now,
            updated_at=now,
        )
