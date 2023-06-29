import logging
from pathlib import Path

import pandas as pd
import sqlalchemy as sa


def parse_log_data(path: Path | str) -> pd.DataFrame:
    """Parse, format, and return data from a module tracking log file

    Args:
        path: The log file path to parse

    Returns:
        A DataFrame with columns for ``user``, ``module``, ``path``, ``node``, and ``time``
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

    connection.commit()

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
