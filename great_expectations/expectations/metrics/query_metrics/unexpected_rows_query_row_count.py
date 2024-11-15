from typing import ClassVar

from great_expectations.expectations.metrics.query_metrics.query_row_count import QueryRowCount


class UnexpectedRowsQueryRowCount(QueryRowCount):
    metric_name = "unexpected_rows_query.row_count"
    value_keys = ("unexpected_rows_query",)

    query_param_name: ClassVar[str] = "unexpected_rows_query"
