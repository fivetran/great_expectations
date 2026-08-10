"""Ad-hoc integration tests for arbitrary SQL backends.

See the ``TestGenericSQL`` docstring for required environment variables
and usage instructions.
"""

import os

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations import get_context
from tests.integration.test_utils.data_source_config.generic_sql import (
    GenericSQLBatchTestSetup,
    GenericSQLDatasourceTestConfig,
)

pytestmark = pytest.mark.generic_sql


@pytest.fixture()
def connection_string() -> str:
    connection_string = os.environ.get("GX_TEST_GENERIC_SQL_CONNECTION_STRING")
    if not connection_string:
        raise ValueError("GX_TEST_GENERIC_SQL_CONNECTION_STRING environment variable is not set")
    return connection_string


class TestGenericSQL:
    """Ad-hoc smoke tests for SQL datasources not covered by CI.

    Use this class to verify basic Great Expectations functionality against
    any SQLAlchemy-compatible database.  These tests are **not** run in CI;
    they are intended for local, on-demand validation of new or uncommon SQL
    backends.

    Configure the target database with environment variables, then run::

        pytest -v -m generic_sql

    Environment variables
    ---------------------
    ``GX_TEST_GENERIC_SQL_CONNECTION_STRING`` (required)
        SQLAlchemy connection string for the target database, e.g.
        ``singlestoredb://user:pass@host:3306/db``.
    ``GX_TEST_GENERIC_SQL_AUTOCOMMIT``
        Set to any non-empty value to skip explicit commits against the target
        database, for a database that auto-commits and does not support normal
        transactions. Read once, when the batch is set up, and applied only to
        that batch - it does not register the target database's dialect
        globally. Leave unset or empty for databases that use normal
        transactions. The same behavior can also be requested in code by
        constructing ``GenericSQLDatasourceTestConfig(autocommit=True)``.
    """

    DATA = pd.DataFrame(
        {
            "name": ["alice", "bob", "charlie"],
            "age": [30, 25, 35],
        }
    )

    def _make_setup(self, connection_string: str) -> GenericSQLBatchTestSetup:
        return GenericSQLBatchTestSetup(
            config=GenericSQLDatasourceTestConfig(
                connection_string=connection_string,
            ),
            data=self.DATA,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

    def test_can_connect_and_validate(self, connection_string: str) -> None:
        batch_setup = self._make_setup(connection_string)

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnValuesToBeInSet(
                    column="name",
                    value_set=["alice", "bob", "charlie"],
                )
            )
        assert result.success

    def test_numeric_expectation(self, connection_string: str) -> None:
        batch_setup = self._make_setup(connection_string)

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnSumToBeBetween(
                    column="age",
                    min_value=89,
                    max_value=91,
                )
            )
        assert result.success

    def test_row_count(self, connection_string: str) -> None:
        batch_setup = self._make_setup(connection_string)

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectTableRowCountToBeBetween(
                    min_value=3,
                    max_value=3,
                )
            )
        assert result.success
