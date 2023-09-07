"""Data ingestion utility for loading Lmod tracking logs into a MySQL database.

Usage:
  lmod_ingest ingest <path>
  lmod_ingest migrate [--sql]
  lmod_ingest --version

Options:
  -h --help     Show this help text
  <path>        Path of the log data to ingest
  --sql         Print migration SQL but do not execute it
  --version     Show the application version number
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

from alembic import config, command
from docopt import docopt
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine

from . import __version__
from .utils import fetch_db_url, ingest_data_to_db, parse_log_data

# Load environmental variables
load_dotenv(Path.home() / '.ingest.env')

# Database metadata
MIGRATIONS_DIR = Path(__file__).resolve().parent / 'migrations'
SCHEMA_VERSION = '0.1'

# Pretty print log messages to the console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)])


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


def main():
    """Parse command line arguments and execute the application"""

    arguments = docopt(__doc__, version=__version__)

    try:
        if arguments['ingest']:
            asyncio.get_event_loop().run_until_complete(
                ingest(Path(arguments['<path>']))
            )

        elif arguments['migrate']:
            migrate(arguments['--sql'])

    except Exception as caught:
        logging.error(str(caught).split('\n')[0])
