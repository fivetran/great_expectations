from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnNullCountResult(MetricResult[int]): ...


class ColumnNullCount(ColumnMetric[ColumnNullCountResult]):
    """Count of null values in a column"""

    name = "column_values.null.count"
