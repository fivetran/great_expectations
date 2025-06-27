from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Final

import pandas as pd

from great_expectations import ValidationDefinition
from great_expectations.checkpoint import Checkpoint
from great_expectations.core import ExpectationSuite
from great_expectations.expectations import ExpectColumnValuesToNotBeNull
from tests.conftest import parameterize_batch_for_data_sources
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


class TestSnowflake:
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


class TestDatabricks:
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
