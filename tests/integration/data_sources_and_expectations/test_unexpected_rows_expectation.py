from datetime import datetime, timezone
from typing import Sequence
from uuid import uuid4

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    BigQueryDatasourceTestConfig,
    DatabricksDatasourceTestConfig,
    DataSourceTestConfig,
    # MSSQLDatasourceTestConfig,
    MySQLDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
    # SqliteDatasourceTestConfig,
)

# pandas not currently supported by this Expecatation
ALL_SUPPORTED_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    BigQueryDatasourceTestConfig(),
    DatabricksDatasourceTestConfig(),
    # MSSQLDatasourceTestConfig(),  # fix me
    MySQLDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    SparkFilesystemCsvDatasourceTestConfig(),
    # SqliteDatasourceTestConfig(),  # fix me
]

# pandas and spark not currently supporting partitioners
PARTITIONER_SUPPORTED_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    BigQueryDatasourceTestConfig(),
    DatabricksDatasourceTestConfig(),
    # MSSQLDatasourceTestConfig(),  # fix me
    MySQLDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    # SqliteDatasourceTestConfig(),  # fix me
]

DATA = pd.DataFrame(
    {
        "created_at": [
            datetime(year=2024, month=12, day=1, tzinfo=timezone.utc).date(),
            datetime(year=2024, month=11, day=30, tzinfo=timezone.utc).date(),
        ],
        "quantity": [1, 2],
        "temperature": [75, 92],
        "color": ["red", "red"],
    }
)

DATE_COLUMN = "created_at"

SUCCESS_QUERIES = [
    "SELECT * FROM {batch} WHERE quantity > 2",
    "SELECT * FROM {batch} WHERE quantity > 2 AND temperature > 91",
    "SELECT * FROM {batch} WHERE quantity > 2 OR temperature > 92",
    "SELECT * FROM {batch} WHERE quantity > 2 ORDER BY quantity DESC",
    "SELECT color FROM {batch} GROUP BY color HAVING SUM(quantity) > 3",
]

FAILURE_QUERIES = [
    "SELECT * FROM {batch}",
    "SELECT * FROM {batch} WHERE quantity > 0",
    "SELECT * FROM {batch} WHERE quantity > 0 AND temperature > 74",
    "SELECT * FROM {batch} WHERE quantity > 0 OR temperature > 92",
    "SELECT * FROM {batch} WHERE quantity > 0 ORDER BY quantity DESC",
    "SELECT color FROM {batch} GROUP BY color  HAVING SUM(quantity) > 0",
]


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
        description="Expect query with {batch} keyword to succeed",
        unexpected_rows_query=unexpected_rows_query,
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
        description="Expect query with {batch} keyword to fail",
        unexpected_rows_query=unexpected_rows_query,
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
        name=str(uuid4()), column=DATE_COLUMN
    ).get_batch()
    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect query with {batch} keyword and paritioner defined to succeed",
        unexpected_rows_query=unexpected_rows_query,
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
        name=str(uuid4()), column=DATE_COLUMN
    ).get_batch()
    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect query with {batch} keyword and partitioner defined to fail",
        unexpected_rows_query=unexpected_rows_query,
    )
    result = batch.validate(expectation)
    assert result.success is False
    assert result.exception_info.get("raised_exception") is False
