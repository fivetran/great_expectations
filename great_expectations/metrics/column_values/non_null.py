from great_expectations.metrics.domain import ColumnValues
from great_expectations.metrics.metric import Metric
from great_expectations.metrics.metric_names import MetricNames
from great_expectations.metrics.metric_results import ConditionValues, MetricResult


class ColumnValuesNonNullResult(MetricResult[ConditionValues]): ...


class ColumnValuesNonNull(Metric[ColumnValuesNonNullResult], ColumnValues):
    name = MetricNames.COLUMN_VALUES_NON_NULL


class ColumnValuesNonNullCountResult(MetricResult[int]): ...


class ColumnValuesNonNullCount(Metric[ColumnValuesNonNullCountResult], ColumnValues):
    name = MetricNames.COLUMN_VALUES_NON_NULL_COUNT
