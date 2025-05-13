import math

import pandas as pd

from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.metrics.column.descriptive_stats import (
    ColumnDescriptiveStats,
    ColumnDescriptiveStatsResult,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import ALL_DATA_SOURCES

COLUMN_NAME = "whatevs"
DATA_FRAME = pd.DataFrame(
    {
        COLUMN_NAME: [1, 1, 2, 2, 3, 3, 4, 4, 5, 5],
    },
)


class TestColumnDescriptiveStats:
    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_descriptive_stats(self, batch_for_datasource: Batch) -> None:
        metric = ColumnDescriptiveStats(column=COLUMN_NAME)
        metric_result = batch_for_datasource.compute_metrics(metric)

        assert isinstance(metric_result, ColumnDescriptiveStatsResult)
        assert metric_result.value.min == 1
        assert metric_result.value.max == 5
        assert metric_result.value.mean == 3
        assert math.isclose(
            metric_result.value.standard_deviation, 1.4907119849998598, rel_tol=1e-6, abs_tol=0.0
        )
