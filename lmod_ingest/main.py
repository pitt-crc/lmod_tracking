"""Data ingestion utility for loading Lmod tracking logs into a MySQL database.

Usage:
  lmod_ingest ingest <path>
  lmod_ingest migrate [--views]

Options:
  <path>     Path of the log data to ingest
  -h --help  Show this help text
"""

import logging
from pathlib import Path

import sqlalchemy as sa
from alembic import config, command
from docopt import docopt
from dotenv import load_dotenv

from .utils import fetch_db_url, ingest_data_to_db, parse_log_data

load_dotenv()

MIGRATIONS_DIR = Path(__file__).resolve().parent / 'migrations'
SCHEMA_VERSION = '0.1'
SCHEMA_VERSION_VIEWS = '0.1.views'

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def ingest(path: Path) -> None:
    """Ingest data from a log file into the application database

    Args:
        path: Path of the lg file
    """

    db_engine = sa.engine.create_engine(url=fetch_db_url())
    with db_engine.connect() as connection:
        data = parse_log_data(path)
        ingest_data_to_db(data, 'log_data', connection=connection)


def migrate(views: bool = False) -> None:
    """Migrate the application database to the given schema version

    Args:
        views: Whether to create views during the migration
    """

    alembic_cfg = config.Config()
    alembic_cfg.set_main_option('script_location', str(MIGRATIONS_DIR))
    alembic_cfg.set_main_option('sqlalchemy.url', fetch_db_url())

    version = SCHEMA_VERSION_VIEWS if views else SCHEMA_VERSION
    command.upgrade(alembic_cfg, revision=version)


def main():
    """The primary application entrypoint

    Parse commandline arguments and ingest data from the resulting file path
    into the database.
    """

    arguments = docopt(__doc__)

    try:
        if arguments['ingest']:
            ingest(arguments['<path>'])

        elif arguments['migrate']:
            migrate()

    except Exception as caught:
        logging.error(str(caught))
