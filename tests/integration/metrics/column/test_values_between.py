import pandas as pd
from great_expectations.metrics.column.values_between import ColumnValuesBetween, ColumnValuesBetweenResult
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import PANDAS_DATA_SOURCES, SPARK_DATA_SOURCES, SQL_DATA_SOURCES

COL = "A"

DATA_FRAME = pd.DataFrame(
    {
        COL: [1, 2, 3, 4],
    },
)
TRUE_MIN_VALUE = 0
TRUE_MAX_VALUE = 5


class TestColumnValuesBetween:

    @parameterize_batch_for_data_sources(
        data_source_configs=PANDAS_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success_pandas(self, batch_for_datasource) -> None:
        batch = batch_for_datasource
        metric = ColumnValuesBetween(
            column=COL, min_value=TRUE_MIN_VALUE, max_value=TRUE_MAX_VALUE
        )
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, ColumnValuesBetweenResult)
        assert isinstance(metric_result.value, pd.Series)
        expected_value = pd.Series(
            [False, False, False, False],
            name=COL,
            dtype=bool,
        )
        assert metric_result.value.equals(expected_value)

    @parameterize_batch_for_data_sources(
        data_source_configs=SPARK_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success_spark(self, batch_for_datasource) -> None:
        batch = batch_for_datasource
        metric = ColumnValuesBetween(column=COL)
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, ColumnValuesBetweenResult)
        assert str(metric_result.value) == "False,False,False,False"

    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success_sql(self, batch_for_datasource) -> None:
        batch = batch_for_datasource
        metric = ColumnValuesBetween(column=COL)
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, ColumnValuesBetweenResult)
        assert metric_result.value == self.NON_NULL_COUNT
