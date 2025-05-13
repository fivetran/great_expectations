from typing import Any

from great_expectations.metrics.metric import NonEmptyString
from great_expectations.metrics.metric_results import MetricResult
from great_expectations.metrics.query import QueryMetric


class QueryDataSourceTableResult(MetricResult[Any]): ...


class QueryDataSourceTable(QueryMetric[QueryDataSourceTableResult]):
    name = "query.data_source_table"

    query: NonEmptyString
    data_source_name: NonEmptyString
