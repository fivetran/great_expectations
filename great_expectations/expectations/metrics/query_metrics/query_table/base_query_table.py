from typing import ClassVar

from great_expectations.expectations.metrics.query_metrics.query_table.query_table import QueryTable


class BaseQueryTable(QueryTable):
    metric_name = "base_query.table"
    value_keys = ("base_query",)

    query_param_name: ClassVar[str] = "base_query"
