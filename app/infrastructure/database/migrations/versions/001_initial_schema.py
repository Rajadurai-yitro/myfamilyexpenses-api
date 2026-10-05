"""Initial schema for users, categories, expenses, settings, and tokens

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-02 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('email_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name_key', sa.String(100), nullable=False),
        sa.Column('icon_key', sa.String(100), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_categories_name_key', 'categories', ['name_key'], unique=True)

    # User settings table
    op.create_table(
        'user_settings',
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('language_code', sa.String(10), nullable=False, default='en'),
        sa.Column('theme_mode', sa.String(20), nullable=False, default='system'),
        sa.Column('theme_color', sa.String(20), nullable=False, default='indigo'),
        sa.Column('currency_code', sa.String(10), nullable=False, default='INR'),
        sa.Column('opening_balance', sa.Numeric(14, 2), nullable=False, default=0.00),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Expenses table
    op.create_table(
        'expenses',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category_id', sa.String(36), sa.ForeignKey('categories.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('expense_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('amount > 0', name='check_positive_amount'),
    )
    op.create_index('ix_expenses_user_date', 'expenses', ['user_id', 'expense_date'])
    op.create_index('ix_expenses_user_category', 'expenses', ['user_id', 'category_id'])
    op.create_index('ix_expenses_user_created', 'expenses', ['user_id', 'created_at'])

    # Refresh tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_refresh_tokens_user', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_tokens_expires', 'refresh_tokens', ['expires_at'])

    # Password reset tokens table
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_password_reset_user', 'password_reset_tokens', ['user_id'])
    op.create_index('ix_password_reset_expires', 'password_reset_tokens', ['expires_at'])


def downgrade() -> None:
    op.drop_table('password_reset_tokens')
    op.drop_table('refresh_tokens')
    op.drop_table('expenses')
    op.drop_table('user_settings')
    op.drop_table('categories')
    op.drop_table('users')
