"""Merge alembic heads and add shared expense group tables.

Revision ID: 004_groups
Revises: 003_payment_mode, 003_profile_avatar_timezone
Create Date: 2026-10-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "004_groups"
down_revision: Union[str, Sequence[str], None] = (
    "003_payment_mode",
    "003_profile_avatar_timezone",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "expense_groups",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("group_type", sa.String(length=20), nullable=False, server_default="other"),
        sa.Column("visibility", sa.String(length=20), nullable=False, server_default="private"),
        sa.Column("image_path", sa.String(length=255), nullable=True),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_expense_groups_visibility", "expense_groups", ["visibility"])
    op.create_index("ix_expense_groups_created_by", "expense_groups", ["created_by"])

    op.create_table(
        "group_memberships",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "group_id",
            sa.String(length=36),
            sa.ForeignKey("expense_groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="member"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("group_id", "user_id", name="uq_group_member"),
    )
    op.create_index("ix_group_memberships_user", "group_memberships", ["user_id", "status"])
    op.create_index(
        "ix_group_memberships_group_status", "group_memberships", ["group_id", "status"]
    )

    op.create_table(
        "group_invitations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "group_id",
            sa.String(length=36),
            sa.ForeignKey("expense_groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "invited_by",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "invitee_user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("responded_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_group_invitations_email_status", "group_invitations", ["email", "status"]
    )
    op.create_index(
        "ix_group_invitations_group_status", "group_invitations", ["group_id", "status"]
    )

    op.create_table(
        "group_expenses",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "group_id",
            sa.String(length=36),
            sa.ForeignKey("expense_groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("paid_by", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("category_id", sa.String(length=36), sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("payment_mode", sa.String(length=20), nullable=False, server_default="cash"),
        sa.Column("online_payment_type", sa.String(length=30), nullable=True),
        sa.Column("split_method", sa.String(length=20), nullable=False, server_default="equal"),
        sa.Column("client_request_id", sa.String(length=64), nullable=True),
        sa.Column("receipt_path", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "group_id",
            "created_by",
            "client_request_id",
            name="uq_group_expense_idempotency",
        ),
    )
    op.create_index(
        "ix_group_expenses_group_date", "group_expenses", ["group_id", "expense_date"]
    )
    op.create_index("ix_group_expenses_created", "group_expenses", ["group_id", "created_at"])

    op.create_table(
        "expense_shares",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "expense_id",
            sa.String(length=36),
            sa.ForeignKey("group_expenses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("percent", sa.Numeric(6, 2), nullable=True),
        sa.Column("shares", sa.Integer(), nullable=True),
        sa.UniqueConstraint("expense_id", "user_id", name="uq_expense_share_member"),
    )
    op.create_index("ix_expense_shares_user", "expense_shares", ["user_id"])

    op.create_table(
        "expense_settlements",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "group_id",
            sa.String(length=36),
            sa.ForeignKey("expense_groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("to_user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("method", sa.String(length=30), nullable=False),
        sa.Column("recording_kind", sa.String(length=20), nullable=False, server_default="manual"),
        sa.Column("client_request_id", sa.String(length=64), nullable=True),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "group_id",
            "created_by",
            "client_request_id",
            name="uq_settlement_idempotency",
        ),
    )
    op.create_index(
        "ix_settlements_group_created", "expense_settlements", ["group_id", "created_at"]
    )

    op.create_table(
        "group_audit_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "group_id",
            sa.String(length=36),
            sa.ForeignKey("expense_groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("actor_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_group_audit_group_created", "group_audit_events", ["group_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_table("group_audit_events")
    op.drop_table("expense_settlements")
    op.drop_table("expense_shares")
    op.drop_table("group_expenses")
    op.drop_table("group_invitations")
    op.drop_table("group_memberships")
    op.drop_table("expense_groups")
