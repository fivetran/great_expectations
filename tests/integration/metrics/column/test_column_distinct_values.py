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

        # NOTE: Different backends handle null values differently:
        # - Pandas: Includes null values (None or nan depending on source)
        # - SQLAlchemy/Spark: Excludes null values
        datasource_type = batch_for_datasource.datasource.type
        if datasource_type in ["pandas", "pandas_filesystem"]:
            # For pandas, we expect the null values to be included
            assert len(metric_result.value) == 4  # a, b, c, and null
            assert "a" in metric_result.value
            assert "b" in metric_result.value
            assert "c" in metric_result.value
            # Check for either None or nan depending on source
            assert any(pd.isna(val) for val in metric_result.value)
        else:
            # For SQL and Spark, we expect only the non-null values
            assert metric_result.value == {"a", "b", "c"}
