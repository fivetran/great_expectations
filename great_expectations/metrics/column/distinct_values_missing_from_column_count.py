from typing import List

from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnDistinctValuesMissingFromColumnCountResult(MetricResult[int]): ...


class ColumnDistinctValuesMissingFromColumnCount(
    ColumnMetric[ColumnDistinctValuesMissingFromColumnCountResult]
):
    """Count of expected values that are missing from the column.

    This is used to efficiently determine if the column contains all expected values,
    without fetching all distinct values.
    """

    name = "column.distinct_values.missing_from_column.count"
    value_set: List
