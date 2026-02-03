import pandas as pd

from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column.distinct_values_missing_from_column_count import (
    ColumnDistinctValuesMissingFromColumnCount,
    ColumnDistinctValuesMissingFromColumnCountResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import ALL_DATA_SOURCES

COLUMN_NAME = "my_col"
DATA_FRAME = pd.DataFrame(
    {
        COLUMN_NAME: ["a", "b", "c", "c", "c", None, None],
    },
)


class TestColumnDistinctValuesMissingFromColumnCount:
    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_all_values_present(self, batch_for_datasource: Batch) -> None:
        """When all expected values are in the column, count should be 0."""
        metric = ColumnDistinctValuesMissingFromColumnCount(
            column=COLUMN_NAME, value_set=["a", "b"]
        )
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesMissingFromColumnCountResult)
        assert metric_result.value == 0

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_some_values_missing(self, batch_for_datasource: Batch) -> None:
        """When some expected values are missing from column, count them."""
        metric = ColumnDistinctValuesMissingFromColumnCount(
            column=COLUMN_NAME,
            value_set=["a", "b", "d"],  # "d" is missing
        )
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesMissingFromColumnCountResult)
        assert metric_result.value == 1  # "d" is missing

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_all_values_missing(self, batch_for_datasource: Batch) -> None:
        """When all expected values are missing, count all of them."""
        metric = ColumnDistinctValuesMissingFromColumnCount(
            column=COLUMN_NAME, value_set=["x", "y", "z"]
        )
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesMissingFromColumnCountResult)
        assert metric_result.value == 3

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_empty_value_set(self, batch_for_datasource: Batch) -> None:
        """When value_set is empty, nothing is missing."""
        metric = ColumnDistinctValuesMissingFromColumnCount(column=COLUMN_NAME, value_set=[])
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesMissingFromColumnCountResult)
        assert metric_result.value == 0
