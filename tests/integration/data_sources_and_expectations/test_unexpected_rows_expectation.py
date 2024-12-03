from datetime import datetime, timezone
from typing import Sequence

import pandas as pd
import pytest

import great_expectations.expectations as gxe
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

# currently excludes pandas
ALL_SUPPORTED_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    BigQueryDatasourceTestConfig(),
    DatabricksDatasourceTestConfig(),
    MSSQLDatasourceTestConfig(),
    MySQLDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    SparkFilesystemCsvDatasourceTestConfig(),
    SqliteDatasourceTestConfig(),
]

# currently excludes pandas and spark
PARTITIONER_SUPPORTED_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    BigQueryDatasourceTestConfig(),
    DatabricksDatasourceTestConfig(),
    MSSQLDatasourceTestConfig(),
    MySQLDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    SqliteDatasourceTestConfig(),
]

DATA = pd.DataFrame(
    {
        "created_at": [
            datetime(year=2024, month=12, day=1, tzinfo=timezone.utc).date(),
            datetime(year=2024, month=11, day=30, tzinfo=timezone.utc).date(),
        ],
        "a": [1, 2],
    }
)

DATE_COLUMN = "created_at"

SUCCESS_QUERIES = ["SELECT * FROM {batch} WHERE a > 2"]

FAILURE_QUERIES = ["SELECT * FROM {batch}"]


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=DATA,
)
@pytest.mark.parametrize("unexpected_rows_query", SUCCESS_QUERIES)
def test_unexpected_rows_expectation_batch_keyword_success(
    batch_for_datasource,
    unexpected_rows_query,
) -> None:
    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect a to be less than 3", unexpected_rows_query=unexpected_rows_query
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success
    assert result.exception_info.get("raised_exception") is False


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=DATA,
)
@pytest.mark.parametrize("unexpected_rows_query", FAILURE_QUERIES)
def test_unexpected_rows_expectation_batch_keyword_failure(
    batch_for_datasource,
    unexpected_rows_query,
) -> None:
    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect table to be empty", unexpected_rows_query=unexpected_rows_query
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success is False
    assert result.exception_info.get("raised_exception") is False


@parameterize_batch_for_data_sources(
    data_source_configs=PARTITIONER_SUPPORTED_DATA_SOURCES,
    data=DATA,
)
@pytest.mark.parametrize("unexpected_rows_query", SUCCESS_QUERIES)
def test_unexpected_rows_expectation_batch_keyword_partitioner_success(
    asset_for_datasource,
    unexpected_rows_query,
) -> None:
    batch = asset_for_datasource.add_batch_definition_monthly(
        name="monthly success", column=DATE_COLUMN
    ).get_batch()
    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect a to be less than 3", unexpected_rows_query=unexpected_rows_query
    )
    result = batch.validate(expectation)
    assert result.success
    assert result.exception_info.get("raised_exception") is False


@parameterize_batch_for_data_sources(
    data_source_configs=PARTITIONER_SUPPORTED_DATA_SOURCES,
    data=DATA,
)
@pytest.mark.parametrize("unexpected_rows_query", FAILURE_QUERIES)
def test_unexpected_rows_expectation_batch_keyword_partitioner_failure(
    asset_for_datasource,
    unexpected_rows_query,
) -> None:
    batch = asset_for_datasource.add_batch_definition_monthly(
        name="monthly failure", column=DATE_COLUMN
    ).get_batch()
    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect table to be empty", unexpected_rows_query=unexpected_rows_query
    )
    result = batch.validate(expectation)
    assert result.success is False
    assert result.exception_info.get("raised_exception") is False
