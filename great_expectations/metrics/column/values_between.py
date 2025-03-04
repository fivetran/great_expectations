from typing import Optional

from great_expectations.core.types import Comparable
from great_expectations.metrics.column.column import ColumnMetric
from great_expectations.metrics.metric_name import MetricNameSuffix
from great_expectations.metrics.metric_results import ConditionValues


class ColumnValuesBetweenResult(ConditionValues): ...


class ColumnValuesBetween(ColumnMetric[ColumnValuesBetweenResult]):
    name = f"column_values.between.{MetricNameSuffix.CONDITION.value}"
    min_value: Optional[Comparable] = None
    max_value: Optional[Comparable] = None
    strict_min: Optional[bool] = None
    strict_max: Optional[bool] = None

