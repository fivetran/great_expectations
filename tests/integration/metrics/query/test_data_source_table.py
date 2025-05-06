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

TARGET_DATA_FRAME = pd.DataFrame({"foo": [1, 2, 3], "bar": [4, 5, 6]})

SOURCE_DATA_FRAME = pd.DataFrame(
    {
        "id": [1, 2, 3, 4],
        "name": ["A", "B", "C", "A"],
    },
)

BIG_SOURCE_DATA_FRAME = pd.DataFrame(
    {
        "id": [i for i in range(300)],
        "name": ["A" for _ in range(300)],
    }
)

ALL_SOURCE_TO_TARGET_SOURCES = [
    MultiSourceTestConfig(
        source=PostgreSQLDatasourceTestConfig(), target=PostgreSQLDatasourceTestConfig()
    ),
    MultiSourceTestConfig(
        source=PostgreSQLDatasourceTestConfig(),
        target=SqliteDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        source=SnowflakeDatasourceTestConfig(), target=SnowflakeDatasourceTestConfig()
    ),
    MultiSourceTestConfig(
        source=SnowflakeDatasourceTestConfig(),
        target=SqliteDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        source=DatabricksDatasourceTestConfig(),
        target=DatabricksDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        source=DatabricksDatasourceTestConfig(),
        target=SqliteDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        source=RedshiftDatasourceTestConfig(),
        target=RedshiftDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        source=RedshiftDatasourceTestConfig(),
        target=SqliteDatasourceTestConfig(),
    ),
]


class TestQueryRowCount:
    @multi_source_batch_setup(
        multi_source_test_configs=ALL_SOURCE_TO_TARGET_SOURCES,
        target_data=TARGET_DATA_FRAME,
        source_data=SOURCE_DATA_FRAME,
    )
    def test_success_sql(self, multi_source_batch: MultiSourceBatch) -> None:
        query = f"SELECT * FROM {multi_source_batch.source_table_name} WHERE name = 'A';"
        batch = multi_source_batch.target_batch
        metric = QueryDataSourceTable(
            query=query, data_source_name=multi_source_batch.source_data_source_name
        )
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, QueryDataSourceTableResult)
        assert len(metric_result.value) == 2

    @multi_source_batch_setup(
        multi_source_test_configs=ALL_SOURCE_TO_TARGET_SOURCES,
        target_data=TARGET_DATA_FRAME,
        source_data=BIG_SOURCE_DATA_FRAME,
    )
    def test_result_is_limited_to_200_rows(self, multi_source_batch: MultiSourceBatch) -> None:
        query = f"SELECT * FROM {multi_source_batch.source_table_name} WHERE id > 0"
        batch = multi_source_batch.target_batch
        metric = QueryDataSourceTable(
            query=query, data_source_name=multi_source_batch.source_data_source_name
        )
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, QueryDataSourceTableResult)
        assert len(metric_result.value) == MAX_RESULT_RECORDS
