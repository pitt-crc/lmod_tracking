"""A simple command line tool for ingesting Lmod log data into a MySQL database."""

import importlib.metadata

# Determine the application version number. Assign 0.0.0 when running in development.
try:
    __version__ = importlib.metadata.version('lmod-ingest')

except importlib.metadata.PackageNotFoundError: # pragma: nocover
    __version__ = '0.0.0'
