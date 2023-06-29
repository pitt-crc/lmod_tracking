"""Entry point and configuration file for running database migrations with ``alembic``."""

import logging
import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool

# Load alembic settings from the alembic.ini file
config = context.config

# Sets up loggers using settings from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def fetch_db_url() -> str:
    """Fetch DB connection settings from environment variables

    Returns:
        A sqlalchemy compatible database URL

    Raises:
        RuntimeError: If the username or password is not defined in the environment
    """

    # Load environmental variables from the .env file if it exists
    load_dotenv()

    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST', default='localhost')
    db_port = os.getenv('DB_PORT', default=3306)
    db_name = os.getenv('DB_NAME', default='lmod')

    if not (db_user and db_password):
        logging.error('Database credentials not configured in the working environment')
        exit(1)

    return f'mysql+mysqldb://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=None,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()


config.set_main_option('sqlalchemy.url', fetch_db_url())

if context.is_offline_mode():
    run_migrations_offline()

else:
    run_migrations_online()
