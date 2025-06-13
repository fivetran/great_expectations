from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from great_expectations.compatibility.typing_extensions import override
from great_expectations.execution_engine import (
    ExecutionEngine,
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.column_aggregate_metric_provider import (
    ColumnAggregateMetricProvider,
)
from great_expectations.expectations.metrics.metric_provider import metric_value
from great_expectations.validator.metric_configuration import MetricConfiguration

if TYPE_CHECKING:
    from great_expectations.expectations.expectation_configuration import (
        ExpectationConfiguration,
    )


def nonnull_proportion(_metrics):
    """Computes the proportion of non-null values out of all values"""
    total_values = _metrics.get("table.row_count")
    nonnull_count = _metrics.get("column.non_null_count")

    # Ensuring that we do not divide by 0, returning 0 if all values are nulls
    if total_values > 0:
        return nonnull_count / total_values
    else:
        return 0


class ColumnNonNullProportion(ColumnAggregateMetricProvider):
    metric_name = "column.non_null_proportion"

    @metric_value(engine=PandasExecutionEngine)
    def _pandas(*args, metrics, **kwargs):
        return nonnull_proportion(metrics)

    @metric_value(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(*args, metrics, **kwargs):
        return nonnull_proportion(metrics)

    @metric_value(engine=SparkDFExecutionEngine)
    def _spark(*args, metrics, **kwargs):
        return nonnull_proportion(metrics)

    @classmethod
    @override
    def _get_evaluation_dependencies(
        cls,
        metric: MetricConfiguration,
        configuration: Optional[ExpectationConfiguration] = None,
        execution_engine: Optional[ExecutionEngine] = None,
        runtime_configuration: Optional[dict] = None,
    ):
        dependencies: dict = super()._get_evaluation_dependencies(
            metric=metric,
            configuration=configuration,
            execution_engine=execution_engine,
            runtime_configuration=runtime_configuration,
        )

        dependencies["column.non_null_count"] = MetricConfiguration(
            metric_name="column.non_null_count",
            metric_domain_kwargs=metric.metric_domain_kwargs,
        )

        return dependencies
