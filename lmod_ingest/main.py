"""Data ingestion utility for loading Lmod tracking logs into a MySQL database."""

import logging
import sys
import time
from argparse import ArgumentParser
from pathlib import Path

from alembic import config, command
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine

from . import __version__
from .utils import fetch_db_url, ingest_data_to_db, parse_log_data

# Pretty print log messages to the console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)])

# Database metadata
MIGRATIONS_DIR = Path(__file__).resolve().parent / 'migrations'
SCHEMA_VERSION = '0.1'


async def ingest(path: Path) -> None:
    """Ingest data from a log file into the application database

    Args:
        path: Path of the log file
    """

    logging.info(f'Ingesting {path.resolve()}')
    db_engine = create_async_engine(url=fetch_db_url())
    async with db_engine.connect() as connection:
        logging.info(f'Parsing log data')
        data = parse_log_data(path)

        logging.info(f'Loading data into database')
        start = time.time()
        await ingest_data_to_db(data, 'log_data', connection=connection)
        logging.info(f'Ingested {len(data)} log entries in {time.time() - start:.2f} seconds')


def migrate(sql: bool = False) -> None:
    """Migrate the application database to the required schema version

    Args:
        sql: Print SQL migration commands without executing them
    """

    alembic_cfg = config.Config()
    alembic_cfg.set_main_option('script_location', str(MIGRATIONS_DIR))
    alembic_cfg.set_main_option('sqlalchemy.url', fetch_db_url())

    command.upgrade(alembic_cfg, revision=SCHEMA_VERSION, sql=sql)


def create_parser() -> ArgumentParser:
    """Create a new commandline parser

    Returns:
        A new ``ArgumentParser``
    """

    parser = ArgumentParser(description='Data ingestion utility for loading Lmod tracking logs into a MySQL database')
    parser.add_argument('--version', action='version', version=__version__)
    subparsers = parser.add_subparsers()

    ingest_parser = subparsers.add_parser('ingest')
    ingest_parser.set_defaults(callable=ingest)
    ingest_parser.add_argument('path', type=Path, help='log path to ingest data from')

    migrate_parser = subparsers.add_parser('migrate')
    migrate_parser.set_defaults(callable=migrate)
    migrate_parser.add_argument('--sql', action='store_true', help='display migration SQL but do not execute it')
    return parser


def main():  # pragma: nocover
    """Parse command line arguments and execute the application"""

    # Load application settings into the working environment
    load_dotenv(Path.home() / '.ingest.env')

    parser = create_parser()
    args = vars(parser.parse_args())
    args.pop('callable')(**args)
