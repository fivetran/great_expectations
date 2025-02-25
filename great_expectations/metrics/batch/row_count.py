from great_expectations.metrics.batch import BatchMetric
from great_expectations.metrics.metric_name import DomainName
from great_expectations.metrics.metric_results import MetricResult


class BatchRowCountResult(MetricResult[int]): ...


class BatchRowCount(BatchMetric[BatchRowCountResult]):
    name = f"{DomainName.BATCH.value}.row_count"
