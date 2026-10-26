from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
import uuid
from pydantic import BaseModel, Field, field_serializer, field_validator


class ExpenseCreateRequest(BaseModel):
    category_id: uuid.UUID
    amount: Decimal = Field(..., gt=0, description="Amount must be strictly greater than 0")
    expense_date: date
    description: Optional[str] = Field(None, max_length=500)
    entry_type: str = "debit"
    payment_mode: str = "cash"
    transaction_id: Optional[str] = Field(None, max_length=100)
    online_payment_type: Optional[str] = None
    tag: Optional[str] = Field(None, max_length=30)

    @field_validator("transaction_id", "online_payment_type", "tag", mode="before")
    @classmethod
    def _blank_optional(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value


class ExpenseUpdateRequest(BaseModel):
    category_id: Optional[uuid.UUID] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    expense_date: Optional[date] = None
    description: Optional[str] = Field(None, max_length=500)
    payment_mode: Optional[str] = None
    transaction_id: Optional[str] = Field(None, max_length=100)
    online_payment_type: Optional[str] = None
    tag: Optional[str] = Field(None, max_length=30)

    @field_validator("transaction_id", "online_payment_type", "tag", mode="before")
    @classmethod
    def _blank_optional(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value


class ExpenseResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category_id: uuid.UUID
    amount: float
    description: Optional[str]
    expense_date: date
    entry_type: str = "debit"
    payment_mode: str = "cash"
    transaction_id: Optional[str] = None
    online_payment_type: Optional[str] = None
    tag: Optional[str] = None
    receipt_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at", when_used="json")
    def _serialize_utc(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.isoformat().replace("+00:00", "Z")
