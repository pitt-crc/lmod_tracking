"""General utilities for data parsing and ingestion."""

import logging
import os
import time
from pathlib import Path

import pandas as pd
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import create_async_engine

# Default database connection values
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 5432


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
    db_host = os.getenv('DB_HOST', default=DEFAULT_HOST)
    db_port = os.getenv('DB_PORT', default=DEFAULT_PORT)
    db_name = os.getenv('DB_NAME')

    if not (db_user and db_password and db_name):
        raise ValueError('DB_NAME, DB_USER, and DB_PASS must be configured as environmental variables')

    # This URI format supports sock file paths in addition to traditional server host names
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
        usecols=range(6, 17, 2),
        names=['user', 'jobid', 'module', 'path', 'host', 'time'],
        engine='python'
    )

    # Mask missing job ID values and convert them to integers
    log_data['jobid'] = log_data['jobid'].mask(log_data['jobid'] == 'nil').astype(pd.Int64Dtype())

    # Convert UTC decimals to a SQL compatible string format
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

    # There is nothing to do when the data is empty
    # Avoid errors and gain efficiency by exiting early
    if data.empty:
        return

    # Create a sqlalchemy representation of the table
    metadata = sa.MetaData()
    await connection.run_sync(metadata.reflect, only=[name])
    table = sa.Table(name, metadata, autoload_with=connection)

    # Ingest data as chunks to avoid Postgres limits on the number of variables
    chunk_size = 32000 // len(data.columns)
    for i in range(0, len(data), chunk_size):
        chunk = data.iloc[i:i + chunk_size]

        # Implicitly assume the `data` argument uses the same data model as the database table
        insert_stmt = insert(table).values(chunk.to_dict(orient="records"))
        on_duplicate_key_stmt = insert_stmt.on_conflict_do_nothing()
        await connection.execute(on_duplicate_key_stmt)
        await connection.commit()


async def ingest_file(path: Path, url: str) -> None:
    """Ingest a log file into a database

    Args:
        path: The log file path
        url: The database URL
    """

    logging.info(f'Ingesting {path.resolve()}')
    db_engine = create_async_engine(url=url)
    async with db_engine.connect() as connection:
        logging.info(f'Parsing log data')
        data = parse_log_data(path)

        logging.info(f'Loading data into database')
        start = time.time()
        await ingest_data_to_db(data, 'log_data', connection=connection)
        logging.info(f'Ingested {len(data)} log entries in {time.time() - start:.2f} seconds')
