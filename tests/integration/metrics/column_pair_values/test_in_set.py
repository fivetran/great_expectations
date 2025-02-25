import pandas as pd

from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column_pair_values.in_set import (
    ColumnPairValuesInSetUnexpectedCount,
    ColumnPairValuesInSetUnexpectedCountResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import PANDAS_DATA_SOURCES, SPARK_DATA_SOURCES, SQL_DATA_SOURCES

DATA_FRAME = pd.DataFrame(
    {"id": [1, 2, 3, 4], "A": [1, 2, 3, 4], "B": ["a", "b", "c", "d"]},
)
SUCCESS_VALUE_PAIR_SET = {(1, "a"), (2, "b"), (3, "c"), (4, "d")}
FAILURE_VALUE_PAIR_SET = {(1, "a"), (2, "b"), (3, "c")}
FAILURE_RESULT_COUNT = 1


class TestColumnPairValuesInSetUnexpectedValues:
    @parameterize_batch_for_data_sources(
        data_source_configs=PANDAS_DATA_SOURCES + SPARK_DATA_SOURCES + SQL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success(self, batch_for_datasource: Batch) -> None:
        batch = batch_for_datasource
        metric = ColumnPairValuesInSetUnexpectedCount(
            batch_id=batch.id,
            value_pairs_set=SUCCESS_VALUE_PAIR_SET,
            column_A="A",
            column_B="B",
        )
        result = batch.compute_metrics(metric)
        assert isinstance(result, ColumnPairValuesInSetUnexpectedCountResult)
        assert result.value == 0

    @parameterize_batch_for_data_sources(
        data_source_configs=PANDAS_DATA_SOURCES + SPARK_DATA_SOURCES + SQL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_failure(self, batch_for_datasource: Batch) -> None:
        batch = batch_for_datasource
        metric = ColumnPairValuesInSetUnexpectedCount(
            batch_id=batch.id,
            value_pairs_set=FAILURE_VALUE_PAIR_SET,
            column_A="A",
            column_B="B",
        )
        result = batch.compute_metrics(metric)
        assert isinstance(result, ColumnPairValuesInSetUnexpectedCountResult)
        assert result.value == FAILURE_RESULT_COUNT
