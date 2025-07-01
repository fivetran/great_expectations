from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Final

import pandas as pd

from great_expectations import ValidationDefinition
from great_expectations.checkpoint import Checkpoint
from great_expectations.core import ExpectationSuite
from great_expectations.expectations import ExpectColumnValuesToNotBeNull
from great_expectations.expectations.expectation_configuration import ExpectationConfiguration
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    DatabricksDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
)

if TYPE_CHECKING:
    from great_expectations.checkpoint.checkpoint import CheckpointResult

TEST_TABLE_NAME: Final[str] = "test_table"


def _run_checkpoint_test(batch_for_datasource, datasource_type: str) -> None:
    """Helper function to run checkpoint validation test"""
    context = batch_for_datasource.datasource.data_context
    expectation_suite = context.suites.add(
        ExpectationSuite(
            name=f"{datasource_type}_es_{uuid.uuid4().hex}",
            expectations=[ExpectColumnValuesToNotBeNull(column="test_column", mostly=1)],
        )
    )
    validation_definition = context.validation_definitions.add(
        ValidationDefinition(
            name=f"{datasource_type}_val_def_{uuid.uuid4().hex}",
            data=batch_for_datasource.data_asset.batch_definitions[0],
            suite=expectation_suite,
        )
    )
    checkpoint = context.checkpoints.add(
        Checkpoint(
            name=f"{datasource_type.title()} Test Checkpoint {uuid.uuid4().hex}",
            validation_definitions=[validation_definition],
        )
    )
    checkpoint_result: CheckpointResult = checkpoint.run()
    assert checkpoint_result.success


def _run_column_expectation_test(
    batch_for_datasource, datasource_type: str, column_name: str
) -> None:
    """Helper function to run column expectation validation test"""
    context = batch_for_datasource.datasource.data_context
    expectation_suite = context.suites.add(
        ExpectationSuite(
            name=f"{datasource_type}_column_es_{uuid.uuid4().hex}",
        )
    )
    expectation_suite.add_expectation_configuration(
        expectation_configuration=ExpectationConfiguration(
            type="expect_column_values_to_match_regex",
            kwargs={"column": column_name, "regex": r".*"},
        )
    )
    expectation_suite.save()
    validation_definition = context.validation_definitions.add(
        ValidationDefinition(
            name=f"{datasource_type}_column_val_def_{uuid.uuid4().hex}",
            data=batch_for_datasource.data_asset.batch_definitions[0],
            suite=expectation_suite,
        )
    )
    checkpoint = context.checkpoints.add(
        Checkpoint(
            name=f"{datasource_type.title()} Column Test Checkpoint {uuid.uuid4().hex}",
            validation_definitions=[validation_definition],
        )
    )
    checkpoint_result: CheckpointResult = checkpoint.run()
    assert checkpoint_result.success


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
