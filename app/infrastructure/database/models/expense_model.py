import uuid
from datetime import datetime
from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from app.infrastructure.database.models.base import Base
from app.infrastructure.database.models.user_model import GUID


class ExpenseModel(Base):
    __tablename__ = "expenses"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(GUID(), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    description = Column(String(500), nullable=True)
    entry_type = Column(String(10), nullable=False, default="debit")
    receipt_path = Column(String(255), nullable=True)
    payment_mode = Column(String(20), nullable=False, default="cash")
    transaction_id = Column(String(100), nullable=True)
    online_payment_type = Column(String(30), nullable=True)
    expense_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("UserModel", back_populates="expenses")
    category = relationship("CategoryModel", back_populates="expenses")

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_positive_amount"),
        Index("ix_expenses_user_date", "user_id", "expense_date"),
        Index("ix_expenses_user_category", "user_id", "category_id"),
        Index("ix_expenses_user_created", "user_id", "created_at"),
    )
