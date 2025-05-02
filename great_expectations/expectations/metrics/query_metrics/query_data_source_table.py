from __future__ import annotations

from typing import Any, Dict

from great_expectations.execution_engine import (
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.metric_provider import metric_value
from great_expectations.expectations.metrics.query_metric_provider import (
    QueryMetricProvider,
)


class QueryDataSourceTable(QueryMetricProvider):
    metric_name = "query.data_source_table"
    value_keys = ("query", "data_source_name")

    @metric_value(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        execution_engine: SqlAlchemyExecutionEngine,
        metric_domain_kwargs: dict,
        metric_value_kwargs: dict,
        metrics: Dict[str, Any],
        runtime_configuration: dict,
    ) -> list[dict]:
        from great_expectations.data_context import project_manager

        # we're querying data from another data source,
        # so we need to use the execution engine of that data source.
        data_source_name = metric_value_kwargs["data_source_name"]
        data_source = project_manager.get_datasources()[data_source_name]
        other_execution_engine = data_source.get_execution_engine()
        query = cls._get_query_from_metric_value_kwargs(metric_value_kwargs)
        return cls._get_sqlalchemy_records_from_substituted_batch_subquery(
            substituted_batch_subquery=query,
            execution_engine=other_execution_engine,
        )
