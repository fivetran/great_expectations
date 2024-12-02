from typing import Sequence

import pandas as pd

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
def test_unexpected_rows_expectation_batch_keyword_success(batch_for_datasource) -> None:
    unexpected_rows_query = "SELECT * FROM {batch} WHERE a > 2"
    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect a to be less than 3", unexpected_rows_query=unexpected_rows_query
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=pd.DataFrame({"a": [1, 2]}),
)
def test_unexpected_rows_expectation_batch_keyword_failure(batch_for_datasource) -> None:
    unexpected_rows_query = "SELECT * FROM {batch}"
    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect table to be empty", unexpected_rows_query=unexpected_rows_query
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success is False
    assert result.exception_info.get("raised_exception") is False
