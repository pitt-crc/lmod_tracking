#!/usr/bin/env python3
"""Data ingestion utility for loading Lmod tracking data from log files into a MySQL database."""

import logging
import os
import sys
from pathlib import Path

import pandas as pd
import sqlalchemy as sa
from dotenv import load_dotenv
from sqlalchemy.dialects.mysql import insert

# Load environmental variables from the .env file if it exists
load_dotenv()


def fetch_db_url() -> str:
    """Fetch DB connection settings from environment variables

    Returns:
        A sqlalchemy compatible database URL

    Raises:
        RuntimeError: If the username or password is not defined in the environment
    """

    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST', default='localhost')
    db_port = os.getenv('DB_PORT', default=3306)
    db_name = os.getenv('DB_NAME', default='lmod')

    if not (db_user and db_password):
        logging.error('Database credentials not configured in the working environment')
        exit(1)

    return f'mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'


def parse_log_data(path: Path | str) -> pd.DataFrame:
    """Parse, format, and return data from an Lmod log file

    Args:
        path: The log file path to parse

    Returns:
        A DataFrame with the parsed data
    """

    # Expect columns to be seperated by whitespace and use ``=`` as a secondary
    # delimiter to automatically split up strings like "user=admin123" into two columns
    log_data = pd.read_table(
        path,
        sep=r'\s+|=',
        header=None,
        usecols=range(6, 15, 2),
        names=['user', 'module', 'path', 'host', 'time'],
        engine='python'
    )

    # Convert UTC decimals to a MYSql compatible string format
    log_data['time'] = pd.to_datetime(log_data['time'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S.%f')

    # Split the module name into package names and versions
    log_data[['package', 'version']] = log_data.module.str.split('/', n=1, expand=True)
    log_data['logname'] = path.name
    return log_data.dropna(subset=['user'])


def insert_on_duplicate(table, conn, keys, data_iter):
    """Helper function for pandas SQL uploads

    Enables upsert functionality for SQL inserts.
    """

    insert_stmt = insert(table.table).values(list(data_iter))
    on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(insert_stmt.inserted)
    conn.execute(on_duplicate_key_stmt)


def ingest_data_to_db(data: pd.DataFrame, name: str, connection: sa.Connection, chunksize=250) -> None:
    """Ingest data into a database

    Args:
        data: A DataFrame returned by ``parse_log_data``
        name: Name of the database to ingest to
        connection: An open database connection
        chunksize: The number of rows in each batch to be written at a time.
    """

    # Upload data into a temporary scratch table
    logging.info('loading data into scratch table ...')
    data.to_sql(
        name=name, con=connection, chunksize=chunksize,
        if_exists='append', index_label='id', method=insert_on_duplicate)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Fetch the log file path from the console
    if not sys.argv[1:]:
        print('You must specify one or more log files to ingest')
        exit(1)

    engine = sa.engine.create_engine(fetch_db_url())
    for fpath in sys.argv[1:]:
        fpath = Path(fpath)

        logging.info(f'Ingesting {fpath}')
        with engine.connect() as connection:
            data = parse_log_data(fpath)
            ingest_data_to_db(data, 'log_data', connection=connection)
