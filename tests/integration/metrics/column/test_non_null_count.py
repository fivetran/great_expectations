import pandas as pd
import pytest

from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column.aggregate_non_null_count import (
    ColumnAggregateNonNullCount,
    ColumnAggregateNonNullCountResult,
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

ALL_NULL_DATA_FRAME = pd.DataFrame(
    {
        STRING_COLUMN_NAME: [None, None, None],
    },
    dtype="object",
)

NO_NULL_DATA_FRAME = pd.DataFrame(
    {
        STRING_COLUMN_NAME: ["a", "b", "c", "d"],
    },
    dtype="object",
)

# Empty dataframe with explicit schema for Spark compatibility
EMPTY_DATA_FRAME = pd.DataFrame(
    {
        STRING_COLUMN_NAME: pd.Series([], dtype="object"),
    }
)


class TestColumnAggregateNonNullCount:
    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES + PANDAS_DATA_SOURCES + SPARK_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success(self, batch_for_datasource: Batch) -> None:
        metric = ColumnAggregateNonNullCount(column=STRING_COLUMN_NAME)
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnAggregateNonNullCountResult)
        assert metric_result.value == 3

    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES + PANDAS_DATA_SOURCES,
        data=ALL_NULL_DATA_FRAME,
    )
    def test_all_null(self, batch_for_datasource: Batch) -> None:
        metric = ColumnAggregateNonNullCount(column=STRING_COLUMN_NAME)
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnAggregateNonNullCountResult)
        assert metric_result.value == 0

    @parameterize_batch_for_data_sources(
        data_source_configs=SPARK_DATA_SOURCES,
        data=ALL_NULL_DATA_FRAME,
    )
    @pytest.mark.xfail(reason="Spark cannot determine types from all-null dataset", strict=True)
    def test_all_null_spark(self, batch_for_datasource: Batch) -> None:
        metric = ColumnAggregateNonNullCount(column=STRING_COLUMN_NAME)
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnAggregateNonNullCountResult)
        assert metric_result.value == 0

    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES + PANDAS_DATA_SOURCES + SPARK_DATA_SOURCES,
        data=NO_NULL_DATA_FRAME,
    )
    def test_no_null(self, batch_for_datasource: Batch) -> None:
        metric = ColumnAggregateNonNullCount(column=STRING_COLUMN_NAME)
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnAggregateNonNullCountResult)
        assert metric_result.value == 4

    # Simplified empty dataset test - only using Pandas data sources
    @parameterize_batch_for_data_sources(
        data_source_configs=PANDAS_DATA_SOURCES,
        data=EMPTY_DATA_FRAME,
    )
    def test_empty_dataset(self, batch_for_datasource: Batch) -> None:
        """Test the metric with an empty dataset using Pandas data sources."""
        metric = ColumnAggregateNonNullCount(column=STRING_COLUMN_NAME)
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnAggregateNonNullCountResult)
        assert metric_result.value == 0
