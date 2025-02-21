from great_expectations.metrics import Metric
from great_expectations.metrics.domain import ColumnValues
from great_expectations.metrics.metric_results import MetricResult


class ColumnValuesNonNullResult(MetricResult[int]): ...


class ColumnValuesNonNull(Metric[ColumnValuesNonNullResult], ColumnValues):
    name = "column_values.non_null.condition"


class ColumnValuesNonNullCountResult(MetricResult[int]): ...


class ColumnValuesNonNullCount(Metric[ColumnValuesNonNullCountResult], ColumnValues):
    name = "column_values.non_null.count"
