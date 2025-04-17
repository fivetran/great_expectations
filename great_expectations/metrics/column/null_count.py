from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnNullCountResult(MetricResult[int]): ...


class ColumnNullCount(ColumnMetric[ColumnNullCountResult]):
    name = "column_values.null.count"
