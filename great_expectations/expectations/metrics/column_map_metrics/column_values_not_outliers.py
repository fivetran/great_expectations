from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, Optional

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


class _OutlierWindow(NamedTuple):
    """The references a value is measured against, with the multiplier applied.

    `threshold` is how far the window reaches past each reference. The "iqr" method
    extends the two quartiles outward by it to reach Tukey's fences; the "std" method
    holds both references on the mean, so it is simply the distance from the mean at
    which a value becomes an outlier.
    """

    lower_reference: float
    upper_reference: float
    threshold: float


def _get_outlier_window(
    statistics: OutlierStatistics, multiplier: float
) -> Optional[_OutlierWindow]:
    """Return the window to measure against, or None when the column offers no basis.

    A column with no references, or with no spread to measure against - an empty column,
    or a single value under a sample standard deviation - gives no basis for calling
    anything an outlier, so it yields no window and every value is left alone.
    """
    lower_reference, upper_reference, spread = statistics
    if lower_reference is None or upper_reference is None or spread is None:
        return None
    return _OutlierWindow(
        lower_reference=lower_reference,
        upper_reference=upper_reference,
        threshold=multiplier * spread,
    )


class ColumnValuesNotOutliers(ColumnMapMetricProvider):
    """Determine whether column values fall inside the configured method's window.

    The "iqr" method takes Tukey's convention, where a value sitting exactly on a fence is
    inside the window; the "std" method treats a value exactly at the threshold as an
    outlier, which is why a zero threshold there needs its own case - a strict comparison
    against it would otherwise admit nothing at all.
    """

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
        window = _get_outlier_window(statistics, multiplier)
        if window is None:
            return column.notnull()
        if method == IQR_METHOD:
            return (column >= window.lower_reference - window.threshold) & (
                column <= window.upper_reference + window.threshold
            )
        if window.threshold <= 0:
            return column == window.lower_reference
        return (column - window.lower_reference).abs() < window.threshold

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
        window = _get_outlier_window(statistics, multiplier)
        if window is None:
            return sa.true()
        if method == IQR_METHOD:
            return sa.and_(
                column >= window.lower_reference - window.threshold,
                column <= window.upper_reference + window.threshold,
            )
        if window.threshold <= 0:
            return column == window.lower_reference
        return sa.func.abs(column - window.lower_reference) < window.threshold

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
        window = _get_outlier_window(statistics, multiplier)
        if window is None:
            return F.lit(True)
        if method == IQR_METHOD:
            return (column >= F.lit(window.lower_reference - window.threshold)) & (
                column <= F.lit(window.upper_reference + window.threshold)
            )
        if window.threshold <= 0:
            return column == F.lit(window.lower_reference)
        return F.abs(column - F.lit(window.lower_reference)) < F.lit(window.threshold)

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
