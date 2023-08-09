"""Data ingestion utility for loading Lmod tracking logs into a MySQL database.

Usage:
  ingest.py <path>

Options:
  <path>     Path of the log data to ingest
  -h --help  Show this help text
"""

import logging
import os
from pathlib import Path

import pandas as pd
import sqlalchemy as sa
from docopt import docopt
from dotenv import load_dotenv
from sqlalchemy.dialects.mysql import insert

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

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
        raise ValueError('Database credentials (DB_USER, DB_PASSWORD) not configured in the working environment')

    return f'mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'


def parse_log_data(path: Path) -> pd.DataFrame:
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


def ingest_data_to_db(data: pd.DataFrame, name: str, connection: sa.Connection) -> None:
    """Ingest data into a database

    Args:
        data: A DataFrame returned by ``parse_log_data``
        name: Name of the database to ingest to
        connection: An open database connection
    """

    table = sa.Table(name, sa.MetaData(), autoload_with=connection.engine)
    insert_stmt = insert(table).values(data.to_dict(orient="records"))
    on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(insert_stmt.inserted)
    connection.execute(on_duplicate_key_stmt)


if __name__ == '__main__':
    arguments = docopt(__doc__)
    path = Path(arguments['<path>'])

    try:
        db_engine = sa.engine.create_engine(url=fetch_db_url())
        with db_engine.connect() as connection:
            data = parse_log_data(path)
            ingest_data_to_db(data, 'log_data', connection=connection)

    except Exception as caught:
        logging.error(str(caught))
