from great_expectations.metrics.metric import NonEmptyString
from great_expectations.metrics.metric_results import MetricResult
from great_expectations.metrics.query import QueryMetric


class QueryRowCountResult(MetricResult[int]): ...


class QueryRowCount(QueryMetric[QueryRowCountResult]):
    name = "query.row_count"

    query: NonEmptyString
