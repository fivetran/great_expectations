from __future__ import annotations

from great_expectations.compatibility.pyspark import functions as F
from great_expectations.execution_engine import (
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.map_metric_provider import (
    MulticolumnMapMetricProvider,
)
from great_expectations.expectations.metrics.map_metric_provider.multicolumn_condition_partial import (  # noqa: E501 # FIXME CoP
    multicolumn_condition_partial,
)


class MulticolumnSumEqual(MulticolumnMapMetricProvider):
    condition_metric_name = "multicolumn_sum.equal"
    condition_domain_keys = (
        "batch_id",
        "table",
        "column_list",
        "row_condition",
        "condition_parser",
        "ignore_row_if",
    )
    condition_value_keys = ("sum_total",)

    @multicolumn_condition_partial(engine=PandasExecutionEngine)
    def _pandas(cls, column_list, **kwargs):
        sum_total = kwargs.get("sum_total")
        row_wise_cond = column_list.sum(axis=1, skipna=False) == sum_total
        return row_wise_cond

    @multicolumn_condition_partial(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(cls, column_list, **kwargs):
        sum_total = kwargs.get("sum_total")
        row_wise_cond = sum(column_list) == sum_total
        return row_wise_cond

    @multicolumn_condition_partial(engine=SparkDFExecutionEngine)
    def _spark(cls, column_list, **kwargs):
        sum_total = kwargs.get("sum_total")
        # Widen each operand to DOUBLE before summing so the addition accumulates in a
        # wide type instead of overflowing an integral/decimal accumulator near its type
        # bounds. Compare against a DOUBLE literal for the same reason. For the value
        # ranges these checks target this preserves the equality result.
        expression = "+".join(
            [f"CAST(COALESCE({column_name}, 0) AS DOUBLE)" for column_name in column_list.columns]
        )
        row_wise_cond = F.expr(expression) == F.lit(sum_total).cast("double")
        return row_wise_cond
