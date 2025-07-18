"""
Unit tests for DatabricksTableAsset methods.
These tests verify the logic for handling special table names that require backticks.
"""

import pytest
from sqlalchemy.sql.elements import quoted_name

from great_expectations.datasource.fluent.databricks_sql_datasource import DatabricksTableAsset


@pytest.mark.unit
class TestDatabricksTableAssetMethods:
    """Unit tests for DatabricksTableAsset static methods."""

    def test_needs_databricks_backticks_digit_start(self):
        """Test that table names starting with digits require backticks."""
        assert DatabricksTableAsset._needs_databricks_backticks("123_test_table")
        assert DatabricksTableAsset._needs_databricks_backticks("9_column_table")

    def test_needs_databricks_backticks_special_chars(self):
        """Test that table names with special characters require backticks."""
        assert DatabricksTableAsset._needs_databricks_backticks("table with spaces")
        assert DatabricksTableAsset._needs_databricks_backticks("table-with-hyphens")
        assert DatabricksTableAsset._needs_databricks_backticks("table.with.dots")
        assert DatabricksTableAsset._needs_databricks_backticks("table#with#hash")
        assert DatabricksTableAsset._needs_databricks_backticks("table@with@at")

    def test_needs_databricks_backticks_normal_names(self):
        """Test that normal table names don't require backticks."""
        assert not DatabricksTableAsset._needs_databricks_backticks("normal_table")
        assert not DatabricksTableAsset._needs_databricks_backticks("table_name")
        assert not DatabricksTableAsset._needs_databricks_backticks("TableName")
        assert not DatabricksTableAsset._needs_databricks_backticks("test_table_123")

    def test_needs_databricks_backticks_already_quoted(self):
        """Test that already quoted names don't require additional backticks."""
        assert not DatabricksTableAsset._needs_databricks_backticks("`247_asset_class_returns`")
        assert not DatabricksTableAsset._needs_databricks_backticks("`table with spaces`")

    def test_is_bracketed_by_quotes_true(self):
        """Test that names with backticks are detected correctly."""
        assert DatabricksTableAsset._is_bracketed_by_quotes("`table_name`")
        assert DatabricksTableAsset._is_bracketed_by_quotes("`247_test_table`")
        assert DatabricksTableAsset._is_bracketed_by_quotes("`table with spaces`")

    def test_is_bracketed_by_quotes_false(self):
        """Test that names without backticks are detected correctly."""
        assert not DatabricksTableAsset._is_bracketed_by_quotes("table_name")
        assert not DatabricksTableAsset._is_bracketed_by_quotes("247_test_table")
        assert not DatabricksTableAsset._is_bracketed_by_quotes('"table_name"')
        assert not DatabricksTableAsset._is_bracketed_by_quotes("'table_name'")

    def test_resolve_quoted_name_digit_start(self):
        """Test that table names starting with digits get quoted_name objects."""
        result = DatabricksTableAsset._resolve_quoted_name("247_asset_class_returns")
        assert isinstance(result, quoted_name)
        assert str(result) == "247_asset_class_returns"

    def test_resolve_quoted_name_special_chars(self):
        """Test that table names with special chars get quoted_name objects."""
        result = DatabricksTableAsset._resolve_quoted_name("table with spaces")
        assert isinstance(result, quoted_name)
        assert str(result) == "table with spaces"

        result = DatabricksTableAsset._resolve_quoted_name("table-with-hyphens")
        assert isinstance(result, quoted_name)
        assert str(result) == "table-with-hyphens"

    def test_resolve_quoted_name_normal_names(self):
        """Test that normal table names remain as strings."""
        result = DatabricksTableAsset._resolve_quoted_name("normal_table")
        assert isinstance(result, str)
        assert result == "normal_table"

    def test_resolve_quoted_name_already_quoted(self):
        """Test that already quoted names get their quotes stripped and become
        quoted_name objects."""
        result = DatabricksTableAsset._resolve_quoted_name("`247_asset_class_returns`")
        assert isinstance(result, quoted_name)
        assert str(result) == "247_asset_class_returns"

    def test_resolve_quoted_schema_name_digit_start(self):
        """Test that schema names starting with digits get quoted_name objects."""
        result = DatabricksTableAsset._resolve_quoted_schema_name("123_schema")
        assert isinstance(result, quoted_name)
        assert str(result) == "123_schema"

    def test_resolve_quoted_schema_name_special_chars(self):
        """Test that schema names with special chars get quoted_name objects."""
        result = DatabricksTableAsset._resolve_quoted_schema_name("schema with spaces")
        assert isinstance(result, quoted_name)
        assert str(result) == "schema with spaces"

    def test_resolve_quoted_schema_name_normal_names(self):
        """Test that normal schema names remain as strings."""
        result = DatabricksTableAsset._resolve_quoted_schema_name("normal_schema")
        assert isinstance(result, str)
        assert result == "normal_schema"

    def test_resolve_quoted_schema_name_none(self):
        """Test that None schema names remain None."""
        result = DatabricksTableAsset._resolve_quoted_schema_name(None)
        assert result is None
