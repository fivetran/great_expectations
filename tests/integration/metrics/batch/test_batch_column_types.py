import pandas as pd
from numpy import dtype

from great_expectations.compatibility import pyspark
from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.batch.batch_column_types import (
    BatchColumnTypes,
    BatchColumnTypesResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import PANDAS_DATA_SOURCES, SPARK_DATA_SOURCES, SQL_DATA_SOURCES

DATA_FRAME = pd.DataFrame(
    {
        "numbers": [1, 2, 3],
        "strings": ["one", "two", "three"],
    },
)


class TestBatchColumnTypes__Pandas:
    @parameterize_batch_for_data_sources(
        data_source_configs=PANDAS_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success(self, batch_for_datasource: Batch) -> None:
        batch = batch_for_datasource
        metric = BatchColumnTypes()
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, BatchColumnTypesResult)
        assert metric_result.value == [
            {"name": "numbers", "type": dtype("int64")},
            {"name": "strings", "type": dtype("O")},
        ]


class TestBatchColumnTypes__Spark:
    @parameterize_batch_for_data_sources(
        data_source_configs=SPARK_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success(self, batch_for_datasource: Batch) -> None:
        batch = batch_for_datasource
        metric = BatchColumnTypes()
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, BatchColumnTypesResult)
        assert metric_result.value == [
            {"name": "numbers", "type": pyspark.types.IntegerType()},
            {"name": "strings", "type": pyspark.types.StringType()},
        ]


class TestBatchColumnTypes__Sql:
    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success(self, batch_for_datasource: Batch) -> None:
        batch = batch_for_datasource
        metric = BatchColumnTypes()
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, BatchColumnTypesResult)
        assert metric_result.value == [
            {"name": "numbers", "type": dtype("int64")},
            {"name": "strings", "type": dtype("O")},
        ]
