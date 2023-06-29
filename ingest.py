#!/usr/bin/env python3
"""Data ingestion utility for loading Lmod tracking data from log files into a MySQL database."""

import logging
import os
import sys
from pathlib import Path

import pandas as pd
import sqlalchemy as sa
from dotenv import load_dotenv


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


def parse_log_data(path: Path | str) -> pd.DataFrame:
    """Parse, format, and return data from a Lmod log file

    he returned DataFrame includes columns for ``user``, ``module``, ``path``,
    ``node``, ``time``, ``package``, and ``version``.

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
        names=['user', 'module', 'path', 'node', 'time'],
        engine='python'
    )

    # Convert UTC decimals to a MYSql compatible string format
    log_data['time'] = pd.to_datetime(log_data['time'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S.%f')

    # Split the module name into package names and versions
    log_data[['package', 'version']] = log_data.module.str.split('/', n=1, expand=True)
    return log_data.dropna(subset=['user'])


def ingest_data_to_db(data: pd.DataFrame, connection: sa.Connection) -> None:
    """Ingest data into a database

    Args:
        data: A DataFrame returned by ``parse_log_data``
        connection: An open database connection
    """

    # Upload data into a temporary scratch table
    logging.info('loading data into scratch table ...')
    data.to_sql(name='scratch', con=connection, if_exists='replace', index_label='id')

    # Move data from scratch table into other tables in accordance with the DB schema
    # We use ``INSERT IGNORE`` instead of ``ON DUPLICATE KEY UPDATE`` for the better performance
    logging.info('updating user table (1/4) ...')
    connection.exec_driver_sql("""
        INSERT IGNORE INTO user (name)
        SELECT user AS name
        FROM scratch;
    """)

    logging.info('updating package table (2/4) ...')
    connection.exec_driver_sql("""
        INSERT IGNORE INTO package (name, version, path)
        SELECT package AS name, version, path
        FROM scratch;
    """)

    logging.info('updating host table (2/4) ...')
    connection.exec_driver_sql("""
        INSERT IGNORE INTO host (name)
        SELECT node AS name
        FROM scratch;
    """)

    logging.info('updating usage table (4/4) ...')
    connection.exec_driver_sql('SET FOREIGN_KEY_CHECKS=0;')
    connection.exec_driver_sql("""
        INSERT IGNORE INTO module_usage (user_id, host_id, package_id, load_time)
        SELECT user.id as user_id, host.id as host_id, package.id as package_id, scratch.time as load_time
        FROM scratch
        JOIN user ON user.name = scratch.user
        JOIN host ON host.name = scratch.node
        JOIN package ON package.name = scratch.package;
    """)

    connection.commit()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Fetch the log file path from the console
    if not sys.argv[1:]:
        print('You must specify one or more log files to ingest')
        exit(1)

    for fpath in sys.argv[1:]:
        logging.info(f'Ingesting {fpath}')
        with sa.engine.create_engine(fetch_db_url()).connect() as connection:
            ingest_data_to_db(
                data=parse_log_data(fpath),
                connection=connection
            )
