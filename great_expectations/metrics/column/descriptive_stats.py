from great_expectations.expectations.metrics.column_aggregate_metrics.column_descriptive_stats import (  # noqa: E501
    DescriptiveStats,
)
from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnDescriptiveStatsResult(MetricResult[DescriptiveStats]): ...


class ColumnDescriptiveStats(ColumnMetric[ColumnDescriptiveStatsResult]):
    name = "column.descriptive_stats"
