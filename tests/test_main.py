"""Tests for the ``main`` module"""

from pathlib import Path
from unittest import TestCase

from lmod_ingest.main import create_parser, ingest, migrate


class CreateParser(TestCase):
    """Test the parser returned by the ``create_parser`` function"""

    def setUp(self) -> None:
        """Create a new parser instance"""

        self.parser = create_parser()

    def test_ingest_command_parsing(self) -> None:
        """Test argument parsing by the ``ingest`` subparser"""

        args = create_parser().parse_args(['ingest', '/this/is/a/path'])
        self.assertIsInstance(args.path, Path)
        self.assertIs(args.callable, ingest)

    def test_migrate_command_parsing(self) -> None:
        """Test argument parsing by the ``migrate`` subparser"""

        args = create_parser().parse_args(['migrate'])
        self.assertFalse(args.sql)

        args = create_parser().parse_args(['migrate', '--sql'])
        self.assertTrue(args.sql)

        self.assertIs(args.callable, migrate)
