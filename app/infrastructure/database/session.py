from typing import Generator
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.logging import logger
from app.infrastructure.database.models.base import Base
# Import all models to ensure they are registered with Base.metadata
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.database.models.category_model import CategoryModel
from app.infrastructure.database.models.expense_model import ExpenseModel
from app.infrastructure.database.models.settings_model import UserSettingsModel
from app.infrastructure.database.models.token_model import (
    PasswordResetTokenModel,
    RefreshTokenModel,
)

# Render and older platforms might provide postgres:// which SQLAlchemy 2.0 requires to be postgresql://
database_url = settings.DATABASE_URL
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
if "sqlite" in database_url:
    connect_args["check_same_thread"] = False

engine = create_engine(
    database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _add_column_if_missing(table: str, column: str, ddl: str) -> None:
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return
    names = {item["name"] for item in inspector.get_columns(table)}
    if column in names:
        return
    with engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))


def init_db():
    """Initialize tables and add columns introduced after the first schema."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    _add_column_if_missing("categories", "kind", "kind VARCHAR(10) NOT NULL DEFAULT 'debit'")
    _add_column_if_missing(
        "expenses", "entry_type", "entry_type VARCHAR(10) NOT NULL DEFAULT 'debit'"
    )
    _add_column_if_missing("expenses", "receipt_path", "receipt_path VARCHAR(255)")
    _add_column_if_missing(
        "expenses",
        "payment_mode",
        "payment_mode VARCHAR(20) NOT NULL DEFAULT 'cash'",
    )
    _add_column_if_missing("expenses", "transaction_id", "transaction_id VARCHAR(100)")
    _add_column_if_missing(
        "expenses",
        "online_payment_type",
        "online_payment_type VARCHAR(30)",
    )
    _add_column_if_missing("users", "avatar_path", "avatar_path VARCHAR(255)")
    _add_column_if_missing(
        "user_settings",
        "time_zone",
        "time_zone VARCHAR(64) NOT NULL DEFAULT 'Asia/Kolkata'",
    )
    logger.info("Database tables initialized successfully.")
