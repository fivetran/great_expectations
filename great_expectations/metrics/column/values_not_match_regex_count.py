from great_expectations.compatibility.pydantic import StrictStr
from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnValuesNotMatchRegexCountResult(MetricResult[int]): ...


class ColumnValuesNotMatchRegexCount(ColumnMetric[ColumnValuesNotMatchRegexCountResult]):
    """Count of values in a column that do not match a regex"""

    name = "column_values.not_match_regex.count"

    regex: StrictStr
