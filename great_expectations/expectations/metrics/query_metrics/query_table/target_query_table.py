from typing import ClassVar

from great_expectations.expectations.metrics.query_metrics.query_table.query_table import QueryTable


class TargetQueryTable(QueryTable):
    metric_name = "target_query.table"
    value_keys = ("target_query",)

    query_param_name: ClassVar[str] = "target_query"
