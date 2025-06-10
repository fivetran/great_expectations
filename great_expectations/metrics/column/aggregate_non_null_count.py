from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


# TODO: Maybe we can update null_count.py instead of introducing this.
class ColumnAggregateNonNullCountResult(MetricResult[int]): ...


class ColumnAggregateNonNullCount(ColumnMetric[ColumnAggregateNonNullCountResult]):
    """Count of non-null values in a column"""

    name = "column.non_null_count"
