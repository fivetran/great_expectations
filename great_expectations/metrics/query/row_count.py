from great_expectations.metrics.domain import Domain, NonEmptyString
from great_expectations.metrics.metric import Metric
from great_expectations.metrics.metric_name import DomainName
from great_expectations.metrics.metric_results import MetricResult


class QueryRowCountResult(MetricResult[int]): ...


class QueryRowCount(Metric[QueryRowCountResult], Domain):
    name = f"{DomainName.QUERY.value}.row_count"

    query: NonEmptyString
