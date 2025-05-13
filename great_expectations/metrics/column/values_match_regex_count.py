from great_expectations.compatibility.pydantic import StrictStr
from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnValuesMatchRegexCountResult(MetricResult[int]): ...


class ColumnValuesMatchRegexCount(ColumnMetric[ColumnValuesMatchRegexCountResult]):
    """Count of values in a column that match a regex"""

    name = "column_values.match_regex.count"

    regex: StrictStr
