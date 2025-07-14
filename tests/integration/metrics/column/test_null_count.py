import pandas as pd
import pytest

from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column.null_count import (
    ColumnNullCount,
    ColumnNullCountResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import (
    PANDAS_DATA_SOURCES,
    SPARK_DATA_SOURCES,
    SQL_DATA_SOURCES,
)

STRING_COLUMN_NAME = "whatevs"
DATA_FRAME = pd.DataFrame(
    {
        STRING_COLUMN_NAME: ["a", None, "c", "d", None],
    },
    dtype="object",
)


class TestColumnNullCount:
    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES + PANDAS_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success(self, batch_for_datasource: Batch) -> None:
        metric = ColumnNullCount(column=STRING_COLUMN_NAME)
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnNullCountResult)
        assert metric_result.value == 2

    @parameterize_batch_for_data_sources(
        data_source_configs=SPARK_DATA_SOURCES,
        data=DATA_FRAME,
    )
    @pytest.mark.xfail(strict=True)
    def test_spark(self, batch_for_datasource: Batch) -> None:
        metric = ColumnNullCount(column=STRING_COLUMN_NAME)
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnNullCountResult)
        assert metric_result.value == 2
