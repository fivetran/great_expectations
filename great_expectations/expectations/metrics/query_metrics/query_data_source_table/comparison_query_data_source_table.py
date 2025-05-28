from typing import ClassVar

from great_expectations.expectations.metrics.query_metrics.query_data_source_table.query_data_source_table import (  # noqa: E501  # too long, but rarely imported
    QueryDataSourceTable,
)


class ComparisonQueryDataSourceTable(QueryDataSourceTable):
    metric_name = "comparison_query.data_source_table"
    value_keys = ("comparison_query", "comparison_data_source_name")

    query_param_name: ClassVar[str] = "comparison_query"
    data_source_name_param_name: ClassVar[str] = "comparison_data_source_name"
