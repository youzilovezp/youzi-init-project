"""Alembic 迁移环境配置。"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.db.base_class import Base

# 显式导入所有模型，确保 Base.metadata 在 autogenerate 时能看到
from app.models import User, Role, Menu  # noqa: F401  触发模型注册（autogenerate 依赖 Base.metadata）

_ = (User, Role, Menu)  # 防止 Pyright 误报"unused import"

config = context.config
# 关键：用 settings.ALEMBIC_SYNC_URL（psycopg2/PyMySQL 同步驱动），
# 避免与异步 engine 共享连接时触发 greenlet 错误。
# 同时让手动 alembic upgrade head 与 init_db.py 走同一条 URL，行为一致。
config.set_main_option("sqlalchemy.url", settings.ALEMBIC_SYNC_URL)  # type: ignore[attr-defined]

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

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
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
