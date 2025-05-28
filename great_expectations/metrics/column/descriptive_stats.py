from great_expectations.compatibility.pydantic import BaseModel
from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class DescriptiveStats(BaseModel):
    min: float
    max: float
    mean: float
    standard_deviation: float


class ColumnDescriptiveStatsResult(MetricResult[DescriptiveStats]): ...


class ColumnDescriptiveStats(ColumnMetric[ColumnDescriptiveStatsResult]):
    """Summary statistics for a column: min, mean, max, standard deviation"""

    name = "column.descriptive_stats"
