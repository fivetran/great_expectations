from typing import Any

from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnDistinctValuesNotInSetCountResult(MetricResult[int]): ...


class ColumnDistinctValuesNotInSetCount(ColumnMetric[ColumnDistinctValuesNotInSetCountResult]):
    """Count of distinct column values NOT in a provided set.

    This metric pushes the comparison logic to the database, avoiding the need
    to fetch all distinct values into memory. Used for optimizing
    expect_column_distinct_values_to_be_in_set expectations.
    """

    name = "column.distinct_values.not_in_set.count"
    value_set: list[Any]
