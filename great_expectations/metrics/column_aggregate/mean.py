from great_expectations.metrics.domain import ColumnValues
from great_expectations.metrics.metric import Metric
from great_expectations.metrics.metric_results import MetricResult


class ColumnValuesMeanResult(MetricResult[float]): ...


class ColumnValuesMean(Metric[ColumnValuesMeanResult], ColumnValues):
    name = "column.mean"
