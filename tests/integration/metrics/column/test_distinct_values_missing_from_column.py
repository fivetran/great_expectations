import pandas as pd

from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column.distinct_values_missing_from_column import (
    ColumnDistinctValuesMissingFromColumn,
    ColumnDistinctValuesMissingFromColumnResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import ALL_DATA_SOURCES

COLUMN_NAME = "my_col"
DATA_FRAME = pd.DataFrame(
    {
        COLUMN_NAME: ["a", "b", "c", "c", "c", None, None],
    },
)


class TestColumnDistinctValuesMissingFromColumn:
    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_all_values_present(self, batch_for_datasource: Batch) -> None:
        """When all expected values are in the column, result should be empty."""
        metric = ColumnDistinctValuesMissingFromColumn(column=COLUMN_NAME, value_set=["a", "b"])
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesMissingFromColumnResult)
        assert metric_result.value == []

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_some_values_missing(self, batch_for_datasource: Batch) -> None:
        """When some expected values are missing from column, return them."""
        metric = ColumnDistinctValuesMissingFromColumn(
            column=COLUMN_NAME,
            value_set=["a", "b", "d"],  # "d" is missing
        )
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesMissingFromColumnResult)
        assert metric_result.value == ["d"]

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_all_values_missing(self, batch_for_datasource: Batch) -> None:
        """When all expected values are missing, return all of them."""
        metric = ColumnDistinctValuesMissingFromColumn(
            column=COLUMN_NAME, value_set=["x", "y", "z"]
        )
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesMissingFromColumnResult)
        assert set(metric_result.value) == {"x", "y", "z"}

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_limit_respected(self, batch_for_datasource: Batch) -> None:
        """Limit parameter should cap the number of values returned."""
        metric = ColumnDistinctValuesMissingFromColumn(
            column=COLUMN_NAME, value_set=["w", "x", "y", "z"], limit=2
        )
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesMissingFromColumnResult)
        assert len(metric_result.value) == 2
