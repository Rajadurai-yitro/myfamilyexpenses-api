import uuid
from datetime import datetime
from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.infrastructure.database.models.base import Base
from app.infrastructure.database.models.user_model import GUID


class ExpenseGroupModel(Base):
    __tablename__ = "expense_groups"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(60), nullable=False)
    description = Column(String(500), nullable=True)
    group_type = Column(String(20), nullable=False, default="other")
    visibility = Column(String(20), nullable=False, default="private")
    image_path = Column(String(255), nullable=True)
    created_by = Column(GUID(), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    memberships = relationship(
        "GroupMembershipModel", back_populates="group", cascade="all, delete-orphan"
    )
    invitations = relationship(
        "GroupInvitationModel", back_populates="group", cascade="all, delete-orphan"
    )
    expenses = relationship(
        "GroupExpenseModel", back_populates="group", cascade="all, delete-orphan"
    )
    settlements = relationship(
        "ExpenseSettlementModel", back_populates="group", cascade="all, delete-orphan"
    )
    audit_events = relationship(
        "GroupAuditEventModel", back_populates="group", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("length(name) >= 2", name="check_group_name_len"),
        CheckConstraint(
            "group_type IN ('family','friends','trip','roommates','other')",
            name="check_group_type",
        ),
        CheckConstraint(
            "visibility IN ('private','discoverable')",
            name="check_group_visibility",
        ),
        Index("ix_expense_groups_visibility", "visibility"),
        Index("ix_expense_groups_created_by", "created_by"),
    )


class GroupMembershipModel(Base):
    __tablename__ = "group_memberships"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    group_id = Column(
        GUID(), ForeignKey("expense_groups.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False, default="member")
    status = Column(String(20), nullable=False, default="active")
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    group = relationship("ExpenseGroupModel", back_populates="memberships")
    user = relationship("UserModel")

    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_member"),
        CheckConstraint("role IN ('admin','member')", name="check_member_role"),
        CheckConstraint("status IN ('active','removed')", name="check_member_status"),
        Index("ix_group_memberships_user", "user_id", "status"),
        Index("ix_group_memberships_group_status", "group_id", "status"),
    )


class GroupInvitationModel(Base):
    __tablename__ = "group_invitations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    group_id = Column(
        GUID(), ForeignKey("expense_groups.id", ondelete="CASCADE"), nullable=False
    )
    email = Column(String(255), nullable=False)
    invited_by = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    invitee_user_id = Column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    responded_at = Column(DateTime, nullable=True)

    group = relationship("ExpenseGroupModel", back_populates="invitations")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','accepted','rejected','expired')",
            name="check_invite_status",
        ),
        Index("ix_group_invitations_email_status", "email", "status"),
        Index("ix_group_invitations_group_status", "group_id", "status"),
    )


class GroupExpenseModel(Base):
    __tablename__ = "group_expenses"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    group_id = Column(
        GUID(), ForeignKey("expense_groups.id", ondelete="CASCADE"), nullable=False
    )
    paid_by = Column(GUID(), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_by = Column(GUID(), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    category_id = Column(
        GUID(), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )
    amount = Column(Numeric(14, 2), nullable=False)
    description = Column(String(500), nullable=True)
    expense_date = Column(Date, nullable=False)
    payment_mode = Column(String(20), nullable=False, default="cash")
    online_payment_type = Column(String(30), nullable=True)
    split_method = Column(String(20), nullable=False, default="equal")
    client_request_id = Column(String(64), nullable=True)
    receipt_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    group = relationship("ExpenseGroupModel", back_populates="expenses")
    shares = relationship(
        "ExpenseShareModel", back_populates="expense", cascade="all, delete-orphan"
    )
    category = relationship("CategoryModel")
    payer = relationship("UserModel", foreign_keys=[paid_by])

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_group_expense_positive"),
        CheckConstraint(
            "split_method IN ('equal','percent','exact','shares')",
            name="check_split_method",
        ),
        UniqueConstraint(
            "group_id",
            "created_by",
            "client_request_id",
            name="uq_group_expense_idempotency",
        ),
        Index("ix_group_expenses_group_date", "group_id", "expense_date"),
        Index("ix_group_expenses_created", "group_id", "created_at"),
    )


class ExpenseShareModel(Base):
    __tablename__ = "expense_shares"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    expense_id = Column(
        GUID(), ForeignKey("group_expenses.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    percent = Column(Numeric(6, 2), nullable=True)
    shares = Column(Integer, nullable=True)

    expense = relationship("GroupExpenseModel", back_populates="shares")

    __table_args__ = (
        UniqueConstraint("expense_id", "user_id", name="uq_expense_share_member"),
        CheckConstraint("amount >= 0", name="check_share_amount"),
        Index("ix_expense_shares_user", "user_id"),
    )


class ExpenseSettlementModel(Base):
    __tablename__ = "expense_settlements"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    group_id = Column(
        GUID(), ForeignKey("expense_groups.id", ondelete="CASCADE"), nullable=False
    )
    from_user_id = Column(GUID(), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    to_user_id = Column(GUID(), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    method = Column(String(30), nullable=False)
    recording_kind = Column(String(20), nullable=False, default="manual")
    client_request_id = Column(String(64), nullable=True)
    created_by = Column(GUID(), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    note = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    group = relationship("ExpenseGroupModel", back_populates="settlements")

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_settlement_positive"),
        CheckConstraint("from_user_id <> to_user_id", name="check_settlement_parties"),
        CheckConstraint(
            "method IN ('cash','upi','bank_transfer','card','other')",
            name="check_settlement_method",
        ),
        CheckConstraint("recording_kind IN ('manual')", name="check_recording_kind"),
        UniqueConstraint(
            "group_id",
            "created_by",
            "client_request_id",
            name="uq_settlement_idempotency",
        ),
        Index("ix_settlements_group_created", "group_id", "created_at"),
    )


class GroupAuditEventModel(Base):
    __tablename__ = "group_audit_events"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    group_id = Column(
        GUID(), ForeignKey("expense_groups.id", ondelete="CASCADE"), nullable=False
    )
    actor_id = Column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(50), nullable=False)
    payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    group = relationship("ExpenseGroupModel", back_populates="audit_events")

    __table_args__ = (Index("ix_group_audit_group_created", "group_id", "created_at"),)
