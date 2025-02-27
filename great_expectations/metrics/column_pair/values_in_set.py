from typing import Any

from great_expectations.metrics.column_pair.column_pair import ColumnPairMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnPairValuesInSetUnexpectedCountResult(MetricResult[int]): ...


class ColumnPairValuesInSetUnexpectedCount(
    ColumnPairMetric[ColumnPairValuesInSetUnexpectedCountResult]
):
    name = "column_pair_values.in_set.unexpected_count"
    value_pairs_set: set[tuple[Any, Any]]
