import pandas as pd

from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.fluent.conftest import (
    TEST_TABLE_NAME,
    _run_checkpoint_test,
    _run_column_expectation_test,
)
from tests.integration.test_utils.data_source_config import SnowflakeDatasourceTestConfig


class TestSnowflakeTableIdentifiers:
    @parameterize_batch_for_data_sources(
        data_source_configs=[
            SnowflakeDatasourceTestConfig(table_name=TEST_TABLE_NAME.lower()),
        ],
        data=pd.DataFrame({"test_column": [1, 2, 3]}),
    )
    def test_lower(self, batch_for_datasource):
        """Test Snowflake with lower case table name"""
        _run_checkpoint_test(batch_for_datasource, "snowflake")

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            SnowflakeDatasourceTestConfig(table_name=f'"{TEST_TABLE_NAME.lower()}"'),
        ],
        data=pd.DataFrame({"test_column": [1, 2, 3]}),
    )
    def test_quoted_lower(self, batch_for_datasource):
        """Test Snowflake with quoted lower case table name"""
        _run_checkpoint_test(batch_for_datasource, "snowflake")

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            SnowflakeDatasourceTestConfig(table_name=TEST_TABLE_NAME.upper()),
        ],
        data=pd.DataFrame({"test_column": [1, 2, 3]}),
    )
    def test_upper(self, batch_for_datasource):
        """Test Snowflake with upper case table name"""
        _run_checkpoint_test(batch_for_datasource, "snowflake")

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            SnowflakeDatasourceTestConfig(table_name=f'"{TEST_TABLE_NAME.upper()}"'),
        ],
        data=pd.DataFrame({"test_column": [1, 2, 3]}),
    )
    def test_quoted_upper(self, batch_for_datasource):
        """Test Snowflake with quoted upper case table name"""
        _run_checkpoint_test(batch_for_datasource, "snowflake")

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            SnowflakeDatasourceTestConfig(table_name=f'"{TEST_TABLE_NAME.title()}"'),
        ],
        data=pd.DataFrame({"test_column": [1, 2, 3]}),
    )
    def test_quoted_title(self, batch_for_datasource):
        """Test Snowflake with quoted title case table name"""
        _run_checkpoint_test(batch_for_datasource, "snowflake")


class TestSnowflakeColumnExpectations:
    """Test column expectations for Snowflake datasources"""

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            SnowflakeDatasourceTestConfig(table_name=TEST_TABLE_NAME.lower()),
        ],
        data=pd.DataFrame({"unquoted_lower_col": ["test_value"]}),
    )
    def test_unquoted_lower_col(self, batch_for_datasource):
        """Test Snowflake column expectation for unquoted_lower_col"""
        _run_column_expectation_test(batch_for_datasource, "snowflake", "unquoted_lower_col")

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            SnowflakeDatasourceTestConfig(table_name=TEST_TABLE_NAME.lower()),
        ],
        data=pd.DataFrame({"UNQUOTED_UPPER_COL": ["test_value"]}),
    )
    def test_unquoted_upper_col(self, batch_for_datasource):
        """Test Snowflake column expectation for unquoted_upper_col"""
        _run_column_expectation_test(batch_for_datasource, "snowflake", "unquoted_upper_col")

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            SnowflakeDatasourceTestConfig(table_name=TEST_TABLE_NAME.lower()),
        ],
        data=pd.DataFrame({'"quoted_lower_col"': ["test_value"]}),
    )
    def test_quoted_lower_col(self, batch_for_datasource):
        """Test Snowflake column expectation for quoted_lower_col"""
        _run_column_expectation_test(batch_for_datasource, "snowflake", '"quoted_lower_col"')

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            SnowflakeDatasourceTestConfig(table_name=TEST_TABLE_NAME.lower()),
        ],
        data=pd.DataFrame({'"QUOTED_UPPER_COL"': ["test_value"]}),
    )
    def test_quoted_upper_col(self, batch_for_datasource):
        """Test Snowflake column expectation for quoted_upper_col"""
        _run_column_expectation_test(batch_for_datasource, "snowflake", '"QUOTED_UPPER_COL"')

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            SnowflakeDatasourceTestConfig(table_name=TEST_TABLE_NAME.lower()),
        ],
        data=pd.DataFrame({'"quotedMixed"': ["test_value"]}),
    )
    def test_quotedmixed(self, batch_for_datasource):
        """Test Snowflake column expectation for quotedMixed"""
        _run_column_expectation_test(batch_for_datasource, "snowflake", '"quotedMixed"')

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            SnowflakeDatasourceTestConfig(table_name=TEST_TABLE_NAME.lower()),
        ],
        data=pd.DataFrame({'"quoted.w.dots"': ["test_value"]}),
    )
    def test_quoted_w_dots(self, batch_for_datasource):
        """Test Snowflake column expectation for quoted.w.dots"""
        _run_column_expectation_test(batch_for_datasource, "snowflake", '"quoted.w.dots"')
