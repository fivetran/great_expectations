"""Integration tests for SingleStore (formerly MemSQL).

Validates GX functionality against a live SingleStore instance.
"""

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations import get_context
from great_expectations.expectations.row_conditions import Column
from tests.integration.test_utils.data_source_config.generic_sql import (
    GenericSQLBatchTestSetup,
    GenericSQLDatasourceTestConfig,
)

pytestmark = pytest.mark.singlestore

CONNECTION_STRING = "singlestoredb://root:test_superuser@127.0.0.1:3306/test_ci"


class TestSingleStore:
    """Smoke tests for SingleStore compatibility."""

    DATA = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie"],
            "age": [30, 25, 35],
        }
    )

    def _make_setup(self) -> GenericSQLBatchTestSetup:
        return GenericSQLBatchTestSetup(
            config=GenericSQLDatasourceTestConfig(
                connection_string=CONNECTION_STRING,
            ),
            data=self.DATA,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

    def test_can_connect_and_validate(self) -> None:
        batch_setup = self._make_setup()

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnValuesToBeInSet(
                    column="name",
                    value_set=["Alice", "Bob", "Charlie"],
                )
            )
        assert result.success

    def test_numeric_expectation(self) -> None:
        batch_setup = self._make_setup()

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnSumToBeBetween(
                    column="age",
                    min_value=89,
                    max_value=91,
                )
            )
        assert result.success

    def test_row_count(self) -> None:
        batch_setup = self._make_setup()

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectTableRowCountToBeBetween(
                    min_value=3,
                    max_value=3,
                )
            )
        assert result.success

    def test_regex_expectation(self) -> None:
        batch_setup = self._make_setup()

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnValuesToMatchRegex(
                    column="name",
                    regex="^[A-Z].*",
                )
            )
        assert result.success

    def test_unique_values(self) -> None:
        batch_setup = self._make_setup()

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnValuesToBeUnique(
                    column="name",
                )
            )
        assert result.success

    def test_row_condition(self) -> None:
        batch_setup = self._make_setup()

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnValuesToBeUnique(
                    column="name",
                    row_condition=Column("name").is_not_in(["Alice"]),
                )
            )
        assert result.success

    def test_unexpected_rows_expectation(self) -> None:
        batch_setup = self._make_setup()

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.UnexpectedRowsExpectation(
                    unexpected_rows_query="SELECT * FROM {batch} WHERE age < 0",
                )
            )
        assert result.success


class TestSingleStoreQuotedIdentifiers:
    """Tests for columns whose names require quoting (spaces, reserved words)."""

    DATA = pd.DataFrame(
        {
            "user name": ["Alice", "Bob", "Charlie"],
            "select": [10, 20, 30],
            "UserName": ["alice", "bob", "charlie"],
        }
    )

    def _make_setup(self) -> GenericSQLBatchTestSetup:
        return GenericSQLBatchTestSetup(
            config=GenericSQLDatasourceTestConfig(
                connection_string=CONNECTION_STRING,
            ),
            data=self.DATA,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

    def test_column_with_space(self) -> None:
        batch_setup = self._make_setup()

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnValuesToBeInSet(
                    column="user name",
                    value_set=["Alice", "Bob", "Charlie"],
                )
            )
        assert result.success

    def test_column_with_reserved_word(self) -> None:
        batch_setup = self._make_setup()

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnSumToBeBetween(
                    column="select",
                    min_value=59,
                    max_value=61,
                )
            )
        assert result.success

    def test_unique_values_quoted_column(self) -> None:
        """Exercises the quoted-identifier path in ColumnValuesUnique temp table logic."""
        batch_setup = self._make_setup()

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnValuesToBeUnique(
                    column="user name",
                )
            )
        assert result.success

    def test_mixed_case_column(self) -> None:
        """Verifies that a mixed-case column name round-trips correctly through quoting."""
        batch_setup = self._make_setup()

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnValuesToBeInSet(
                    column="UserName",
                    value_set=["alice", "bob", "charlie"],
                )
            )
        assert result.success
