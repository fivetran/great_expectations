from __future__ import annotations

from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.execution_engine import (
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.column_aggregate_metric_provider import (
    ColumnAggregateMetricProvider,
    column_aggregate_partial,
)


class ColumnSampleValues(ColumnAggregateMetricProvider):
    metric_name = "column.sample_values"

    @column_aggregate_partial(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(cls, column, count, **kwargs):
        return sa.func.sample(column, count)
