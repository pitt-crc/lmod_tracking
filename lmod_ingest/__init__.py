"""A simple command line tool for ingesting Lmod log data into a MySQL database."""

import importlib.metadata

try:
    __version__ = importlib.metadata.version('quota-notifier')

except importlib.metadata.PackageNotFoundError:
    __version__ = '0.0.0'
