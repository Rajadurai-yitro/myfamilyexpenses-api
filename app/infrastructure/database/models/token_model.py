import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.infrastructure.database.models.base import Base
from app.infrastructure.database.models.user_model import GUID


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("UserModel", back_populates="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_tokens_user", "user_id"),
        Index("ix_refresh_tokens_expires", "expires_at"),
    )


class PasswordResetTokenModel(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("UserModel", back_populates="password_reset_tokens")

    __table_args__ = (
        Index("ix_password_reset_user", "user_id"),
        Index("ix_password_reset_expires", "expires_at"),
    )
