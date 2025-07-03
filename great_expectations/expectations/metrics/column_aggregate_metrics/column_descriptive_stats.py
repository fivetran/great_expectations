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
from great_expectations.metrics.column.descriptive_stats import DescriptiveStats
from great_expectations.validator.metric_configuration import MetricConfiguration

if TYPE_CHECKING:
    from great_expectations.expectations.expectation_configuration import (
        ExpectationConfiguration,
    )


class ColumnDescriptiveStats(ColumnAggregateMetricProvider):
    metric_name = "column.descriptive_stats"

    @metric_value(engine=PandasExecutionEngine)
    def _pandas(
        cls,
        metrics: dict[str, int],
        **kwargs,
    ) -> DescriptiveStats:
        return DescriptiveStats(
            min=metrics["column.min"],
            max=metrics["column.max"],
            mean=metrics["column.mean"],
            standard_deviation=metrics["column.standard_deviation"],
        )

    @metric_value(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        metrics: dict[str, int],
        **kwargs,
    ) -> DescriptiveStats:
        return DescriptiveStats(
            min=metrics["column.min"],
            max=metrics["column.max"],
            mean=metrics["column.mean"],
            standard_deviation=metrics["column.standard_deviation"],
        )

    @metric_value(engine=SparkDFExecutionEngine)
    def _spark(
        cls,
        metrics: dict[str, int],
        **kwargs,
    ) -> DescriptiveStats:
        return DescriptiveStats(
            min=metrics["column.min"],
            max=metrics["column.max"],
            mean=metrics["column.mean"],
            standard_deviation=metrics["column.standard_deviation"],
        )

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
        dependencies["column.min"] = MetricConfiguration(
            metric_name="column.min",
            metric_domain_kwargs=metric.metric_domain_kwargs,
            metric_value_kwargs=None,
        )
        dependencies["column.max"] = MetricConfiguration(
            metric_name="column.max",
            metric_domain_kwargs=metric.metric_domain_kwargs,
            metric_value_kwargs=None,
        )
        dependencies["column.mean"] = MetricConfiguration(
            metric_name="column.mean",
            metric_domain_kwargs=metric.metric_domain_kwargs,
            metric_value_kwargs=None,
        )
        dependencies["column.standard_deviation"] = MetricConfiguration(
            metric_name="column.standard_deviation",
            metric_domain_kwargs=metric.metric_domain_kwargs,
            metric_value_kwargs=None,
        )
        return dependencies
