"""A simple command line tool for ingesting Lmod log data into a PostgreSQL database."""

import importlib.metadata
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

try:
    __version__ = importlib.metadata.version('lmod-ingest')

except importlib.metadata.PackageNotFoundError:  # pragma: nocover
    __version__ = '0.0.0'
