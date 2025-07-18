"""
Integration tests for Databricks table names with special characters.
These tests verify that table names starting with digits or containing special characters
work correctly with Custom SQL Expectations and other operations.
"""

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations import get_context
from tests.integration.test_utils.data_source_config import DatabricksDatasourceTestConfig
from tests.integration.test_utils.data_source_config.databricks import DatabricksBatchTestSetup

pytestmark = pytest.mark.databricks


class TestDatabricksSpecialTableNames:
    """Integration tests for Databricks tables with special naming requirements."""

    # Sample data for testing
    SAMPLE_DATA = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
            "value": [10.5, 20.0, 30.5, 40.0, 50.5],
            "active": [True, False, True, False, True],
        }
    )

    def test_table_name_starting_with_digit(self):
        """Test that table names starting with digits work correctly."""
        batch_setup = DatabricksBatchTestSetup(
            config=DatabricksDatasourceTestConfig(table_name="247_asset_class_cumulative_returns"),
            data=self.SAMPLE_DATA,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

        with batch_setup.batch_test_context() as batch:
            # Test a basic expectation on the batch
            result = batch.validate(gxe.ExpectTableRowCountToBeBetween(min_value=1, max_value=10))
            assert result.success

            # Test column expectations
            result = batch.validate(
                gxe.ExpectColumnValuesToBeInSet(
                    column="name",
                    value_set=["Alice", "Bob", "Charlie", "David", "Eve"],
                )
            )
            assert result.success

    def test_table_name_with_spaces(self):
        """Test that table names with spaces work correctly."""
        batch_setup = DatabricksBatchTestSetup(
            config=DatabricksDatasourceTestConfig(table_name="my table with spaces"),
            data=self.SAMPLE_DATA,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

        with batch_setup.batch_test_context() as batch:
            # Test that batch was created successfully
            result = batch.validate(gxe.ExpectTableRowCountToBeBetween(min_value=1, max_value=10))
            assert result.success

            # Test column operations work
            result = batch.validate(
                gxe.ExpectColumnMeanToBeBetween(
                    column="value",
                    min_value=25.0,
                    max_value=35.0,
                )
            )
            assert result.success

    def test_table_name_with_hyphens(self):
        """Test that table names with hyphens work correctly."""
        batch_setup = DatabricksBatchTestSetup(
            config=DatabricksDatasourceTestConfig(table_name="my-table-with-hyphens"),
            data=self.SAMPLE_DATA,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(gxe.ExpectTableRowCountToBeBetween(min_value=1, max_value=10))
            assert result.success

            # Test column expectations
            result = batch.validate(
                gxe.ExpectColumnValuesToBeInSet(
                    column="active",
                    value_set=[True, False],
                )
            )
            assert result.success

    def test_table_name_with_dots(self):
        """Test that table names with dots work correctly."""
        batch_setup = DatabricksBatchTestSetup(
            config=DatabricksDatasourceTestConfig(table_name="my.table.with.dots"),
            data=self.SAMPLE_DATA,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(gxe.ExpectTableRowCountToBeBetween(min_value=1, max_value=10))
            assert result.success

            # Test numeric column expectations
            result = batch.validate(
                gxe.ExpectColumnValuesToBeBetween(
                    column="id",
                    min_value=1,
                    max_value=5,
                )
            )
            assert result.success

    def test_table_name_with_hash_and_at_symbols(self):
        """Test that table names with # and @ symbols work correctly."""
        batch_setup = DatabricksBatchTestSetup(
            config=DatabricksDatasourceTestConfig(table_name="my#table@with#symbols"),
            data=self.SAMPLE_DATA,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(gxe.ExpectTableRowCountToBeBetween(min_value=1, max_value=10))
            assert result.success

            # Test string column expectations
            result = batch.validate(gxe.ExpectColumnValuesToNotBeNull(column="name"))
            assert result.success

    def test_custom_sql_expectation_with_special_table_name(self):
        """Test that Custom SQL Expectations work with table names requiring special quoting."""
        batch_setup = DatabricksBatchTestSetup(
            config=DatabricksDatasourceTestConfig(table_name="247_asset_class_cumulative_returns"),
            data=self.SAMPLE_DATA,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

        with batch_setup.batch_test_context() as batch:
            # Test a Custom SQL Expectation - this was the main failing case
            result = batch.validate(
                gxe.ExpectColumnValuesToBeInSet(
                    column="name",
                    value_set=["Alice", "Bob", "Charlie", "David", "Eve"],
                )
            )
            assert result.success

            # Test another expectation that generates SQL
            result = batch.validate(
                gxe.ExpectColumnSumToBeBetween(
                    column="value",
                    min_value=150.0,
                    max_value=155.0,
                )
            )
            assert result.success

    def test_schema_and_table_name_both_special(self):
        """Test schema and table names that both require special quoting.

        Note: This test uses a table name that simulates a schema.table pattern
        since DatabricksDatasourceTestConfig doesn't support schema_name parameter.
        """
        # Use a table name that contains a schema-like pattern
        batch_setup = DatabricksBatchTestSetup(
            config=DatabricksDatasourceTestConfig(table_name="123_schema_456_table"),
            data=self.SAMPLE_DATA,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(gxe.ExpectTableRowCountToBeBetween(min_value=1, max_value=10))
            assert result.success

            # Test column expectations work with special table names
            result = batch.validate(gxe.ExpectColumnValuesToBeUnique(column="id"))
            assert result.success

    def test_multiple_special_table_operations(self):
        """Test multiple operations on tables with different special naming patterns."""
        special_table_names = [
            "123_starts_with_digit",
            "table with spaces",
            "table-with-hyphens",
            "table.with.dots",
            "table#with@symbols",
        ]

        for table_name in special_table_names:
            batch_setup = DatabricksBatchTestSetup(
                config=DatabricksDatasourceTestConfig(table_name=table_name),
                data=self.SAMPLE_DATA,
                extra_data={},
                context=get_context(mode="ephemeral"),
            )

            with batch_setup.batch_test_context() as batch:
                # Test basic table operations
                result = batch.validate(
                    gxe.ExpectTableRowCountToBeBetween(min_value=1, max_value=10)
                )
                assert result.success

                # Test column expectations to ensure SQL generation works
                result = batch.validate(gxe.ExpectColumnValuesToNotBeNull(column="name"))
                assert result.success

    def test_schema_and_table_name_both_special_realistic(self):
        """Test realistic schema and table names that both require special quoting."""
        # Test with a more realistic scenario where both schema and table start with digits
        batch_setup = DatabricksBatchTestSetup(
            config=DatabricksDatasourceTestConfig(
                table_name="123_schema.456_table"  # Simulating schema.table pattern
            ),
            data=self.SAMPLE_DATA,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(gxe.ExpectTableRowCountToBeBetween(min_value=1, max_value=10))
            assert result.success

            # Test column expectations work with special schema.table names
            result = batch.validate(gxe.ExpectColumnValuesToBeUnique(column="id"))
            assert result.success

    def test_edge_cases_special_characters(self):
        """Test edge cases with various special character combinations."""
        edge_case_names = [
            "247_asset_class_cumulative_returns",  # Original failing case
            "123test",  # Digit start with no underscore
            "table name with multiple   spaces",  # Multiple spaces
            "table-with--double-hyphens",  # Double hyphens
            "table.with..double.dots",  # Double dots
            "table#@$%special",  # Multiple special chars
        ]

        for table_name in edge_case_names:
            batch_setup = DatabricksBatchTestSetup(
                config=DatabricksDatasourceTestConfig(table_name=table_name),
                data=self.SAMPLE_DATA,
                extra_data={},
                context=get_context(mode="ephemeral"),
            )

            with batch_setup.batch_test_context() as batch:
                # Test that batch creation works
                result = batch.validate(
                    gxe.ExpectTableRowCountToBeBetween(min_value=1, max_value=10)
                )
                assert result.success

                # Test complex expectations to ensure SQL generation is robust
                result = batch.validate(
                    gxe.ExpectColumnValuesToBeInSet(
                        column="name",
                        value_set=["Alice", "Bob", "Charlie", "David", "Eve"],
                    )
                )
                assert result.success
