import pandas as pd

from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column.distinct_values_not_in_set_count import (
    ColumnDistinctValuesNotInSetCount,
    ColumnDistinctValuesNotInSetCountResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import ALL_DATA_SOURCES

COLUMN_NAME = "my_col"
DATA_FRAME = pd.DataFrame(
    {
        COLUMN_NAME: ["a", "b", "c", "c", "c", None, None],
    },
)


class TestColumnDistinctValuesNotInSetCount:
    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_all_values_in_set(self, batch_for_datasource: Batch) -> None:
        """When all column values are in the set, count should be 0."""
        metric = ColumnDistinctValuesNotInSetCount(column=COLUMN_NAME, value_set=["a", "b", "c"])
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesNotInSetCountResult)
        assert metric_result.value == 0

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_some_values_not_in_set(self, batch_for_datasource: Batch) -> None:
        """When some column values are not in the set, count should reflect that."""
        metric = ColumnDistinctValuesNotInSetCount(
            column=COLUMN_NAME,
            value_set=["a", "b"],  # missing "c"
        )
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesNotInSetCountResult)
        assert metric_result.value == 1  # "c" is not in set

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_no_values_in_set(self, batch_for_datasource: Batch) -> None:
        """When no column values are in the set, count all distinct values."""
        metric = ColumnDistinctValuesNotInSetCount(column=COLUMN_NAME, value_set=["x", "y", "z"])
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesNotInSetCountResult)
        assert metric_result.value == 3  # all of a, b, c are not in set

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_empty_value_set(self, batch_for_datasource: Batch) -> None:
        """When value_set is empty, all non-null values are violations."""
        metric = ColumnDistinctValuesNotInSetCount(column=COLUMN_NAME, value_set=[])
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesNotInSetCountResult)
        # Normalize type for Spark compatibility (may return numpy.int64 or Java long)
        assert int(metric_result.value) == 3  # a, b, c
