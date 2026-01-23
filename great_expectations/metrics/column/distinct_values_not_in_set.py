from typing import Any

from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnDistinctValuesNotInSetResult(MetricResult[list[Any]]): ...


class ColumnDistinctValuesNotInSet(ColumnMetric[ColumnDistinctValuesNotInSetResult]):
    """Sample of distinct column values NOT in a provided set.

    This metric pushes the comparison logic to the database and uses LIMIT to
    restrict the number of values returned. Used for optimizing
    expect_column_distinct_values_to_be_in_set expectations.

    Args:
        value_set: The set of expected values
        limit: Maximum number of violation values to return (default: 20)
    """

    name = "column.distinct_values.not_in_set"
    value_set: list[Any]
    limit: int = 20
