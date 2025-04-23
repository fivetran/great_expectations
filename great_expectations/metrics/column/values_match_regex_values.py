from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnValuesMatchRegexValuesResult(MetricResult[list[str]]): ...


class ColumnValuesMatchRegexValues(ColumnMetric[ColumnValuesMatchRegexValuesResult]):
    name = "column_values.match_regex"
    regex: str
    limit: int = 20
