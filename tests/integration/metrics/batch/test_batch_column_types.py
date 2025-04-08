import pandas as pd
from numpy import dtype

from great_expectations.compatibility import bigquery, pyspark, snowflake, sqlalchemy
from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.batch.batch_column_types import (
    BatchColumnTypes,
    BatchColumnTypesResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config.postgres import PostgreSQLDatasourceTestConfig
from tests.metrics.conftest import (
    PANDAS_DATA_SOURCES,
    SPARK_DATA_SOURCES,
    BigQueryDatasourceTestConfig,
    DatabricksDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SqliteDatasourceTestConfig,
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
    data_source_configs=[BigQueryDatasourceTestConfig()],
    data=DATA_FRAME,
)
def test_bigquery_success(batch_for_datasource: Batch) -> None:
    batch = batch_for_datasource
    metric = BatchColumnTypes()
    metric_result = batch.compute_metrics(metric)
    assert isinstance(metric_result, BatchColumnTypesResult)
    assert metric_result.value == [
        {"name": "numbers", "type": bigquery.BIGQUERY_TYPES.INTEGER()},
        {"name": "strings", "type": bigquery.BIGQUERY_TYPES.STRING()},
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
    data_source_configs=[SnowflakeDatasourceTestConfig()],
    data=DATA_FRAME,
)
def test_snowflake_success(batch_for_datasource: Batch) -> None:
    batch = batch_for_datasource
    metric = BatchColumnTypes()
    metric_result = batch.compute_metrics(metric)
    assert isinstance(metric_result, BatchColumnTypesResult)
    assert metric_result.value == [
        {"name": "numbers", "type": snowflake.DEC()},
        {"name": "strings", "type": snowflake.TEXT()},
    ]


@parameterize_batch_for_data_sources(
    data_source_configs=[SqliteDatasourceTestConfig()],
    data=DATA_FRAME,
)
def test_sqlite_success(batch_for_datasource: Batch) -> None:
    batch = batch_for_datasource
    metric = BatchColumnTypes()
    metric_result = batch.compute_metrics(metric)
    assert isinstance(metric_result, BatchColumnTypesResult)
    assert metric_result.value == [
        {"name": "numbers", "type": sqlalchemy.sqltypes.INTEGER()},
        {"name": "strings", "type": sqlalchemy.sqlalchemy.VARCHAR()},
    ]
