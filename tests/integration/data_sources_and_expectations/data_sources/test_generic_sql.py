"""Tests for the generic SQL datasource test helper.

These tests exercise ``GenericSQLBatchTestSetup`` by connecting to a real
database (Postgres by default) via a plain connection string, proving that the
helper works end-to-end without any dialect-specific config class.

Override the default connection string by setting the
``GX_TEST_GENERIC_SQL_CONNECTION_STRING`` environment variable.
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

DEFAULT_CONNECTION_STRING = "postgresql+psycopg2://postgres@localhost:5432/test_ci"

pytestmark = pytest.mark.postgresql


@pytest.fixture()
def connection_string() -> str:
    return os.environ.get("GX_TEST_GENERIC_SQL_CONNECTION_STRING", DEFAULT_CONNECTION_STRING)


class TestGenericSQL:
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
