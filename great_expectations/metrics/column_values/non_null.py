from great_expectations.metrics.domain import ColumnValues
from great_expectations.metrics.metric import Metric
from great_expectations.metrics.metric_name import DomainName, MetricNameSuffix
from great_expectations.metrics.metric_results import ConditionValues, MetricResult


class ColumnValuesNonNullResult(MetricResult[ConditionValues]): ...


class ColumnValuesNonNull(Metric[ColumnValuesNonNullResult], ColumnValues):
    name = f"{DomainName.COLUMN_VALUES.value}.nonnull.{MetricNameSuffix.CONDITION.value}"


class ColumnValuesNonNullCountResult(MetricResult[int]): ...


class ColumnValuesNonNullCount(Metric[ColumnValuesNonNullCountResult], ColumnValues):
    name = f"{DomainName.COLUMN_VALUES.value}.nonnull.{MetricNameSuffix.COUNT.value}"
