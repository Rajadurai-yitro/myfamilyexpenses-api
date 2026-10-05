"""Add profile photo path and time zone

Revision ID: 003_profile_avatar_timezone
Revises: 002_credit_debit_receipts
Create Date: 2026-10-03 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_profile_avatar_timezone"
down_revision: Union[str, None] = "002_credit_debit_receipts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_path", sa.String(length=255), nullable=True))
    op.add_column(
        "user_settings",
        sa.Column(
            "time_zone",
            sa.String(length=64),
            nullable=False,
            server_default="Asia/Kolkata",
        ),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "time_zone")
    op.drop_column("users", "avatar_path")
