"""Tests for the ``utils`` module"""

import sqlite3
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest import TestCase
from unittest.mock import patch

import pandas as pd
import sqlalchemy as sa

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
            time=['1682407234.086799', '1682407234.103664'],
        ))

        # Write test data in the log format expected by the application
        with cls.test_path.open('w') as file:
            for _, row in cls.test_data.iterrows():
                file.write(
                    f"{row['date']} {row['node']} ModuleUsageTracking: user={row['user']} module={row['module']} path={row['path']} host={row['host']} time={row['time']}\n")

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


class TestIngestDataToDB(TestCase):
    """Test the ``ingest_data_to_db`` function"""

    def setUp(self):
        """Create a temporary test database in memory"""

        # Create an in-memory SQLite database
        self.db_connection = sqlite3.connect(':memory:')
        self.engine = sa.create_engine('sqlite://', echo=True)
        self.metadata = sa.MetaData()

        # Define a test table and create it in the database
        self.table_name = 'test_table'
        self.table = sa.Table(
            self.table_name,
            self.metadata,
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('name', sa.String),
        )

        self.metadata.create_all(bind=self.engine)

    def tearDown(self):
        """Close any open database connections"""

        self.db_connection.close()

    def test_ingest_data_to_db(self):
        # Define test data
        data = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie']
        })

        # Call the function to ingest data into the test table
        with self.engine.connect() as conn:
            ingest_data_to_db(data, self.table_name, conn)

        # Retrieve data from the database
        with self.engine.connect() as conn:
            rows = conn.execute(sa.select(self.table)).fetchall()
            self.assertEqual(len(rows), len(data))

            for i, row in enumerate(rows):
                self.assertEqual(row['id'], data['id'][i])
                self.assertEqual(row['name'], data['name'][i])

    def test_ingest_data_to_db_empty_data(self):
        # Define an empty DataFrame
        data = pd.DataFrame()

        # Call the function to ingest empty data
        ingest_data_to_db(data, self.table_name, self.db_connection)

        # Retrieve data from the database
        with self.engine.connect() as conn:
            result = conn.execute(sa.select([self.table]))

            # Verify that the table is empty
            rows = result.fetchall()
            self.assertEqual(len(rows), 0)
