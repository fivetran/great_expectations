import pandas as pd

from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column.column_distinct_values import (
    ColumnDistinctValues,
    ColumnDistinctValuesResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import ALL_DATA_SOURCES

COLUMN_NAME = "whatevs"
DATA_FRAME = pd.DataFrame(
    {
        COLUMN_NAME: ["a", "b", "c", "c", "c", "c", "c", "c", "c", "c", None, None],
    },
)


class TestColumnDistinctValues:
    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_distinct_values(self, batch_for_datasource: Batch) -> None:
        metric = ColumnDistinctValues(column=COLUMN_NAME)
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDistinctValuesResult)
        assert metric_result.value == {"a", "b", "c"}
