"""Tests for the ``main`` module"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock

from lmod_ingest.main import main  # Replace 'lmod_ingest.main' with the actual module name


class Main(unittest.TestCase):
    """Test argument parsing by the `main.main` function"""

    @unittest.mock.patch('lmod_ingest.main.ingest')
    def test_ingest(self, mock_ingest) -> None:
        """Test the ``ingest`` subparser calls the ``ingest`` method"""

        input_path = Path('/some/path')
        arguments = {'ingest': True, '<path>': input_path}
        with unittest.mock.patch('lmod_ingest.main.docopt', return_value=arguments):
            main()

        mock_ingest.assert_called_once_with(path=input_path)

    @unittest.mock.patch('lmod_ingest.main.migrate')
    def test_migrate_is_called(self, mock_migrate) -> None:
        """Test the ``migrate`` subparser with ``sql=False``"""

        arguments = {'migrate': True, '--sql': False}
        with unittest.mock.patch('lmod_ingest.main.docopt', return_value=arguments):
            main()

        mock_migrate.assert_called_once_with(sql=False)

    @unittest.mock.patch('lmod_ingest.main.migrate')
    def test_migrate_is_called_with_sql(self, mock_migrate) -> None:
        """Test the ``migrate`` subparser with ``sql=True``"""

        arguments = {'migrate': True, '--sql': True}
        with unittest.mock.patch('lmod_ingest.main.docopt', return_value=arguments):
            main()

        mock_migrate.assert_called_once_with(sql=True)
