from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnMeanResult(MetricResult[float]): ...


class ColumnMean(ColumnMetric[ColumnMeanResult]):
    name = "column.mean"
