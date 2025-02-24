from typing import Sequence

import pandas as pd

from great_expectations.metrics.query.row_count import QueryRowCount, QueryRowCountResult
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    BigQueryDatasourceTestConfig,
    DatabricksDatasourceTestConfig,
    DataSourceTestConfig,
    MSSQLDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)

SPARK_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    SparkFilesystemCsvDatasourceTestConfig(),
]

SQL_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    BigQueryDatasourceTestConfig(),
    DatabricksDatasourceTestConfig(),
    MSSQLDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    SqliteDatasourceTestConfig(),
]

DATA_FRAME = pd.DataFrame(
    {
        "id": [1, 2, 3, 4],
        "name": ["A", "B", "C", "D"],
    },
)


class TestQueryRowCount:
    @parameterize_batch_for_data_sources(
        data_source_configs=SPARK_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success_spark(self, batch_for_datasource) -> None:
        batch = batch_for_datasource
        metric = QueryRowCount(
            batch_id=batch.id,
            query="SELECT * FROM {batch} WHERE id > 0",
        )
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, QueryRowCountResult)
        assert metric_result.value == 4

    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success_sql(self, batch_for_datasource) -> None:
        batch = batch_for_datasource
        metric = QueryRowCount(
            batch_id=batch.id,
            query="SELECT * FROM {batch} WHERE id > 0",
        )
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, QueryRowCountResult)
        assert metric_result.value == 4

    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_filtered_query_sql(self, batch_for_datasource) -> None:
        batch = batch_for_datasource
        metric = QueryRowCount(
            batch_id=batch.id,
            query="SELECT * FROM {batch} WHERE id <= 2",
        )
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, QueryRowCountResult)
        assert metric_result.value == 2
