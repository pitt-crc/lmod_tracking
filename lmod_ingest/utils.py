"""General utilities for data parsing and ingestion."""

import logging
import os
from pathlib import Path

import pandas as pd
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert


def fetch_db_url() -> str:
    """Fetch DB connection settings from environment variables

    Returns:
        A SQLAlchemy compatible database URL

    Raises:
        RuntimeError: If the username or password is not defined in the environment
    """

    logging.info('Fetching database connection details')

    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASS')
    db_host = os.getenv('DB_HOST', default='localhost')
    db_port = os.getenv('DB_PORT', default=5432)
    db_name = os.getenv('DB_NAME')

    if not (db_user and db_password and db_name):
        raise ValueError('DB_NAME, DB_USER, and DB_PASS must be configured as environmental variables')

    return f'postgresql+asyncpg://{db_user}:{db_password}@/{db_name}?host={db_host}&port={db_port}'


def parse_log_data(path: Path) -> pd.DataFrame:
    """Parse, format, and return data from an Lmod log file

    The returned DataFrame is formatted using the same data model assumed
    by the ingestion database.

    Args:
        path: The log file path to parse

    Returns:
        A DataFrame with the parsed data
    """

    # Expect columns to be separated by whitespace and use ``=`` as a secondary
    # delimiter to automatically split up strings like "user=admin123" into two columns
    log_data = pd.read_table(
        path,
        sep=r'\s+|=',
        header=None,
        usecols=range(6, 15, 2),
        names=['user', 'module', 'path', 'host', 'time'],
        engine='python'
    )

    # Convert UTC decimals to a MySQL compatible string format
    log_data['time'] = pd.to_datetime(log_data['time'], unit='s')

    # Split the module name into package names and versions
    log_data[['package', 'version']] = log_data.module.str.split('/', n=1, expand=True)

    log_data['logname'] = str(path.resolve())
    return log_data.dropna(subset=['user'])


async def ingest_data_to_db(data: pd.DataFrame, name: str, connection) -> None:
    """Ingest data into a database

    The ``data`` argument is expected to follow the same data model as the
    target database table.

    Args:
        data: The data to ingest
        name: Name of the database table to ingest into
        connection: An open database connection
    """

    metadata = sa.MetaData()
    await connection.run_sync(metadata.reflect, only=[name])
    table = sa.Table(name, metadata, autoload_with=connection)

    chunk_size = 32000 // len(data.columns)
    for i in range(0, len(data), chunk_size):
        chunk = data.iloc[i:i + chunk_size]

        # Implicitly assume the `data` argument uses the same data model as the database table
        insert_stmt = insert(table).values(chunk.to_dict(orient="records"))
        on_duplicate_key_stmt = insert_stmt.on_conflict_do_nothing()
        await connection.execute(on_duplicate_key_stmt)
        await connection.commit()
