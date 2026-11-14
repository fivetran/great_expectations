import pandas as pd

from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column.sample_values import (
    ColumnSampleValues,
    ColumnSampleValuesResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import SQL_DATA_SOURCES

COLUMN_NAME = "stuff"
DATA_FRAME = pd.DataFrame(
    {
        COLUMN_NAME: [
            "a",
            "b",
            "c",
            "c",
            "c",
            "c",
            "c",
            "c",
            "c",
            "c",
            "a",
            "b",
            "c",
            "c",
            "c",
            "c",
            "c",
            "c",
            "c",
            "c",
            "c",
            "c",
        ],
    },
)


FILTER_COLUMN_NAME = "filter_col"
# A row condition of `filter_col > 0` drops the first row, the only one holding "decoy".
ROW_CONDITION_DATA_FRAME = pd.DataFrame(
    {COLUMN_NAME: ["decoy", "a", "b", "b"], FILTER_COLUMN_NAME: [0, 1, 1, 1]}
)


class TestColumnSampleValues:
    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_column_sample_values_default(self, batch_for_datasource: Batch) -> None:
        metric = ColumnSampleValues(column=COLUMN_NAME)
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnSampleValuesResult)
        assert len(metric_result.value) == 20
        assert isinstance(metric_result.value[0], str)

    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_column_sample_values_count(self, batch_for_datasource: Batch) -> None:
        metric = ColumnSampleValues(column=COLUMN_NAME, count=10)
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnSampleValuesResult)
        assert len(metric_result.value) == 10
        assert isinstance(metric_result.value[0], str)

    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=ROW_CONDITION_DATA_FRAME,
    )
    def test_column_sample_values_sql_row_condition(self, batch_for_datasource: Batch) -> None:
        """A row condition makes the SQL domain a SELECT, which must be wrapped to be a FROM."""
        metric = ColumnSampleValues(
            column=COLUMN_NAME,
            row_condition=f'col("{FILTER_COLUMN_NAME}") > 0',
            condition_parser="great_expectations",
        )
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnSampleValuesResult), metric_result
        assert sorted(metric_result.value) == ["a", "b", "b"]
