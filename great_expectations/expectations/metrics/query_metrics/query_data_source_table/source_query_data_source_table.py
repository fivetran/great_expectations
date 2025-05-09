from typing import ClassVar

from great_expectations.expectations.metrics.query_metrics.query_data_source_table.query_data_source_table import (  # noqa: E501  # too long, but rarely imported
    QueryDataSourceTable,
)


class SourceQueryDataSourceTable(QueryDataSourceTable):
    metric_name = "source_query.data_source_table"
    value_keys = ("source_query", "source_data_source_name")

    query_param_name: ClassVar[str] = "source_query"
    data_source_name_param_name: ClassVar[str] = "source_data_source_name"
