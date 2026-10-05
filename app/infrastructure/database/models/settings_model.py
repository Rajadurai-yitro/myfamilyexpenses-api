from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from app.infrastructure.database.models.base import Base
from app.infrastructure.database.models.user_model import GUID


class UserSettingsModel(Base):
    __tablename__ = "user_settings"

    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    language_code = Column(String(10), default="en", nullable=False)
    theme_mode = Column(String(20), default="system", nullable=False)
    theme_color = Column(String(20), default="indigo", nullable=False)
    currency_code = Column(String(10), default="INR", nullable=False)
    time_zone = Column(String(64), default="Asia/Kolkata", nullable=False)
    opening_balance = Column(Numeric(14, 2), default=0.00, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship("UserModel", back_populates="settings")
