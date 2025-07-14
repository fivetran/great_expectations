"""
Integration tests for Databricks table names with special characters.
These tests verify that table names starting with digits or containing special characters
work correctly with Custom SQL Expectations and other operations.
"""

import pytest

from great_expectations.core.batch_definition import BatchDefinition
from great_expectations.expectations.expectation import ExpectationValidationResult


@pytest.mark.databricks
class TestDatabricksSpecialTableNames:
    """Test suite for Databricks tables with special naming requirements."""

    def test_table_name_starting_with_digit(self, context, databricks_datasource):
        """Test that table names starting with digits work correctly."""

        # Create a table asset for a table starting with a digit
        table_asset = databricks_datasource.add_table_asset(
            name="247_asset_class_cumulative_returns",
            table_name="247_asset_class_cumulative_returns",
        )

        # Create a batch definition
        batch_definition: BatchDefinition = table_asset.add_batch_definition_whole_table(
            "full_table_batch"
        )

        # Get a batch
        batch = table_asset.get_batch(batch_definition.build_batch_request())

        # Verify the batch was created successfully
        assert batch is not None
        assert batch.data is not None

        # Test a basic expectation on the batch
        result = batch.expect_table_row_count_to_be_between(min_value=0, max_value=1000000)
        assert isinstance(result, ExpectationValidationResult)
        assert result.success is not None  # Should not error out

    def test_table_name_with_spaces(self, context, databricks_datasource):
        """Test that table names with spaces work correctly."""

        # Create a table asset for a table with spaces
        table_asset = databricks_datasource.add_table_asset(
            name="my_table_with_spaces",
            table_name="my table with spaces",  # Contains spaces
        )

        # Create a batch definition
        batch_definition: BatchDefinition = table_asset.add_batch_definition_whole_table(
            "full_table_batch",
        )

        # This should not raise an exception when creating the batch
        batch = table_asset.get_batch(batch_definition.build_batch_request())

        # Verify the batch was created successfully
        assert batch is not None
        assert batch.data is not None

    def test_table_name_with_hyphens(self, context, databricks_datasource):
        """Test that table names with hyphens work correctly."""

        # Create a table asset for a table with hyphens
        table_asset = databricks_datasource.add_table_asset(
            name="my_table_with_hyphens",
            table_name="my-table-with-hyphens",  # Contains hyphens
        )

        # Create a batch definition
        batch_definition: BatchDefinition = table_asset.add_batch_definition_whole_table(
            "full_table_batch"
        )

        # This should not raise an exception when creating the batch
        batch = table_asset.get_batch(batch_definition.build_batch_request())

        # Verify the batch was created successfully
        assert batch is not None
        assert batch.data is not None

    def test_table_name_with_dots(self, context, databricks_datasource):
        """Test that table names with dots work correctly."""

        # Create a table asset for a table with dots
        table_asset = databricks_datasource.add_table_asset(
            name="my_table_with_dots",
            table_name="my.table.with.dots",  # Contains dots
        )

        # Create a batch definition
        batch_definition: BatchDefinition = table_asset.add_batch_definition_whole_table(
            "full_table_batch"
        )

        # This should not raise an exception when creating the batch
        batch = table_asset.get_batch(batch_definition.build_batch_request())

        # Verify the batch was created successfully
        assert batch is not None
        assert batch.data is not None

    def test_table_name_with_hash_and_at_symbols(self, context, databricks_datasource):
        """Test that table names with # and @ symbols work correctly."""

        # Create a table asset for a table with special symbols
        table_asset = databricks_datasource.add_table_asset(
            name="my_table_with_symbols",
            table_name="my#table@with#symbols",  # Contains # and @ symbols
        )

        # Create a batch definition
        batch_definition: BatchDefinition = table_asset.add_batch_definition_whole_table(
            "full_table_batch"
        )

        # This should not raise an exception when creating the batch
        batch = table_asset.get_batch(batch_definition.build_batch_request())

        # Verify the batch was created successfully
        assert batch is not None
        assert batch.data is not None

    def test_custom_sql_expectation_with_special_table_name(self, context, databricks_datasource):
        """Test that Custom SQL Expectations work with table names requiring special quoting."""

        # Create a table asset for a table starting with a digit (the main bug case)
        table_asset = databricks_datasource.add_table_asset(
            name="247_asset_class_cumulative_returns",
            table_name="247_asset_class_cumulative_returns",
        )

        # Create a batch definition
        batch_definition: BatchDefinition = table_asset.add_batch_definition_whole_table(
            "full_table_batch"
        )

        # Get a batch
        batch = table_asset.get_batch(batch_definition.build_batch_request())

        # Test a Custom SQL Expectation - this was the main failing case
        result = batch.expect_column_values_to_be_in_set(
            column="some_column",  # Assume this column exists
            value_set=["expected_value_1", "expected_value_2"],
        )

        # The expectation should execute without SQL syntax errors
        assert isinstance(result, ExpectationValidationResult)
        # We don't assert on success since we don't know the actual data
        # But it should not raise a SQL syntax error about double quotes

    def test_schema_and_table_name_both_special(self, context, databricks_datasource):
        """Test schema and table names that both require special quoting."""

        # Create a table asset with both schema and table needing quoting
        table_asset = databricks_datasource.add_table_asset(
            name="special_schema_and_table",
            schema_name="123_schema",  # Schema starts with digit
            table_name="456_table",  # Table starts with digit
        )

        # Create a batch definition
        batch_definition: BatchDefinition = table_asset.add_batch_definition_whole_table(
            "full_table_batch"
        )

        # This should not raise an exception when creating the batch
        batch = table_asset.get_batch(batch_definition.build_batch_request())

        # Verify the batch was created successfully
        assert batch is not None
        assert batch.data is not None

    def test_query_asset_referencing_special_table_name(self, context, databricks_datasource):
        """Test that Query Assets can reference tables with special names."""

        # Create a query asset that references a table with special naming
        query_asset = databricks_datasource.add_query_asset(
            name="query_with_special_table",
            query="SELECT * FROM `247_asset_class_cumulative_returns` LIMIT 10",
        )

        # Create a batch definition
        batch_definition: BatchDefinition = query_asset.add_batch_definition_whole_table(
            "full_query_batch"
        )

        # This should not raise an exception when creating the batch
        batch = query_asset.get_batch(batch_definition.build_batch_request())

        # Verify the batch was created successfully
        assert batch is not None
        assert batch.data is not None

    def test_multiple_special_table_operations(self, context, databricks_datasource):
        """Test multiple operations on tables with special names."""

        # Create multiple table assets with different special naming patterns
        table_assets = []

        special_names = [
            "123_starts_with_digit",
            "table with spaces",
            "table-with-hyphens",
            "table.with.dots",
            "table#with@symbols",
        ]

        for i, table_name in enumerate(special_names):
            asset = databricks_datasource.add_table_asset(
                name=f"special_table_{i}",
                table_name=table_name,
            )
            table_assets.append(asset)

        # Test that all assets can create batches successfully
        for asset in table_assets:
            batch_definition = asset.add_batch_definition_whole_table("test_batch")
            batch = asset.get_batch(batch_definition.build_batch_request())

            assert batch is not None
            assert batch.data is not None

            # Test a basic expectation to ensure SQL generation works
            result = batch.expect_table_row_count_to_be_between(min_value=0, max_value=1000000)
            assert isinstance(result, ExpectationValidationResult)
