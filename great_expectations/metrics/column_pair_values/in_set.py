from typing import Any

from great_expectations.metrics.domain import ColumnPairValues
from great_expectations.metrics.metric import Metric
from great_expectations.metrics.metric_results import MetricResult


class ColumnPairValuesInSet(ColumnPairValues):
    value_pairs_set: set[tuple[Any, Any]]


class ColumnPairValuesInSetUnexpectedValuesResult(MetricResult[list[Any]]): ...


class ColumnPairValuesInSetUnexpectedValues(
    Metric[ColumnPairValuesInSetUnexpectedValuesResult], ColumnPairValuesInSet
):
    name = "column_pair_values.in_set.unexpected_values"


class ColumnPairValuesInSetUnexpectedCountResult(MetricResult[int]): ...


class ColumnPairValuesInSetUnexpectedCount(
    Metric[ColumnPairValuesInSetUnexpectedCountResult], ColumnPairValuesInSet
):
    name = "column_pair_values.in_set.unexpected_count"
