from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.core.config import settings
from app.infrastructure.database.models.base import Base
# Import all models to ensure metadata is populated
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.database.models.category_model import CategoryModel
from app.infrastructure.database.models.expense_model import ExpenseModel
from app.infrastructure.database.models.settings_model import UserSettingsModel
from app.infrastructure.database.models.token_model import RefreshTokenModel, PasswordResetTokenModel

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set database URL from settings
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
config.set_main_option("sqlalchemy.url", db_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
