import pandas as pd

from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column.column_distinct_values_count import (
    ColumnDistinctValuesCount,
    ColumnDistinctValuesCountResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import ALL_DATA_SOURCES, SparkFilesystemCsvDatasourceTestConfig

COLUMN_NAME = "whatevs"
NULL_COLUMN_NAME = "nulls"
DATA_FRAME = pd.DataFrame(
    {
        COLUMN_NAME: ["a", "b", "c", "c", "c", "c", "c", "c", "c", "c"],
        NULL_COLUMN_NAME: [None, None, None, None, None, None, None, None, None, None],
    },
)

try:
    from great_expectations.compatibility.pyspark import types as PYSPARK_TYPES

    SPARK_COLUMN_TYPES = {
        COLUMN_NAME: PYSPARK_TYPES.StringType,
        NULL_COLUMN_NAME: PYSPARK_TYPES.StringType,
    }
except ModuleNotFoundError:
    SPARK_COLUMN_TYPES = {}


ALL_DATA_SOURCES_EXCEPT_SPARK = [
    datasource
    for datasource in ALL_DATA_SOURCES
    if not isinstance(datasource, SparkFilesystemCsvDatasourceTestConfig)
]


class TestColumnNullCount:
    @parameterize_batch_for_data_sources(
        data_source_configs=[
            *ALL_DATA_SOURCES_EXCEPT_SPARK,
            SparkFilesystemCsvDatasourceTestConfig(column_types=SPARK_COLUMN_TYPES),
        ],
        data=DATA_FRAME,
    )
    def test_strings(self, batch_for_datasource: Batch) -> None:
        metric = ColumnDistinctValuesCount(column=COLUMN_NAME)
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesCountResult)
        assert metric_result.value == 3

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_all_nulls(self, batch_for_datasource: Batch) -> None:
        metric = ColumnDistinctValuesCount(column=NULL_COLUMN_NAME)
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesCountResult)
        assert metric_result.value == 0
