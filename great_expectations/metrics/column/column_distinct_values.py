from typing import Any, Set

from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnDistinctValuesResult(MetricResult[Set[Any]]): ...


class ColumnDistinctValues(ColumnMetric[ColumnDistinctValuesResult]):
    name = "column.distinct_values"
