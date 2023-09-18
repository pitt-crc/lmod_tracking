"""Tests for the ``utils`` module"""

import asyncio
import unittest
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest import TestCase
from unittest.mock import patch

import pandas as pd
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

from lmod_ingest.utils import fetch_db_url, parse_log_data, ingest_data_to_db


class TestFetchDBUrl(TestCase):
    """Tests for the ``fetch_db_url`` function"""

    @patch('os.getenv', side_effect=lambda x, default=None: {
        'DB_USER': 'testuser',
        'DB_PASS': 'testpass',
        'DB_HOST': 'testhost',
        'DB_PORT': '5433',
        'DB_NAME': 'testdb'
    }.get(x, default))
    def test_fetch_db_url_valid(self, mock_getenv) -> None:
        """Test the returned URI is valid and matches environmental variables"""

        expected_url = 'postgresql+asyncpg://testuser:testpass@/testdb?host=testhost&port=5433'
        self.assertEqual(expected_url, fetch_db_url())

    @patch('os.getenv', side_effect=lambda x, default=None: {
        'DB_USER': 'testuser',
        'DB_PASS': 'testpass',
        'DB_NAME': 'testdb'
    }.get(x, default))
    def test_fetch_db_url_defaults(self, mock_getenv) -> None:
        """Test ``DB_HOST`` and ``DB_PORT`` revert to defaults when not specified"""

        db_url = fetch_db_url()
        expected_url = 'postgresql+asyncpg://testuser:testpass@/testdb?host=localhost&port=5432'
        self.assertEqual(expected_url, db_url)

    def test_fetch_db_url_missing_user(self):
        """Test an error is raised when environmental variables are not specified"""

        with self.assertRaises(ValueError):
            fetch_db_url()


class ParseLogData(TestCase):
    """Tests for the ``parse_log_data`` function"""

    @classmethod
    def setUpClass(cls) -> None:
        """Create a temporary log file with test data"""

        cls.temp_file = NamedTemporaryFile()
        cls.test_path = Path(cls.temp_file.name)
        cls.test_data = pd.DataFrame(dict(
            date=['Apr 1 03:20:34', 'May 12 03:20:34'],
            node=['gpu-n53', 'smp-n10'],
            user=['user1', 'user2'],
            module=['gcc/8.2.0', 'openmpi'],
            path=['/software/gcc/8.2.0.lua', '/software/gcc/openmpi/4.0.3.lua'],
            host=['gpu-n53.crc.pitt.edu', 'smp-n10.crc.pitt.edu'],
            time=[1682407234.086799, 1682407234.103664],
        ))

        # Write test data in the log format expected by the application
        log_record_format = "{date} {node} ModuleUsageTracking: user={user} module={module} path={path} host={host} time={time}\n"
        with cls.test_path.open('w') as file:
            for _, row in cls.test_data.iterrows():
                file.write(log_record_format.format(**row))

    @classmethod
    def tearDownClass(cls) -> None:
        """Close any open file handles"""

        cls.temp_file.close()

    def test_parse_log_data_valid(self) -> None:
        """Teste the parsed file data matches the test data"""

        result_df = parse_log_data(self.test_path)
        expected_df = pd.DataFrame({
            'user': self.test_data.user,
            'module': self.test_data.module,
            'path': self.test_data.path,
            'host': self.test_data.host,
            'time': pd.to_datetime(self.test_data.time, unit='s'),
            'package': ['gcc', 'openmpi'],
            'version': ['8.2.0', None],  # No version information in the sample data
            'logname': [str(self.test_path), str(self.test_path)]
        })

        pd.testing.assert_frame_equal(expected_df, result_df)


class TestIngestDataToDB(unittest.IsolatedAsyncioTestCase):
    """Tests for the ``ingest_data_to_db`` method"""

    async def asyncSetUp(self) -> None:
        """Create a temporary table to run tests against"""

        metadata = sa.MetaData()
        self.engine = create_async_engine(url='postgresql+asyncpg://testing@localhost:5432/test_db')
        self.table = sa.Table('test_table', metadata, sa.Column('column1', sa.Integer), sa.Column('column2', sa.Integer))

        # Create a table for testing
        create_expression = sa.schema.CreateTable(self.table)
        async with self.engine.connect() as connection:
            await connection.execute(create_expression)

    async def asyncTearDown(self) -> None:
        """Teardown database constructs"""

        delete_expression = sa.schema.DropTable(self.table)
        async with self.engine.connect() as connection:
            await connection.execute(delete_expression)

    async def test_data_ingested(self) -> None:
        """Test data is ingested into the database table"""

        data = pd.DataFrame({'column1': [1, 2, 3], 'column2': [1, 2, 3]})
        with self.engine.connect() as connection:
            asyncio.run(ingest_data_to_db(data, self.table.name, connection))

        with self.engine.connect() as connection:
            recovered = pd.read_sql(sa.select(self.table), connection)

        pd.testing.assert_frame_equal(data, recovered)

    async def test_empty_data(self) -> None:
        """Test empy data frames are handled without error"""

        with self.engine.connect() as connection:
            asyncio.run(ingest_data_to_db(pd.DataFrame(), self.table.name, connection))

        with self.engine.connect() as connection:
            recovered = pd.read_sql(sa.select(self.table), connection)

        self.assertTrue(recovered.empty)

    async def test_missing_table(self) -> None:
        """Test an error is raised for database tables that do not exist"""

        with self.assertRaises(ValueError), self.engine.connect() as connection:
            asyncio.run(ingest_data_to_db(pd.DataFrame(), 'fake_table', connection))
