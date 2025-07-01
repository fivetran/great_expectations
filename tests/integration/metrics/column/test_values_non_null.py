import pandas as pd

from great_expectations.compatibility.pyspark import functions as F
from great_expectations.compatibility.sqlalchemy import BinaryExpression, ColumnClause
from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column.values_non_null import (
    ColumnValuesNonNull,
    ColumnValuesNonNullCount,
    ColumnValuesNonNullCountResult,
    ColumnValuesNonNullResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import PANDAS_DATA_SOURCES, SPARK_DATA_SOURCES, SQL_DATA_SOURCES

STRING_COLUMN_NAME = "letter"
DATA_FRAME = pd.DataFrame(
    {
        STRING_COLUMN_NAME: ["a", None, "c", "d"],
    },
)


class TestColumnValuesNonNull:
    @parameterize_batch_for_data_sources(
        data_source_configs=PANDAS_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success_pandas(self, batch_for_datasource: Batch) -> None:
        batch = batch_for_datasource
        metric = ColumnValuesNonNull(column=STRING_COLUMN_NAME)
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, ColumnValuesNonNullResult)
        assert isinstance(metric_result.value, pd.Series)
        expected_value = pd.Series(
            [False, True, False, False],
            name=STRING_COLUMN_NAME,
            dtype=bool,
        )
        assert metric_result.value.equals(expected_value)

    @parameterize_batch_for_data_sources(
        data_source_configs=SPARK_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success_spark(self, batch_for_datasource: Batch) -> None:
        batch = batch_for_datasource
        metric = ColumnValuesNonNull(column=STRING_COLUMN_NAME)
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, ColumnValuesNonNullResult)
        expected_value = ~(F.col(STRING_COLUMN_NAME).isNotNull())
        assert str(metric_result.value) == str(expected_value)

    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success_sql(self, batch_for_datasource: Batch) -> None:
        batch = batch_for_datasource
        metric = ColumnValuesNonNull(column=STRING_COLUMN_NAME)
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, ColumnValuesNonNullResult)
        assert isinstance(metric_result.value, BinaryExpression)
        expected_value = ColumnClause(STRING_COLUMN_NAME).is_(None)
        assert metric_result.value.compare(expected_value)


class TestColumnValuesNonNullCount:
    NON_NULL_COUNT = 3

    @parameterize_batch_for_data_sources(
        data_source_configs=PANDAS_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success_pandas(self, batch_for_datasource: Batch) -> None:
        batch = batch_for_datasource
        metric = ColumnValuesNonNullCount(column=STRING_COLUMN_NAME)
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, ColumnValuesNonNullCountResult)
        assert metric_result.value == self.NON_NULL_COUNT

    @parameterize_batch_for_data_sources(
        data_source_configs=SPARK_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success_spark(self, batch_for_datasource: Batch) -> None:
        batch = batch_for_datasource
        metric = ColumnValuesNonNullCount(column=STRING_COLUMN_NAME)
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, ColumnValuesNonNullCountResult)
        assert metric_result.value == self.NON_NULL_COUNT

    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success_sql(self, batch_for_datasource: Batch) -> None:
        batch = batch_for_datasource
        metric = ColumnValuesNonNullCount(column=STRING_COLUMN_NAME)
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, ColumnValuesNonNullCountResult)
        assert metric_result.value == self.NON_NULL_COUNT
