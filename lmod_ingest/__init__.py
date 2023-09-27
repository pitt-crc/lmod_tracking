"""A simple command line tool for ingesting Lmod log data into a Postgres database."""

import logging
import sys
from importlib.metadata import version, PackageNotFoundError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

try:
    __version__ = version('lmod-ingest')

except PackageNotFoundError:  # pragma: nocover
    __version__ = '0.0.0'
