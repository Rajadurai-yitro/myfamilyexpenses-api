from datetime import datetime
import uuid
from pydantic import BaseModel


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name_key: str
    icon_key: str
    kind: str
    sort_order: int
    is_active: bool
    created_at: datetime
