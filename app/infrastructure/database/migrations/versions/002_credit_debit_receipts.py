"""Add credit/debit kind and bill image path

Revision ID: 002_credit_debit_receipts
Revises: 001_initial_schema
Create Date: 2026-10-03 00:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_credit_debit_receipts"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "categories",
        sa.Column("kind", sa.String(length=10), nullable=False, server_default="debit"),
    )
    op.add_column(
        "expenses",
        sa.Column("entry_type", sa.String(length=10), nullable=False, server_default="debit"),
    )
    op.add_column("expenses", sa.Column("receipt_path", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("expenses", "receipt_path")
    op.drop_column("expenses", "entry_type")
    op.drop_column("categories", "kind")
