"""Add payment mode fields to expenses

Revision ID: 003_payment_mode
Revises: 002_credit_debit_receipts
Create Date: 2026-10-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_payment_mode"
down_revision: Union[str, None] = "002_credit_debit_receipts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "expenses",
        sa.Column("payment_mode", sa.String(length=20), nullable=False, server_default="cash"),
    )
    op.add_column("expenses", sa.Column("transaction_id", sa.String(length=100), nullable=True))
    op.add_column(
        "expenses",
        sa.Column("online_payment_type", sa.String(length=30), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("expenses", "online_payment_type")
    op.drop_column("expenses", "transaction_id")
    op.drop_column("expenses", "payment_mode")
