from great_expectations.metrics.batch import BatchMetric
from great_expectations.metrics.metric import NonEmptyString, _MetricResult


class ColumnMetric(BatchMetric[_MetricResult]):
    column: NonEmptyString
