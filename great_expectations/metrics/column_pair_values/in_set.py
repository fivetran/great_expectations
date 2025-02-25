from typing import Any

from great_expectations.metrics.domain import ColumnPairValues
from great_expectations.metrics.metric import Metric
from great_expectations.metrics.metric_results import MetricResult


class ColumnPairValuesInSetUnexpectedCountResult(MetricResult[int]): ...


class ColumnPairValuesInSetUnexpectedCount(
    Metric[ColumnPairValuesInSetUnexpectedCountResult], ColumnPairValues
):
    name = "column_pair_values.in_set.unexpected_count"
    value_pairs_set: set[tuple[Any, Any]]
