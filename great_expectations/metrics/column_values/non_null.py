from great_expectations.metrics.domain import ColumnValues
from great_expectations.metrics.metric import Metric
from great_expectations.metrics.metric_results import ColumnValuesCondition, MetricResult


class ColumnValuesNonNullResult(MetricResult[ColumnValuesCondition]): ...


class ColumnValuesNonNull(Metric[ColumnValuesNonNullResult], ColumnValues):
    name = "column_values.nonnull.condition"


class ColumnValuesNonNullCountResult(MetricResult[int]): ...


class ColumnValuesNonNullCount(Metric[ColumnValuesNonNullCountResult], ColumnValues):
    name = "column_values.nonnull.count"
