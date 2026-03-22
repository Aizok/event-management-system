from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
from pathlib import Path

# ------------------------------------------------------------------------
# 1. Добавляем путь к корню проекта, чтобы видеть пакет 'app'
# ------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 2. Импортируем настройки и модели
from app.core.config import settings
from app.models import Base  # метаданные всех моделей
import app.models  # чтобы модели точно загрузились

# Alembic Config object
config = context.config

# ------------------------------------------------------------------------
# 3. Настройка логирования
# ------------------------------------------------------------------------
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 4. Метаданные моделей для автогенерации
target_metadata = Base.metadata


def run_migrations_offline():
    """Миграции в offline режиме"""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Миграции в online режиме (синхронный движок)"""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = engine_from_config(
        configuration,
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