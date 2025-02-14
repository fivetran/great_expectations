from great_expectations.metrics.domain import Batch
from great_expectations.metrics.metric import Metric
from great_expectations.metrics.metric_results import MetricResult


class BatchRowCount(Metric, Batch): ...


class BatchRowCountResult(MetricResult[int]): ...
