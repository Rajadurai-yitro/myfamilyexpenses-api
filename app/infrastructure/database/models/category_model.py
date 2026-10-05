import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.infrastructure.database.models.base import Base
from app.infrastructure.database.models.user_model import GUID


class CategoryModel(Base):
    __tablename__ = "categories"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name_key = Column(String(100), unique=True, nullable=False, index=True)
    icon_key = Column(String(100), nullable=False)
    kind = Column(String(10), nullable=False, default="debit")
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    expenses = relationship("ExpenseModel", back_populates="category")
