from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnDistinctValuesCountResult(MetricResult[int]): ...


class ColumnDistinctValuesCount(ColumnMetric[ColumnDistinctValuesCountResult]):
    """Count of distinct values in a column"""

    name = "column.distinct_values.count"
