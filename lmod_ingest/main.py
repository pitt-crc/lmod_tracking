"""Top level application logic for handling command line parsing and data ingestion."""

import asyncio
from argparse import ArgumentParser
from pathlib import Path

from alembic import config, command
from dotenv import load_dotenv

from . import utils, __version__

# Database metadata
CURRENT_SCHEMA_VERSION = '0.2'
MIGRATIONS_DIR = Path(__file__).resolve().parent / 'migrations'


def ingest(path: Path) -> None:
    """Ingest data from a log file into the application database

    Args:
        path: Path of the log file
    """

    db_url = utils.fetch_db_url()
    asyncio.run(utils.ingest_file(path, db_url))


def migrate(sql: bool = False) -> None:
    """Migrate the application database to the current schema version

    Args:
        sql: Print SQL migration commands without executing them
    """

    alembic_cfg = config.Config()
    alembic_cfg.set_main_option('script_location', str(MIGRATIONS_DIR))
    alembic_cfg.set_main_option('sqlalchemy.url', utils.fetch_db_url())

    command.upgrade(alembic_cfg, revision=CURRENT_SCHEMA_VERSION, sql=sql)


def create_parser() -> ArgumentParser:
    """Create a new commandline parser

    Returns:
        A new command line parser
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


def main() -> None:  # pragma: nocover
    """Parse command line arguments and execute the application"""

    # Load application settings into the working environment
    load_dotenv(Path.home() / '.ingest.env')

    # Parse arguments and pass them to the appropriate function
    parser = create_parser()
    args = vars(parser.parse_args())

    try:
        args.pop('callable')(**args)

    except Exception as exc:
        parser.error(message=str(exc))
