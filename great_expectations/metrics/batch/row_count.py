from great_expectations.metrics.batch import BatchMetric
from great_expectations.metrics.metric_results import MetricResult


class BatchRowCountResult(MetricResult[int]): ...


class BatchRowCount(BatchMetric[BatchRowCountResult]):
    name = "table.row_count"
