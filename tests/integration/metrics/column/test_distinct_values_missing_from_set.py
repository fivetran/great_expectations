import pandas as pd

from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column.distinct_values_missing_from_set import (
    ColumnDistinctValuesMissingFromSet,
    ColumnDistinctValuesMissingFromSetResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import ALL_DATA_SOURCES

COLUMN_NAME = "my_col"
DATA_FRAME = pd.DataFrame(
    {
        COLUMN_NAME: ["a", "b", "c", "c", "c", None],
    },
)


class TestColumnDistinctValuesMissingFromSet:
    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_all_set_values_present(self, batch_for_datasource: Batch) -> None:
        """When all set values are in the column, result should be empty."""
        metric = ColumnDistinctValuesMissingFromSet(column=COLUMN_NAME, value_set=["a", "b", "c"])
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesMissingFromSetResult)
        assert metric_result.value == []

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_some_set_values_missing(self, batch_for_datasource: Batch) -> None:
        """When some set values are not in the column, result should contain them."""
        metric = ColumnDistinctValuesMissingFromSet(
            column=COLUMN_NAME,
            value_set=["a", "b", "c", "d", "e"],  # d and e are missing
        )
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesMissingFromSetResult)
        assert set(metric_result.value) == {"d", "e"}

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_all_set_values_missing(self, batch_for_datasource: Batch) -> None:
        """When no set values are in the column, result should contain all set values."""
        metric = ColumnDistinctValuesMissingFromSet(column=COLUMN_NAME, value_set=["x", "y", "z"])
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesMissingFromSetResult)
        assert set(metric_result.value) == {"x", "y", "z"}

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_subset_of_column_values(self, batch_for_datasource: Batch) -> None:
        """When set is a subset of column values, result should be empty."""
        metric = ColumnDistinctValuesMissingFromSet(
            column=COLUMN_NAME,
            value_set=["a", "b"],  # subset of a, b, c
        )
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesMissingFromSetResult)
        assert metric_result.value == []

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_limit_parameter(self, batch_for_datasource: Batch) -> None:
        """The limit parameter should restrict the number of returned values."""
        metric = ColumnDistinctValuesMissingFromSet(
            column=COLUMN_NAME, value_set=["w", "x", "y", "z"], limit=2
        )
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesMissingFromSetResult)
        assert len(metric_result.value) <= 2
        # All returned values should be from the set
        assert all(v in {"w", "x", "y", "z"} for v in metric_result.value)
