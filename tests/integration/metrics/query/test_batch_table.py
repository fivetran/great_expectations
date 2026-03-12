from typing import Sequence

import pandas as pd

from great_expectations.constants import MAX_RESULT_RECORDS
from great_expectations.metrics.query.batch_table import (
    QueryBatchTable,
    QueryBatchTableResult,
)
from tests.integration.conftest import (
    parameterize_batch_for_data_sources,
)
from tests.integration.test_utils.data_source_config import (
    DatabricksDatasourceTestConfig,
    DataSourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)

SQL_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    PostgreSQLDatasourceTestConfig(),
    SqliteDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    DatabricksDatasourceTestConfig(),
]

SPARK_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    SparkFilesystemCsvDatasourceTestConfig(),
]

SMALL_DF = pd.DataFrame({"id": [1, 2, 3], "name": ["A", "B", "C"]})
BIG_DF = pd.DataFrame({"id": list(range(300)), "name": ["X"] * 300})


class TestQueryBatchTable:
    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=SMALL_DF,
    )
    def test_success_sql(self, batch_for_datasource):
        metric = QueryBatchTable(
            query="SELECT * FROM {batch} WHERE name = 'A'",
            fetch_all=False,
        )
        result = batch_for_datasource.compute_metrics(metric)
        assert isinstance(result, QueryBatchTableResult)
        assert len(result.value) == 1

    @parameterize_batch_for_data_sources(
        data_source_configs=SPARK_DATA_SOURCES,
        data=SMALL_DF,
    )
    def test_success_spark(self, batch_for_datasource):
        metric = QueryBatchTable(
            query="SELECT * FROM {batch} WHERE name = 'A'",
            fetch_all=False,
        )
        result = batch_for_datasource.compute_metrics(metric)
        assert isinstance(result, QueryBatchTableResult)
        assert len(result.value) == 1

    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=BIG_DF,
    )
    def test_fetch_all_false_caps_at_200(self, batch_for_datasource):
        metric = QueryBatchTable(
            query="SELECT * FROM {batch} WHERE id > 0",
            fetch_all=False,
        )
        result = batch_for_datasource.compute_metrics(metric)
        assert len(result.value) == MAX_RESULT_RECORDS

    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=BIG_DF,
    )
    def test_fetch_all_true_returns_all_rows_sql(self, batch_for_datasource):
        metric = QueryBatchTable(
            query="SELECT * FROM {batch} WHERE id > 0",
            fetch_all=True,
        )
        result = batch_for_datasource.compute_metrics(metric)
        assert len(result.value) == 299

    @parameterize_batch_for_data_sources(
        data_source_configs=SPARK_DATA_SOURCES,
        data=BIG_DF,
    )
    def test_fetch_all_true_returns_all_rows_spark(self, batch_for_datasource):
        metric = QueryBatchTable(
            query="SELECT * FROM {batch} WHERE id > 0",
            fetch_all=True,
        )
        result = batch_for_datasource.compute_metrics(metric)
        assert len(result.value) == 299
