from typing import Any

from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnDistinctValuesResult(MetricResult[set[Any]]): ...


class ColumnDistinctValues(ColumnMetric[ColumnDistinctValuesResult]):
    """List of distinct values in a column"""

    name = "column.distinct_values"
