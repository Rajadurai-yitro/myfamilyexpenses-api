from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid
from pydantic import BaseModel, Field


class ExpenseCreateRequest(BaseModel):
    category_id: uuid.UUID
    amount: Decimal = Field(..., gt=0, description="Amount must be strictly greater than 0")
    expense_date: date
    description: Optional[str] = Field(None, max_length=500)
    entry_type: str = "debit"
    payment_mode: str = "cash"
    transaction_id: Optional[str] = Field(None, max_length=100)
    online_payment_type: Optional[str] = None


class ExpenseUpdateRequest(BaseModel):
    category_id: Optional[uuid.UUID] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    expense_date: Optional[date] = None
    description: Optional[str] = Field(None, max_length=500)
    payment_mode: Optional[str] = None
    transaction_id: Optional[str] = Field(None, max_length=100)
    online_payment_type: Optional[str] = None


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
    receipt_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
