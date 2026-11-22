from __future__ import annotations

from sqlalchemy import String, cast, func

from great_expectations.execution_engine import (
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.map_metric_provider import (
    ColumnMapMetricProvider,
    column_condition_partial,
)


class ColumnValuesNotBlank(ColumnMapMetricProvider):
    condition_metric_name = "column_values.not_blank"
    filter_column_isnull = False

    @column_condition_partial(engine=PandasExecutionEngine)
    def _pandas(cls, column, **kwargs):
        non_null = ~column.isnull()
        non_blank = column.astype("string").str.strip().ne("")
        return non_null & non_blank

    @column_condition_partial(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(cls, column, **kwargs):
        trimmed_column = func.trim(cast(column, String))
        return column.is_not(None) & (trimmed_column != "")

    @column_condition_partial(engine=SparkDFExecutionEngine)
    def _spark(cls, column, **kwargs):
        return column.isNotNull() & column.cast("string").rlike(r"\S")
