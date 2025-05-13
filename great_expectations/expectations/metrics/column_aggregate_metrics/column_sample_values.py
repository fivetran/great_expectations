from __future__ import annotations

from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.core.metric_domain_types import MetricDomainTypes
from great_expectations.execution_engine import (
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.column_aggregate_metric_provider import (
    ColumnAggregateMetricProvider,
)
from great_expectations.expectations.metrics.metric_provider import metric_value


class ColumnSampleValues(ColumnAggregateMetricProvider):
    metric_name = "column.sample_values"

    @metric_value(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        execution_engine: SqlAlchemyExecutionEngine,
        metric_domain_kwargs: dict,
        metric_value_kwargs: dict,
        **kwargs,
    ):
        selectable, _, _ = execution_engine.get_compute_domain(
            domain_kwargs=metric_domain_kwargs, domain_type=MetricDomainTypes.COLUMN
        )
        column = metric_domain_kwargs["column"]
        count = metric_value_kwargs["count"]
        query: sa.Select = sa.select(sa.column(column)).select_from(selectable).limit(count)  # type: ignore[arg-type] # FIXME CoP
        rows = execution_engine.execute_query(query).fetchall()
        # even though we query a single column, the result is a list of length=1 tuples
        return [row[0] for row in rows]
