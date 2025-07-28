import pandas as pd

from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.fluent.conftest import (
    TEST_TABLE_NAME,
    _run_checkpoint_test,
    _run_column_expectation_test,
)
from tests.integration.test_utils.data_source_config import DatabricksDatasourceTestConfig


class TestDatabricksTableIdentifiers:
    @parameterize_batch_for_data_sources(
        data_source_configs=[
            DatabricksDatasourceTestConfig(table_name=TEST_TABLE_NAME.lower()),
        ],
        data=pd.DataFrame({"test_column": [1, 2, 3]}),
    )
    def test_unquoted_lower(self, batch_for_datasource):
        """Test Databricks with unquoted lower case table name"""
        _run_checkpoint_test(batch_for_datasource, "databricks")

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            DatabricksDatasourceTestConfig(table_name=f"`{TEST_TABLE_NAME.lower()}`"),
        ],
        data=pd.DataFrame({"test_column": [1, 2, 3]}),
    )
    def test_quoted_lower(self, batch_for_datasource):
        """Test Databricks with quoted lower case table name"""
        _run_checkpoint_test(batch_for_datasource, "databricks")

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            DatabricksDatasourceTestConfig(table_name=TEST_TABLE_NAME.upper()),
        ],
        data=pd.DataFrame({"test_column": [1, 2, 3]}),
    )
    def test_unquoted_upper(self, batch_for_datasource):
        """Test Databricks with unquoted upper case table name"""
        _run_checkpoint_test(batch_for_datasource, "databricks")

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            DatabricksDatasourceTestConfig(table_name=f"`{TEST_TABLE_NAME.upper()}`"),
        ],
        data=pd.DataFrame({"test_column": [1, 2, 3]}),
    )
    def test_quoted_upper(self, batch_for_datasource):
        """Test Databricks with quoted upper case table name"""
        _run_checkpoint_test(batch_for_datasource, "databricks")

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            DatabricksDatasourceTestConfig(table_name=f"`{TEST_TABLE_NAME.title()}`"),
        ],
        data=pd.DataFrame({"test_column": [1, 2, 3]}),
    )
    def test_quoted_mixed(self, batch_for_datasource):
        """Test Databricks with quoted mixed case table name"""
        _run_checkpoint_test(batch_for_datasource, "databricks")

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            DatabricksDatasourceTestConfig(table_name=TEST_TABLE_NAME.title()),
        ],
        data=pd.DataFrame({"test_column": [1, 2, 3]}),
    )
    def test_unquoted_mixed(self, batch_for_datasource):
        """Test Databricks with unquoted mixed case table name"""
        _run_checkpoint_test(batch_for_datasource, "databricks")


class TestDatabricksColumnExpectations:
    """Test column expectations for Databricks datasources"""

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            DatabricksDatasourceTestConfig(table_name=TEST_TABLE_NAME.lower()),
        ],
        data=pd.DataFrame({"unquoted_lower_col": ["test_value"]}),
    )
    def test_unquoted_lower_col(self, batch_for_datasource):
        """Test Databricks column expectation for unquoted_lower_col"""
        _run_column_expectation_test(batch_for_datasource, "databricks", "unquoted_lower_col")

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            DatabricksDatasourceTestConfig(table_name=TEST_TABLE_NAME.lower()),
        ],
        data=pd.DataFrame({"UNQUOTED_UPPER_COL": ["test_value"]}),
    )
    def test_unquoted_upper_col(self, batch_for_datasource):
        """Test Databricks column expectation for unquoted_upper_col"""
        _run_column_expectation_test(batch_for_datasource, "databricks", "UNQUOTED_UPPER_COL")

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            DatabricksDatasourceTestConfig(table_name=TEST_TABLE_NAME.lower()),
        ],
        data=pd.DataFrame({"quoted_lower_col": ["test_value"]}),
    )
    def test_quoted_lower_col(self, batch_for_datasource):
        """Test Databricks column expectation for quoted_lower_col"""
        _run_column_expectation_test(batch_for_datasource, "databricks", "quoted_lower_col")

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            DatabricksDatasourceTestConfig(table_name=TEST_TABLE_NAME.lower()),
        ],
        data=pd.DataFrame({"QUOTED_UPPER_COL": ["test_value"]}),
    )
    def test_quoted_upper_col(self, batch_for_datasource):
        """Test Databricks column expectation for quoted_upper_col"""
        _run_column_expectation_test(batch_for_datasource, "databricks", "QUOTED_UPPER_COL")

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            DatabricksDatasourceTestConfig(table_name=TEST_TABLE_NAME.lower()),
        ],
        data=pd.DataFrame({"quotedMixed": ["test_value"]}),
    )
    def test_quotedmixed(self, batch_for_datasource):
        """Test Databricks column expectation for quotedmixed"""
        _run_column_expectation_test(batch_for_datasource, "databricks", "quotedMixed")

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            DatabricksDatasourceTestConfig(table_name=TEST_TABLE_NAME.lower()),
        ],
        data=pd.DataFrame({"quoted.w.dots": ["test_value"]}),
    )
    def test_quoted_w_dots(self, batch_for_datasource):
        """Test Databricks column expectation for quoted.w.dots"""
        _run_column_expectation_test(batch_for_datasource, "databricks", "quoted.w.dots")

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            DatabricksDatasourceTestConfig(table_name=TEST_TABLE_NAME.lower()),
        ],
        data=pd.DataFrame({"QUOTED.W.DOTS": ["test_value"]}),
    )
    def test_quoted_w_dots_upper(self, batch_for_datasource):
        """Test Databricks column expectation for QUOTED.W.DOTS"""
        _run_column_expectation_test(batch_for_datasource, "databricks", "QUOTED.W.DOTS")
