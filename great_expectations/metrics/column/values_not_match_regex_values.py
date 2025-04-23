from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnValuesNotMatchRegexValuesResult(MetricResult[list[str]]): ...


class ColumnValuesNotMatchRegexValues(ColumnMetric[ColumnValuesNotMatchRegexValuesResult]):
    name = "column_values.not_match_regex_values"
    regex: str
    limit: int = 20
