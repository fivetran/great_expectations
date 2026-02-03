from typing import List

from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnDistinctValuesNotInSetResult(MetricResult[List]): ...


class ColumnDistinctValuesNotInSet(ColumnMetric[ColumnDistinctValuesNotInSetResult]):
    """Sample of distinct values in a column that are NOT in the expected set.

    This returns a limited sample of values that violate the "be in set" constraint,
    without fetching all distinct values.
    """

    name = "column.distinct_values.not_in_set"
    value_set: List
    limit: int = 20
