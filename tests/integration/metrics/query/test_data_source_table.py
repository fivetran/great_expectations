from typing import Sequence

import pandas as pd

from great_expectations.expectations.metrics.util import MAX_RESULT_RECORDS
from great_expectations.metrics import QueryDataSourceTable
from great_expectations.metrics.query.data_source_table import QueryDataSourceTableResult
from tests.integration.conftest import (
    MultiSourceBatch,
    MultiSourceTestConfig,
    multi_source_batch_setup,
)
from tests.integration.test_utils.data_source_config import (
    DatabricksDatasourceTestConfig,
    DataSourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    RedshiftDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)

SPARK_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    SparkFilesystemCsvDatasourceTestConfig(),
]

BASE_DATA_FRAME = pd.DataFrame({"foo": [1, 2, 3], "bar": [4, 5, 6]})

COMPARISON_DATA_FRAME = pd.DataFrame(
    {
        "id": [1, 2, 3, 4],
        "name": ["A", "B", "C", "A"],
    },
)

BIG_COMPARISON_DATA_FRAME = pd.DataFrame(
    {
        "id": [i for i in range(300)],
        "name": ["A" for _ in range(300)],
    }
)

ALL_COMPARISON_TO_BASE_SOURCES = [
    MultiSourceTestConfig(
        comparison=PostgreSQLDatasourceTestConfig(), base=PostgreSQLDatasourceTestConfig()
    ),
    MultiSourceTestConfig(
        comparison=PostgreSQLDatasourceTestConfig(),
        base=SqliteDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        comparison=SnowflakeDatasourceTestConfig(), base=SnowflakeDatasourceTestConfig()
    ),
    MultiSourceTestConfig(
        comparison=SnowflakeDatasourceTestConfig(),
        base=SqliteDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        comparison=DatabricksDatasourceTestConfig(),
        base=DatabricksDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        comparison=DatabricksDatasourceTestConfig(),
        base=SqliteDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        comparison=RedshiftDatasourceTestConfig(),
        base=RedshiftDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        comparison=RedshiftDatasourceTestConfig(),
        base=SqliteDatasourceTestConfig(),
    ),
]


class TestQueryRowCount:
    @multi_source_batch_setup(
        multi_source_test_configs=ALL_COMPARISON_TO_BASE_SOURCES,
        base_data=BASE_DATA_FRAME,
        comparison_data=COMPARISON_DATA_FRAME,
    )
    def test_success_sql(self, multi_source_batch: MultiSourceBatch) -> None:
        query = f"SELECT * FROM {multi_source_batch.comparison_table_name} WHERE name = 'A';"
        batch = multi_source_batch.base_batch
        metric = QueryDataSourceTable(
            query=query, data_source_name=multi_source_batch.comparison_data_source_name
        )
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, QueryDataSourceTableResult)
        assert len(metric_result.value) == 2

    @multi_source_batch_setup(
        multi_source_test_configs=ALL_COMPARISON_TO_BASE_SOURCES,
        base_data=BASE_DATA_FRAME,
        comparison_data=BIG_COMPARISON_DATA_FRAME,
    )
    def test_result_is_limited_to_200_rows(self, multi_source_batch: MultiSourceBatch) -> None:
        query = f"SELECT * FROM {multi_source_batch.comparison_table_name} WHERE id > 0"
        batch = multi_source_batch.base_batch
        metric = QueryDataSourceTable(
            query=query, data_source_name=multi_source_batch.comparison_data_source_name
        )
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, QueryDataSourceTableResult)
        assert len(metric_result.value) == MAX_RESULT_RECORDS
