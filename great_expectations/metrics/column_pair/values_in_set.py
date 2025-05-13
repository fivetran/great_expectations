from typing import Any

from great_expectations.metrics.column_pair.column_pair import ColumnPairMetric
from great_expectations.metrics.metric_name import MetricNameSuffix
from great_expectations.metrics.metric_results import MetricResult


class ColumnPairValuesInSetUnexpectedCountResult(MetricResult[int]): ...


class ColumnPairValuesInSetUnexpectedCount(
    ColumnPairMetric[ColumnPairValuesInSetUnexpectedCountResult]
):
    """Count of values in a column pair that are not in the set of expected values"""

    name = f"column_pair_values.in_set.{MetricNameSuffix.UNEXPECTED_COUNT.value}"
    value_pairs_set: set[tuple[Any, Any]]
