"""Data ingestion utility for loading Lmod tracking logs into a MySQL database.

Usage:
  lmod_ingest ingest <path>
  lmod_ingest migrate [--sql]

Options:
  -h --help  Show this help text
  <path>     Path of the log data to ingest
  --sql      Print migration SQL but do not execute it
"""

import logging
import sys
from pathlib import Path

import sqlalchemy as sa
from alembic import config, command
from docopt import docopt
from dotenv import load_dotenv

from .utils import fetch_db_url, ingest_data_to_db, parse_log_data

# Load environmental variables
load_dotenv()

# Database metadata
MIGRATIONS_DIR = Path(__file__).resolve().parent / 'migrations'
SCHEMA_VERSION = '0.1'

# Pretty print log messages to the console
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)])


def ingest(path: Path) -> None:
    """Ingest data from a log file into the application database

    Args:
        path: Path of the lg file
    """

    db_engine = sa.engine.create_engine(url=fetch_db_url())
    with db_engine.connect() as connection:
        data = parse_log_data(path)
        ingest_data_to_db(data, 'log_data', connection=connection)


def migrate(sql: bool) -> None:
    """Migrate the application database to the required schema version

    Args:
    """

    alembic_cfg = config.Config()
    alembic_cfg.set_main_option('script_location', str(MIGRATIONS_DIR))
    alembic_cfg.set_main_option('sqlalchemy.url', fetch_db_url())

    command.upgrade(alembic_cfg, revision=SCHEMA_VERSION, sql=sql)


def main():
    """Parse command line arguments and execute the application"""

    arguments = docopt(__doc__)

    try:
        if arguments['ingest']:
            path = Path(arguments['<path>'])
            logging.info(f'Ingesting from {path.resolve()}')
            ingest(path)

        elif arguments['migrate']:
            migrate(arguments['--sql'])

    except Exception as caught:
        logging.error(str(caught))
