from great_expectations.metrics.metric import NonEmptyString
from great_expectations.metrics.metric_results import MetricResult
from great_expectations.metrics.query import QueryMetric


class QueryBatchTableResult(MetricResult[list[dict]]): ...


class QueryBatchTable(QueryMetric[QueryBatchTableResult]):
    name = "query.table"

    query: NonEmptyString
    fetch_all: bool = False
