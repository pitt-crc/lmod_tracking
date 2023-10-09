"""Tests for the ``utils`` module"""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest import TestCase, IsolatedAsyncioTestCase

import pandas as pd
import sqlalchemy as sa
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.asyncio import create_async_engine

from lmod_ingest.utils import DEFAULT_HOST, DEFAULT_PORT
from lmod_ingest.utils import fetch_db_url, parse_log_data, ingest_data_to_db
from . import mock


class TestFetchDBUrl(TestCase):
    """Tests for the ``fetch_db_url`` function"""

    def setUp(self) -> None:
        """Clear the working environment"""

        self.old_env = os.environ.copy()
        os.environ.clear()

    def tearDown(self) -> None:
        """Restore the working environment"""

        os.environ.clear()
        os.environ.update(self.old_env)

    def test_fetch_db_from_env(self) -> None:
        """Test the returned URI matches environmental variables"""

        db_user = 'testuser'
        db_pass = 'testpass'
        db_host = 'testhost'
        db_port = '1234'
        db_name = 'testdb'

        os.environ.update(
            DB_USER=db_user,
            DB_PASS=db_pass,
            DB_HOST=db_host,
            DB_PORT=db_port,
            DB_NAME=db_name
        )

        expected_url = f'postgresql+asyncpg://{db_user}:{db_pass}@/{db_name}?host={db_host}&port={db_port}'
        self.assertEqual(expected_url, fetch_db_url())

    def test_fetch_db_url_defaults(self) -> None:
        """Test ``DB_HOST`` and ``DB_PORT`` revert to defaults when not specified"""

        db_user = 'testuser'
        db_pass = 'testpass'
        db_name = 'testdb'

        os.environ.update(
            DB_USER=db_user,
            DB_PASS=db_pass,
            DB_NAME=db_name
        )

        expected_url = f'postgresql+asyncpg://{db_user}:{db_pass}@/{db_name}?host={DEFAULT_HOST}&port={DEFAULT_PORT}'
        self.assertEqual(expected_url, fetch_db_url())

    def test_fetch_db_url_missing_values(self):
        """Test an error is raised when environmental variables are not specified"""

        with self.assertRaises(ValueError):
            fetch_db_url()


class ParseLogData(TestCase):
    """Tests for the ``parse_log_data`` function"""

    def test_parse_valid_data(self) -> None:
        """Teste the parsed file data matches the test data"""

        mock_data = mock.get_mock_data()
        mock_path = mock.TEST_PATH
        expected_df = pd.DataFrame({
            'user': mock_data.user,
            'module': mock_data.module,
            'path': mock_data.path,
            'host': mock_data.host,
            'time': pd.to_datetime(mock_data.time, unit='s'),
            'package': ['gcc', 'openmpi'],
            'version': ['8.2.0', None],
            'logname': [str(mock_path), str(mock_path)]
        })

        result_df = parse_log_data(mock.TEST_PATH)
        pd.testing.assert_frame_equal(expected_df, result_df)

    def test_parse_invalid_data(self) -> None:
        """Test an error is raised when parsing data with an incorrect record format"""

        with self.assertRaises(ValueError), NamedTemporaryFile() as temp_file:
            temp_file.write(b'this is not valid data')
            parse_log_data(Path(temp_file.name))

    def test_parse_empty_file(self) -> None:
        """Test an error is raised when parsing an empty file"""

        with self.assertRaises(ValueError), NamedTemporaryFile() as temp_file:
            parse_log_data(Path(temp_file.name))


class TestIngestDataToDB(IsolatedAsyncioTestCase):
    """Tests for the ``ingest_data_to_db`` function"""

    async def asyncSetUp(self) -> None:
        """Create a temporary table to run tests against"""

        # Define a database table to test against
        db_url = fetch_db_url()
        print(db_url)
        self.engine = create_async_engine(db_url)
        self.table = sa.Table(
            'test_table', sa.MetaData(),
            sa.Column('column1', sa.Integer),
            sa.Column('column2', sa.Integer))

        # Clean up remnants from old tests and create the test table
        await self.delete_test_table(self.table)
        await self.create_test_table(self.table)

    async def asyncTearDown(self) -> None:
        """Teardown database constructs"""

        await self.delete_test_table(self.table)

    async def create_test_table(self, table: sa.Table) -> None:
        """Create a table in the database if it does not already exist

        Args:
            table: The Sqlalchemy table to create
        """

        create_expression = sa.schema.CreateTable(table)
        async with self.engine.connect() as connection:
            await connection.execute(create_expression)
            await connection.commit()

    async def delete_test_table(self, table: sa.Table) -> None:
        """Delete a table from the database if it already exists

        Args:
            table: The Sqlalchemy table to delete
        """

        delete_expression = sa.schema.DropTable(table, if_exists=True)
        async with self.engine.connect() as connection:
            await connection.execute(delete_expression)
            await connection.commit()

    async def test_data_ingested(self) -> None:
        """Test data is ingested into the database table"""

        data = pd.DataFrame({'column1': [1, 2, 3], 'column2': [4, 5, 6]})
        async with self.engine.connect() as connection:
            await ingest_data_to_db(data, self.table.name, connection)

        async with self.engine.connect() as connection:
            result = await connection.execute(sa.select(self.table))
            result_df = pd.DataFrame(result.all())

        pd.testing.assert_frame_equal(data, result_df)

    async def test_empty_data(self) -> None:
        """Test empty data frames are handled without error"""

        async with self.engine.connect() as connection:
            await ingest_data_to_db(pd.DataFrame(), self.table.name, connection)

        async with self.engine.connect() as connection:
            result = await connection.execute(sa.select(self.table))
            self.assertIsNone(result.scalar_one_or_none())

    async def test_missing_table(self) -> None:
        """Test an error is raised for database tables that do not exist"""

        data = pd.DataFrame({'column1': [1, 2, 3], 'column2': [4, 5, 6]})
        async with self.engine.connect() as connection:
            with self.assertRaises(sa.exc.InvalidRequestError):
                await ingest_data_to_db(data, 'fake_table', connection)

    async def test_incorrect_table_schema(self) -> None:
        """Test an error is raised when the ingested data does not match the table schema"""

        fake_data = pd.DataFrame({'fake_column': [1, 2, 3]})
        with self.assertRaises(sa.exc.CompileError):
            async with self.engine.connect() as connection:
                await ingest_data_to_db(fake_data, self.table.name, connection)
