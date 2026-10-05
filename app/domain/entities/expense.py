from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid


@dataclass
class Expense:
    id: uuid.UUID
    user_id: uuid.UUID
    category_id: uuid.UUID
    amount: Decimal
    description: Optional[str]
    expense_date: date
    created_at: datetime
    updated_at: datetime
    entry_type: str = "debit"
    receipt_path: Optional[str] = None
    payment_mode: str = "cash"
    transaction_id: Optional[str] = None
    online_payment_type: Optional[str] = None

    def __post_init__(self):
        if self.amount <= Decimal("0.00"):
            raise ValueError("Expense amount must be strictly greater than 0")

    @classmethod
    def create(
        cls,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        amount: Decimal,
        expense_date: date,
        description: Optional[str] = None,
        entry_type: str = "debit",
        payment_mode: str = "cash",
        transaction_id: Optional[str] = None,
        online_payment_type: Optional[str] = None,
    ) -> "Expense":
        now = datetime.utcnow()
        return cls(
            id=uuid.uuid4(),
            user_id=user_id,
            category_id=category_id,
            amount=round(Decimal(str(amount)), 2),
            description=description.strip() if description else None,
            expense_date=expense_date,
            entry_type=entry_type,
            payment_mode=payment_mode,
            transaction_id=transaction_id,
            online_payment_type=online_payment_type,
            created_at=now,
            updated_at=now,
        )
