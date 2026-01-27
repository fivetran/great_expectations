from typing import Any

from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnDistinctValuesNotInSetCountResult(MetricResult[int]): ...


class ColumnDistinctValuesNotInSetCount(ColumnMetric[ColumnDistinctValuesNotInSetCountResult]):
    """Count of distinct column values that are NOT in the provided value_set."""

    name = "column.distinct_values.not_in_set.count"
    value_set: list[Any]
