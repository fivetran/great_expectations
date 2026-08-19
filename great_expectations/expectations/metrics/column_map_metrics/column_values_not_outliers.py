from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from great_expectations.compatibility.pyspark import functions as F
from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.metric_function_types import (
    MetricPartialFunctionTypeSuffixes,
)
from great_expectations.execution_engine import (
    ExecutionEngine,
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.column_aggregate_metrics.column_outlier_statistics import (  # noqa: E501
    IQR_METHOD,
    OutlierStatistics,
    validate_method,
)
from great_expectations.expectations.metrics.map_metric_provider import (
    ColumnMapMetricProvider,
    column_condition_partial,
)
from great_expectations.validator.metric_configuration import MetricConfiguration

if TYPE_CHECKING:
    import pandas as pd

    from great_expectations.expectations.expectation_configuration import (
        ExpectationConfiguration,
    )

_OUTLIER_STATISTICS_METRIC_NAME = "column.outlier_statistics"


def _get_threshold(statistics: OutlierStatistics, multiplier: float) -> Optional[float]:
    """Return the distance at which a value becomes an outlier, or None if unmeasurable.

    A column with no center, or with no spread to measure against - an empty column, or a
    single value under a sample standard deviation - gives no basis for calling anything
    an outlier, so it yields no threshold and every value is left alone.
    """
    center, spread = statistics
    if center is None or spread is None:
        return None
    return multiplier * spread


class ColumnValuesNotOutliers(ColumnMapMetricProvider):
    """Determine whether column values fall within the configured outlier threshold."""

    condition_metric_name = "column_values.not_outliers"
    condition_value_keys = ("method", "multiplier")
    filter_column_isnull = True

    @column_condition_partial(engine=PandasExecutionEngine)
    def _pandas(
        cls,
        column,
        _metrics,
        method: str = IQR_METHOD,
        multiplier: float = 1.5,
        **kwargs,
    ) -> pd.Series:
        validate_method(method)
        statistics: OutlierStatistics = _metrics[_OUTLIER_STATISTICS_METRIC_NAME]
        threshold = _get_threshold(statistics, multiplier)
        if threshold is None:
            return column.notnull()
        if threshold <= 0:
            return column == statistics.center
        return (column - statistics.center).abs() < threshold

    @column_condition_partial(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        column,
        _metrics,
        method: str = IQR_METHOD,
        multiplier: float = 1.5,
        **kwargs,
    ):
        validate_method(method)
        statistics: OutlierStatistics = _metrics[_OUTLIER_STATISTICS_METRIC_NAME]
        threshold = _get_threshold(statistics, multiplier)
        if threshold is None:
            return sa.true()
        if threshold <= 0:
            return column == statistics.center
        return sa.func.abs(column - statistics.center) < threshold

    @column_condition_partial(engine=SparkDFExecutionEngine)
    def _spark(
        cls,
        column,
        _metrics,
        method: str = IQR_METHOD,
        multiplier: float = 1.5,
        **kwargs,
    ):
        validate_method(method)
        statistics: OutlierStatistics = _metrics[_OUTLIER_STATISTICS_METRIC_NAME]
        threshold = _get_threshold(statistics, multiplier)
        if threshold is None:
            return F.lit(True)
        if threshold <= 0:
            return column == F.lit(statistics.center)
        return F.abs(column - F.lit(statistics.center)) < F.lit(threshold)

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

        condition_metric_name = (
            f"{cls.condition_metric_name}.{MetricPartialFunctionTypeSuffixes.CONDITION.value}"
        )
        if metric.metric_name != condition_metric_name:
            return dependencies

        method = metric.metric_value_kwargs.get("method", IQR_METHOD)
        validate_method(method)
        dependencies[_OUTLIER_STATISTICS_METRIC_NAME] = MetricConfiguration(
            metric_name=_OUTLIER_STATISTICS_METRIC_NAME,
            metric_domain_kwargs=metric.metric_domain_kwargs,
            metric_value_kwargs={"method": method},
        )
        return dependencies
