from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnValuesMatchRegexValuesResult(MetricResult[list[str]]): ...


class ColumnValuesMatchRegexValues(ColumnMetric[ColumnValuesMatchRegexValuesResult]):
    """List of values in a column that match a regex"""

    name = "column_values.match_regex"
    regex: str
    limit: int = 20
