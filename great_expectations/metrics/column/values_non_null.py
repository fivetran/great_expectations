from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_name import MetricNameSuffix
from great_expectations.metrics.metric_results import ConditionValues, MetricResult


class ColumnValuesNonNullResult(MetricResult[ConditionValues]): ...


class ColumnValuesNonNull(ColumnMetric[ColumnValuesNonNullResult]):
    name = f"column_values.nonnull.{MetricNameSuffix.CONDITION.value}"


class ColumnValuesNonNullCountResult(MetricResult[int]): ...


class ColumnValuesNonNullCount(ColumnMetric[ColumnValuesNonNullCountResult]):
    """Count of non-null values in a column"""

    name = f"column_values.nonnull.{MetricNameSuffix.COUNT.value}"
