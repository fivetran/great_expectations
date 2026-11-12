import pandas as pd

from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column.distinct_values import (
    ColumnDistinctValues,
    ColumnDistinctValuesResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import PANDAS_DATA_SOURCES, SPARK_DATA_SOURCES, SQL_DATA_SOURCES

COLUMN_NAME = "whatevs"
DATA_FRAME = pd.DataFrame(
    {
        COLUMN_NAME: ["a", "b", "c", "c", "c", "c", "c", "c", "c", "c", None, None],
    },
)


FILTER_COLUMN_NAME = "filter_col"
# A row condition of `filter_col > 0` drops the first row, the only one holding "decoy".
ROW_CONDITION_DATA_FRAME = pd.DataFrame(
    {COLUMN_NAME: ["decoy", "a", "b", "b"], FILTER_COLUMN_NAME: [0, 1, 1, 1]}
)


def get_pandas_data_sources():
    return PANDAS_DATA_SOURCES


def get_non_pandas_data_sources():
    return SPARK_DATA_SOURCES + SQL_DATA_SOURCES


class TestColumnDistinctValues:
    @parameterize_batch_for_data_sources(
        data_source_configs=get_pandas_data_sources(),
        data=DATA_FRAME,
    )
    def test_distinct_values_pandas(self, batch_for_datasource: Batch) -> None:
        metric = ColumnDistinctValues(column=COLUMN_NAME)
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesResult)
        # For pandas, we expect the null values to be included
        assert len(metric_result.value) == 4  # a, b, c, and null
        assert "a" in metric_result.value
        assert "b" in metric_result.value
        assert "c" in metric_result.value
        # Check for either None or nan depending on source
        assert any(pd.isna(val) for val in metric_result.value)

    @parameterize_batch_for_data_sources(
        data_source_configs=get_non_pandas_data_sources(),
        data=DATA_FRAME,
    )
    def test_distinct_values_non_pandas(self, batch_for_datasource: Batch) -> None:
        metric = ColumnDistinctValues(column=COLUMN_NAME)
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesResult)
        # For SQL and Spark, we expect only the non-null values
        assert metric_result.value == {"a", "b", "c"}

    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=ROW_CONDITION_DATA_FRAME,
    )
    def test_distinct_values_sql_row_condition(self, batch_for_datasource: Batch) -> None:
        """A row condition makes the SQL domain a SELECT, which must be wrapped to be a FROM."""
        metric = ColumnDistinctValues(
            column=COLUMN_NAME,
            row_condition=f'col("{FILTER_COLUMN_NAME}") > 0',
            condition_parser="great_expectations",
        )
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesResult), metric_result
        assert metric_result.value == {"a", "b"}
