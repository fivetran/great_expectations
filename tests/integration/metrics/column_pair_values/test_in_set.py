import pandas as pd
import pytest

from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column_pair_values.in_set import (
    ColumnPairValuesInSetUnexpectedCount,
    ColumnPairValuesInSetUnexpectedCountResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import PANDAS_DATA_SOURCES, SPARK_DATA_SOURCES, SQL_DATA_SOURCES

COL_A_WITH_NULLS = "PARTIAL_NULLS_A"
COL_B_WITH_NULLS = "PARTIAL_NULLS_B"

DATA_FRAME = pd.DataFrame(
    {
        "id": [1, 2, 3, 4],
        "A": [1, 2, 3, 4],
        "B": ["a", "b", "c", "d"],
        COL_A_WITH_NULLS: [None, "b", "c", None],
        COL_B_WITH_NULLS: [None, "b", None, "d"],
    },
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

    @pytest.mark.parametrize(
        "ignore_row_if,unexpected_count",
        [
            ("either_value_is_missing", 1),  # this is expected
            ("both_values_are_missing", 1),  # shouldn't this be 3?
            ("neither", 3),  # shouldn't this be 4?
        ],
    )
    @parameterize_batch_for_data_sources(
        data_source_configs=PANDAS_DATA_SOURCES + SPARK_DATA_SOURCES + SQL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_ignore_row_if(
        self, batch_for_datasource: Batch, ignore_row_if, unexpected_count
    ) -> None:
        batch = batch_for_datasource
        metric = ColumnPairValuesInSetUnexpectedCount(
            batch_id=batch.id,
            value_pairs_set={("d", "d")},  # does not match anything
            column_A=COL_B_WITH_NULLS,
            column_B=COL_B_WITH_NULLS,
            ignore_row_if=ignore_row_if,
        )
        result = batch.compute_metrics(metric)
        assert result.value == unexpected_count
