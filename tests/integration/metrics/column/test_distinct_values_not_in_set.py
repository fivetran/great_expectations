import pandas as pd

from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column.distinct_values_not_in_set import (
    ColumnDistinctValuesNotInSet,
    ColumnDistinctValuesNotInSetResult,
)
from great_expectations.metrics.column.distinct_values_not_in_set_count import (
    ColumnDistinctValuesNotInSetCount,
    ColumnDistinctValuesNotInSetCountResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import ALL_DATA_SOURCES

COLUMN_NAME = "my_col"
DATA_FRAME = pd.DataFrame(
    {
        COLUMN_NAME: ["a", "b", "c", "c", "c", None],
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
        """When no column values are in the set, count should be all distinct values."""
        metric = ColumnDistinctValuesNotInSetCount(column=COLUMN_NAME, value_set=["x", "y", "z"])
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesNotInSetCountResult)
        assert metric_result.value == 3  # a, b, c are all not in set


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
        """When some column values are not in the set, result should contain them."""
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
        """When no column values are in the set, result should contain all distinct values."""
        metric = ColumnDistinctValuesNotInSet(column=COLUMN_NAME, value_set=["x", "y", "z"])
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesNotInSetResult)
        assert set(metric_result.value) == {"a", "b", "c"}

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_limit_parameter(self, batch_for_datasource: Batch) -> None:
        """The limit parameter should restrict the number of returned values."""
        metric = ColumnDistinctValuesNotInSet(
            column=COLUMN_NAME, value_set=["x", "y", "z"], limit=2
        )
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesNotInSetResult)
        assert len(metric_result.value) <= 2
        # All returned values should be from the column
        assert all(v in {"a", "b", "c"} for v in metric_result.value)
