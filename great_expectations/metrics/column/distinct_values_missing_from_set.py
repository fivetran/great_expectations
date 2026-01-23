from typing import Any

from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnDistinctValuesMissingFromSetResult(MetricResult[list[Any]]): ...


class ColumnDistinctValuesMissingFromSet(ColumnMetric[ColumnDistinctValuesMissingFromSetResult]):
    """Values in the expected set that are missing from the column.

    Used for expect_column_distinct_values_to_contain_set to check which
    required values are not present in the column.

    Args:
        value_set: The set of expected values that should be present
        limit: Maximum number of missing values to return (default: 20)
    """

    name = "column.distinct_values.missing_from_set"
    value_set: list[Any]
    limit: int = 20
