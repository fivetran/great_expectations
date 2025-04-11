import pandas as pd

from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column.column_values_match_regex_count import (
    ColumnValuesMatchRegexCount,
    ColumnValuesMatchRegexCountResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import ALL_DATA_SOURCES

COLUMN_NAME = "whatevs"
BIG_NUMBER = 101
MATCH_ALL_REGEX = ".+"

DATA_FRAME = pd.DataFrame({COLUMN_NAME: ["abc", "def", "ghi", "1ab2", "1ab3", None]})
DATA_FRAME_WITH_LOTS_OF_VALUES = pd.DataFrame({COLUMN_NAME: ["A"] * BIG_NUMBER})


class TestColumnValuesMatchRegexCount:
    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_partial_match_characters(self, batch_for_datasource: Batch) -> None:
        metric = ColumnValuesMatchRegexCount(column=COLUMN_NAME, regex="ab")
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnValuesMatchRegexCountResult)
        assert metric_result.value == 3

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_special_characters(self, batch_for_datasource: Batch) -> None:
        metric = ColumnValuesMatchRegexCount(column=COLUMN_NAME, regex="^(a|d).+")
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnValuesMatchRegexCountResult)
        assert metric_result.value == 2
