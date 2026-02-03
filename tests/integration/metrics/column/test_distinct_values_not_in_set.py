import pandas as pd

from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column.distinct_values_not_in_set import (
    ColumnDistinctValuesNotInSet,
    ColumnDistinctValuesNotInSetResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import ALL_DATA_SOURCES

COLUMN_NAME = "my_col"
DATA_FRAME = pd.DataFrame(
    {
        COLUMN_NAME: ["a", "b", "c", "c", "c", None, None],
    },
)


class TestColumnDistinctValuesNotInSet:
    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_all_values_in_set(self, batch_for_datasource: Batch) -> None:
        """When all column values are in the set, result should be empty."""
        metric = ColumnDistinctValuesNotInSet(column=COLUMN_NAME, value_set=["a", "b", "c"])
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesNotInSetResult)
        assert metric_result.value == []

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_some_values_not_in_set(self, batch_for_datasource: Batch) -> None:
        """When some column values are not in the set, return them."""
        metric = ColumnDistinctValuesNotInSet(
            column=COLUMN_NAME,
            value_set=["a", "b"],  # missing "c"
        )
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesNotInSetResult)
        assert metric_result.value == ["c"]

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_no_values_in_set(self, batch_for_datasource: Batch) -> None:
        """When no column values are in the set, return all distinct values."""
        metric = ColumnDistinctValuesNotInSet(column=COLUMN_NAME, value_set=["x", "y", "z"])
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesNotInSetResult)
        assert set(metric_result.value) == {"a", "b", "c"}

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_limit_respected(self, batch_for_datasource: Batch) -> None:
        """Limit parameter should cap the number of values returned."""
        metric = ColumnDistinctValuesNotInSet(column=COLUMN_NAME, value_set=["x"], limit=2)
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesNotInSetResult)
        assert len(metric_result.value) == 2
