import pandas as pd

from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column.values_match_regex_count import (
    ColumnValuesMatchRegexCount,
    ColumnValuesMatchRegexCountResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import SQLServerDatasourceTestConfig
from tests.metrics.conftest import (
    ALL_DATA_SOURCES,
    SPARK_DATA_SOURCES,
    SQL_DATA_SOURCES,
    SnowflakeDatasourceTestConfig,
)

COLUMN_NAME = "whatevs"

DATA_FRAME = pd.DataFrame({COLUMN_NAME: ["abc", "def", "ghi", "1ab2", "1ab3", None]})

# SQL Server ships no regex operator, so the per-dialect expression these metrics compile to has
# no SQL Server form and the metric raises instead of computing. The regex expectation modules
# draw the same line with hand-written supported-source lists; deriving it from the shared lists
# here keeps this module in step as backends join them.
REGEX_CAPABLE_SQL_DATA_SOURCES = [
    datasource
    for datasource in SQL_DATA_SOURCES
    if not isinstance(datasource, SQLServerDatasourceTestConfig)
]

REGEX_CAPABLE_DATA_SOURCES_EXCEPT_SNOWFLAKE = [
    datasource
    for datasource in ALL_DATA_SOURCES
    if not isinstance(datasource, (SQLServerDatasourceTestConfig, SnowflakeDatasourceTestConfig))
]


class TestColumnValuesMatchRegexCount:
    @parameterize_batch_for_data_sources(
        data_source_configs=REGEX_CAPABLE_DATA_SOURCES_EXCEPT_SNOWFLAKE,
        data=DATA_FRAME,
    )
    def test_partial_match_characters(self, batch_for_datasource: Batch) -> None:
        metric = ColumnValuesMatchRegexCount(column=COLUMN_NAME, regex="ab")
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnValuesMatchRegexCountResult)
        assert metric_result.value == 3

    @parameterize_batch_for_data_sources(
        data_source_configs=SPARK_DATA_SOURCES + REGEX_CAPABLE_SQL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_special_characters(self, batch_for_datasource: Batch) -> None:
        metric = ColumnValuesMatchRegexCount(column=COLUMN_NAME, regex="^(a|d).+")
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnValuesMatchRegexCountResult)
        assert metric_result.value == 2
