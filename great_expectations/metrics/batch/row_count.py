from great_expectations.metrics.domain import Batch
from great_expectations.metrics.metric import Metric
from great_expectations.metrics.metric_name import DomainName
from great_expectations.metrics.metric_results import MetricResult


class BatchRowCountResult(MetricResult[int]): ...


class BatchRowCount(Metric[BatchRowCountResult], Batch):
    name = f"{DomainName.BATCH.value}.row_count"
