from typing import List

from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnDistinctValuesNotInSetCountResult(MetricResult[int]): ...


class ColumnDistinctValuesNotInSetCount(ColumnMetric[ColumnDistinctValuesNotInSetCountResult]):
    """Count of distinct values in a column that are NOT in the expected set.

    This is used to efficiently determine if all column values are in the expected set,
    without fetching all distinct values.
    """

    name = "column.distinct_values.not_in_set.count"
    value_set: List
