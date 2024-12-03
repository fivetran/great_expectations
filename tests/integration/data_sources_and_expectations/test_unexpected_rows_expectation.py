from datetime import datetime, timezone
from typing import Sequence

import pandas as pd

import great_expectations.expectations as gxe
from great_expectations.core.batch_definition import BatchDefinition
from great_expectations.core.partitioners import ColumnPartitionerMonthly
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    BigQueryDatasourceTestConfig,
    DatabricksDatasourceTestConfig,
    DataSourceTestConfig,
    MSSQLDatasourceTestConfig,
    MySQLDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)

ALL_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    BigQueryDatasourceTestConfig(),
    DatabricksDatasourceTestConfig(),
    MSSQLDatasourceTestConfig(),
    MySQLDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    SparkFilesystemCsvDatasourceTestConfig(),
    SqliteDatasourceTestConfig(),
]


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=pd.DataFrame({"a": [1, 2]}),
)
def test_unexpected_rows_expectation_batch_keyword_whole_table_success(
    batch_for_datasource,
) -> None:
    unexpected_rows_query = "SELECT * FROM {batch} WHERE a > 2"
    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect a to be less than 3", unexpected_rows_query=unexpected_rows_query
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success
    assert result.exception_info.get("raised_exception") is False


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=pd.DataFrame({"a": [1, 2]}),
)
def test_unexpected_rows_expectation_batch_keyword_whole_table_failure(
    batch_for_datasource,
) -> None:
    unexpected_rows_query = "SELECT * FROM {batch}"
    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect table to be empty", unexpected_rows_query=unexpected_rows_query
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success is False
    assert result.exception_info.get("raised_exception") is False


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=pd.DataFrame(
        {
            "created_at": [
                datetime(year=2024, month=12, day=1, tzinfo=timezone.utc),
                datetime(year=2024, month=11, day=31, tzinfo=timezone.utc),
            ],
            "a": [1, 2],
        }
    ),
    batch_definition=BatchDefinition(
        name="MONTHLY",
        partitioner=ColumnPartitionerMonthly(
            method_name="partition_on_year_and_month",
            column_name="created_at",
        ),
    ),
)
def test_unexpected_rows_expectation_batch_keyword_monthly_success(batch_for_datasource) -> None:
    unexpected_rows_query = "SELECT * FROM {batch} WHERE a > 2"
    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect a to be less than 3", unexpected_rows_query=unexpected_rows_query
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success
    assert result.exception_info.get("raised_exception") is False


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=pd.DataFrame(
        {
            "created_at": [
                datetime(year=2024, month=12, day=1, tzinfo=timezone.utc),
                datetime(year=2024, month=11, day=31, tzinfo=timezone.utc),
            ],
            "a": [1, 2],
        }
    ),
    batch_definition=BatchDefinition(
        name="MONTHLY",
        partitioner=ColumnPartitionerMonthly(
            method_name="partition_on_year_and_month",
            column_name="created_at",
        ),
    ),
)
def test_unexpected_rows_expectation_batch_keyword_monthly_failure(batch_for_datasource) -> None:
    unexpected_rows_query = "SELECT * FROM {batch}"
    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect table to be empty", unexpected_rows_query=unexpected_rows_query
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success is False
    assert result.exception_info.get("raised_exception") is False
