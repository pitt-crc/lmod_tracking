"""
A simple command line tool for ingesting Lmod log data into a PostgreSQL database.

[Lmod](https://lmod.readthedocs.io/en/latest/index.html) is a popular
utility for managing user runtime environments on supercomputing clusters.
To better understand system usage patterns, many system administrators
leverage Lmod logs to track what software is being loaded by users and where.
The `lmod-ingest` utility is a simple ETL tool used to ingest Lmod log
records into a Postgres database in a useful format.
"""

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
