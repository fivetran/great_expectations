from unittest.mock import ANY

import pandas as pd
from numpy import dtype

from great_expectations.compatibility import pyspark
from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.batch.batch_column_types import (
    BatchColumnTypes,
    BatchColumnTypesResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config.databricks import (
    DatabricksDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.postgres import PostgreSQLDatasourceTestConfig
from tests.integration.test_utils.data_source_config.snowflake import SnowflakeDatasourceTestConfig
from tests.metrics.conftest import (
    PANDAS_DATA_SOURCES,
    SPARK_DATA_SOURCES,
    SQL_DATA_SOURCES,
)

DATA_FRAME = pd.DataFrame(
    {
        "numbers": [1, 2, 3],
        "strings": ["one", "two", "three"],
    },
)


@parameterize_batch_for_data_sources(
    data_source_configs=PANDAS_DATA_SOURCES,
    data=DATA_FRAME,
)
def test_pandas_success(batch_for_datasource: Batch) -> None:
    batch = batch_for_datasource
    metric = BatchColumnTypes()
    metric_result = batch.compute_metrics(metric)
    assert isinstance(metric_result, BatchColumnTypesResult)
    assert metric_result.value == [
        {"name": "numbers", "type": dtype("int64")},
        {"name": "strings", "type": dtype("O")},
    ]


@parameterize_batch_for_data_sources(
    data_source_configs=SPARK_DATA_SOURCES,
    data=DATA_FRAME,
)
def test_spark_success(batch_for_datasource: Batch) -> None:
    batch = batch_for_datasource
    metric = BatchColumnTypes()
    metric_result = batch.compute_metrics(metric)
    assert isinstance(metric_result, BatchColumnTypesResult)
    assert metric_result.value == [
        {"name": "numbers", "type": pyspark.types.IntegerType()},
        {"name": "strings", "type": pyspark.types.StringType()},
    ]


@parameterize_batch_for_data_sources(
    data_source_configs=[PostgreSQLDatasourceTestConfig()],
    data=DATA_FRAME,
)
def test_postgres_success(batch_for_datasource: Batch) -> None:
    batch = batch_for_datasource
    metric = BatchColumnTypes()
    metric_result = batch.compute_metrics(metric)
    assert isinstance(metric_result, BatchColumnTypesResult)
    assert metric_result.value == [
        {"name": "numbers", "type": "INTEGER"},
        {"name": "strings", "type": "VARCHAR"},
    ]


@parameterize_batch_for_data_sources(
    data_source_configs=[DatabricksDatasourceTestConfig()],
    data=DATA_FRAME,
)
def test_databricks_success(batch_for_datasource: Batch) -> None:
    batch = batch_for_datasource
    metric = BatchColumnTypes()
    metric_result = batch.compute_metrics(metric)
    assert isinstance(metric_result, BatchColumnTypesResult)
    assert metric_result.value == [
        {"name": "numbers", "type": "INT"},
        {"name": "strings", "type": "STRING"},
    ]


@parameterize_batch_for_data_sources(
    data_source_configs=[SnowflakeDatasourceTestConfig()],
    data=DATA_FRAME,
)
def test_snowflake_success(batch_for_datasource: Batch) -> None:
    batch = batch_for_datasource
    metric = BatchColumnTypes()
    metric_result = batch.compute_metrics(metric)
    assert isinstance(metric_result, BatchColumnTypesResult)
    assert metric_result.value == [
        {"name": "numbers", "type": "DECIMAL(38, 0)"},
        {"name": "strings", "type": "VARCHAR(16777216)"},
    ]


@parameterize_batch_for_data_sources(
    data_source_configs=SQL_DATA_SOURCES,
    data=DATA_FRAME,
)
def test_sql_happy_path(batch_for_datasource: Batch) -> None:
    """General happy path for other SQL dialects.

    The above Postgres test validates exact types come back for sqlalchemy datasources.
    This test uses ANY to account for different SQL dialects returning different type names
    and case-insensitive string comparisons that are now used for PostgreSQL, Databricks,
    and Snowflake dialects.
    """

    batch = batch_for_datasource
    metric = BatchColumnTypes()
    metric_result = batch.compute_metrics(metric)
    assert isinstance(metric_result, BatchColumnTypesResult)
    assert metric_result.value == [
        {"name": "numbers", "type": ANY},
        {"name": "strings", "type": ANY},
    ]
