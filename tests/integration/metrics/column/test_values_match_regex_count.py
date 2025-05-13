import pandas as pd

from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column.values_match_regex_count import (
    ColumnValuesMatchRegexCount,
    ColumnValuesMatchRegexCountResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import (
    ALL_DATA_SOURCES,
    SPARK_DATA_SOURCES,
    SQL_DATA_SOURCES,
    SnowflakeDatasourceTestConfig,
)

COLUMN_NAME = "whatevs"

DATA_FRAME = pd.DataFrame({COLUMN_NAME: ["abc", "def", "ghi", "1ab2", "1ab3", None]})

ALL_DATA_SOURCES_EXCEPT_SNOWFLAKE = [
    datasource
    for datasource in ALL_DATA_SOURCES
    if not isinstance(datasource, SnowflakeDatasourceTestConfig)
]


class TestColumnValuesMatchRegexCount:
    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES_EXCEPT_SNOWFLAKE,
        data=DATA_FRAME,
    )
    def test_partial_match_characters(self, batch_for_datasource: Batch) -> None:
        metric = ColumnValuesMatchRegexCount(column=COLUMN_NAME, regex="ab")
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnValuesMatchRegexCountResult)
        assert metric_result.value == 3

    @parameterize_batch_for_data_sources(
        data_source_configs=SPARK_DATA_SOURCES + SQL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_special_characters(self, batch_for_datasource: Batch) -> None:
        metric = ColumnValuesMatchRegexCount(column=COLUMN_NAME, regex="^(a|d).+")
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnValuesMatchRegexCountResult)
        assert metric_result.value == 2
