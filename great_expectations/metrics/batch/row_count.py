from great_expectations.metrics.batch import BatchMetric
from great_expectations.metrics.metric_results import MetricResult


class BatchRowCountResult(MetricResult[int]): ...


class BatchRowCount(BatchMetric[BatchRowCountResult]):
    """Count of rows in a table"""

    name = "table.row_count"
