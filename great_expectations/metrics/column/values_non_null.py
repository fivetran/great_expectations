from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_name import DomainName, MetricNameSuffix
from great_expectations.metrics.metric_results import ConditionValues, MetricResult


class ColumnValuesNonNullResult(MetricResult[ConditionValues]): ...


class ColumnValuesNonNull(ColumnMetric[ColumnValuesNonNullResult]):
    name = f"{DomainName.COLUMN_VALUES.value}.nonnull.{MetricNameSuffix.CONDITION.value}"


class ColumnValuesNonNullCountResult(MetricResult[int]): ...


class ColumnValuesNonNullCount(ColumnMetric[ColumnValuesNonNullCountResult]):
    name = f"{DomainName.COLUMN_VALUES.value}.nonnull.{MetricNameSuffix.COUNT.value}"
