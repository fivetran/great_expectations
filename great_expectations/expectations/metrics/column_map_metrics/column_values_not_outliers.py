from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Optional

from great_expectations.compatibility.pyspark import functions as F
from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.metric_domain_types import MetricDomainTypes
from great_expectations.core.metric_function_types import (
    MetricPartialFunctionTypeSuffixes,
)
from great_expectations.execution_engine import (
    ExecutionEngine,
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.execution_engine.sqlalchemy_dialect import GXSqlDialect
from great_expectations.expectations.metrics.column_aggregate_metric_provider import (
    ColumnAggregateMetricProvider,
    column_aggregate_partial,
    column_aggregate_value,
)
from great_expectations.expectations.metrics.map_metric_provider import (
    ColumnMapMetricProvider,
    column_condition_partial,
)
from great_expectations.expectations.metrics.metric_provider import metric_value
from great_expectations.validator.metric_configuration import MetricConfiguration

if TYPE_CHECKING:
    import pandas as pd

    from great_expectations.expectations.expectation_configuration import (
        ExpectationConfiguration,
    )

_IQR_METHOD = "iqr"
_STD_METHOD = "std"
_SUPPORTED_METHODS = (_IQR_METHOD, _STD_METHOD)
_SPARK_PERCENTILE_ACCURACY = 100_000
_MINIMUM_SAMPLE_SIZE_FOR_STANDARD_DEVIATION = 2


def _validate_method(method: str) -> None:
    if method not in _SUPPORTED_METHODS:
        raise NotImplementedError(f"method {method!r} has not been implemented")


def _is_missing_statistic(value: Any) -> bool:
    if value is None:
        return True
    try:
        return math.isnan(float(value))
    except (TypeError, ValueError):
        return False


def _get_sql_compute_domain(
    execution_engine: SqlAlchemyExecutionEngine,
    metric_domain_kwargs: dict,
):
    nonnull_domain_kwargs = execution_engine.add_column_row_condition(metric_domain_kwargs)
    selectable, _, accessor_domain_kwargs = execution_engine.get_compute_domain(
        nonnull_domain_kwargs,
        domain_type=MetricDomainTypes.COLUMN,
    )
    if isinstance(selectable, sa.sql.Select):
        selectable = selectable.subquery()
    return selectable, sa.column(accessor_domain_kwargs["column"])


def _get_window_linear_percentiles(
    *,
    column,
    quantiles: tuple[float, ...],
    selectable,
    execution_engine: SqlAlchemyExecutionEngine,
) -> tuple[Optional[float], ...]:
    """Calculate continuous percentiles for SQL dialects without PERCENTILE_CONT."""
    value_label = "_gx_outlier_value"
    row_number_label = "_gx_outlier_row_number"
    count_label = "_gx_outlier_count"

    ordered_values = (
        sa.select(
            column.label(value_label),
            sa.func.row_number().over(order_by=column.asc()).label(row_number_label),
            sa.func.count(column).over().label(count_label),
        )
        .where(column.is_not(None))
        .select_from(selectable)
        .subquery()
    )

    value = sa.cast(ordered_values.c[value_label], sa.Float)
    row_number = ordered_values.c[row_number_label]
    row_count = ordered_values.c[count_label]

    percentile_expressions = []
    for index, quantile in enumerate(quantiles):
        position = quantile * (row_count - 1) + 1
        aggregate_position = sa.func.max(position)
        lower_value = sa.func.max(sa.case((row_number <= position, value), else_=None))
        upper_value = sa.func.min(sa.case((row_number >= position, value), else_=None))
        interpolation_fraction = aggregate_position - sa.cast(aggregate_position, sa.Integer)
        percentile_expressions.append(
            (lower_value + interpolation_fraction * (upper_value - lower_value)).label(
                f"_gx_outlier_quantile_{index}"
            )
        )

    row = execution_engine.execute_query(
        sa.select(*percentile_expressions).select_from(ordered_values)
    ).fetchone()
    if row is None:
        return tuple(None for _ in quantiles)
    return tuple(None if value is None else float(value) for value in row)


def _get_sql_percentiles(
    *,
    column,
    quantiles: tuple[float, ...],
    selectable,
    execution_engine: SqlAlchemyExecutionEngine,
) -> tuple[Optional[float], ...]:
    dialect_name = execution_engine.dialect_name
    percentile_expressions: list[Any]

    if dialect_name in (GXSqlDialect.SQLITE, GXSqlDialect.MYSQL):
        return _get_window_linear_percentiles(
            column=column,
            quantiles=quantiles,
            selectable=selectable,
            execution_engine=execution_engine,
        )

    if dialect_name == GXSqlDialect.SQL_SERVER:
        percentile_expressions = [
            sa.func.percentile_cont(quantile).within_group(column.asc()).over()
            for quantile in quantiles
        ]
        query = sa.select(*percentile_expressions).select_from(selectable).limit(1)
    elif dialect_name == GXSqlDialect.BIGQUERY:
        percentile_expressions = [
            sa.func.percentile_cont(column, quantile).over() for quantile in quantiles
        ]
        query = sa.select(*percentile_expressions).select_from(selectable).limit(1)
    elif dialect_name in (
        GXSqlDialect.POSTGRESQL,
        GXSqlDialect.REDSHIFT,
        GXSqlDialect.SNOWFLAKE,
        GXSqlDialect.DATABRICKS,
    ):
        percentile_expressions = [
            sa.func.percentile_cont(quantile).within_group(column.asc()) for quantile in quantiles
        ]
        query = sa.select(*percentile_expressions).select_from(selectable)
    else:
        raise NotImplementedError(
            f"IQR outlier detection is not implemented for SQL dialect {dialect_name!r}"
        )

    row = execution_engine.execute_query(query).fetchone()
    if row is None:
        return tuple(None for _ in quantiles)
    return tuple(None if value is None else float(value) for value in row)


def _get_sql_standard_deviation_statistics(
    *,
    column,
    selectable,
    execution_engine: SqlAlchemyExecutionEngine,
) -> tuple[Optional[float], Optional[float]]:
    numeric_column = sa.cast(column, sa.Float)
    row = execution_engine.execute_query(
        sa.select(
            sa.func.count(column),
            sa.func.avg(numeric_column),
            sa.func.sum(numeric_column * numeric_column),
        ).select_from(selectable)
    ).fetchone()

    if row is None or row[0] == 0:
        return None, None

    count = int(row[0])
    mean = float(row[1])
    if count < _MINIMUM_SAMPLE_SIZE_FOR_STANDARD_DEVIATION or row[2] is None:
        return mean, None

    sum_of_squares = float(row[2])
    variance = (sum_of_squares - count * mean * mean) / (count - 1)
    # Floating-point cancellation can produce a tiny negative value for a
    # constant or near-constant column.
    standard_deviation = math.sqrt(max(variance, 0.0))
    return mean, standard_deviation


def _get_sql_outlier_statistic(
    *,
    execution_engine: SqlAlchemyExecutionEngine,
    metric_domain_kwargs: dict,
    method: str,
    statistic: str,
) -> Optional[float]:
    _validate_method(method)
    selectable, column = _get_sql_compute_domain(
        execution_engine=execution_engine,
        metric_domain_kwargs=metric_domain_kwargs,
    )

    if method == _STD_METHOD:
        mean, standard_deviation = _get_sql_standard_deviation_statistics(
            column=column,
            selectable=selectable,
            execution_engine=execution_engine,
        )
        return mean if statistic == "center" else standard_deviation

    first_quartile, median, third_quartile = _get_sql_percentiles(
        column=column,
        quantiles=(0.25, 0.5, 0.75),
        selectable=selectable,
        execution_engine=execution_engine,
    )
    if statistic == "center":
        return median
    if first_quartile is None or third_quartile is None:
        return None
    return third_quartile - first_quartile


class ColumnOutlierCenter(ColumnAggregateMetricProvider):
    """Return the center used by the configured outlier detection method."""

    metric_name = "column.outlier_center"
    value_keys = ("method",)
    filter_column_isnull = True

    @column_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(cls, column, method, **kwargs):
        _validate_method(method)
        if method == _IQR_METHOD:
            return column.median()
        return column.mean()

    @metric_value(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        execution_engine: SqlAlchemyExecutionEngine,
        metric_domain_kwargs: dict,
        metric_value_kwargs: dict,
        metrics: dict[str, Any],
        runtime_configuration: dict,
    ):
        return _get_sql_outlier_statistic(
            execution_engine=execution_engine,
            metric_domain_kwargs=metric_domain_kwargs,
            method=metric_value_kwargs["method"],
            statistic="center",
        )

    @column_aggregate_partial(engine=SparkDFExecutionEngine)
    def _spark(cls, column, method, **kwargs):
        _validate_method(method)
        if method == _IQR_METHOD:
            return F.percentile_approx(column, 0.5, _SPARK_PERCENTILE_ACCURACY)
        return F.mean(column)


class ColumnOutlierSpread(ColumnAggregateMetricProvider):
    """Return the IQR or sample standard deviation used for outlier detection."""

    metric_name = "column.outlier_spread"
    value_keys = ("method",)
    filter_column_isnull = True

    @column_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(cls, column, method, **kwargs):
        _validate_method(method)
        if method == _IQR_METHOD:
            from scipy import stats

            return stats.iqr(column, nan_policy="omit")
        return column.std()

    @metric_value(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        execution_engine: SqlAlchemyExecutionEngine,
        metric_domain_kwargs: dict,
        metric_value_kwargs: dict,
        metrics: dict[str, Any],
        runtime_configuration: dict,
    ):
        return _get_sql_outlier_statistic(
            execution_engine=execution_engine,
            metric_domain_kwargs=metric_domain_kwargs,
            method=metric_value_kwargs["method"],
            statistic="spread",
        )

    @column_aggregate_partial(engine=SparkDFExecutionEngine)
    def _spark(cls, column, method, **kwargs):
        _validate_method(method)
        if method == _IQR_METHOD:
            first_quartile = F.percentile_approx(column, 0.25, _SPARK_PERCENTILE_ACCURACY)
            third_quartile = F.percentile_approx(column, 0.75, _SPARK_PERCENTILE_ACCURACY)
            return third_quartile - first_quartile
        return F.stddev_samp(column)


class ColumnValuesNotOutliers(ColumnMapMetricProvider):
    """Determine whether column values fall within the configured outlier threshold."""

    condition_metric_name = "column_values.not_outliers"
    condition_value_keys = ("method", "multiplier")

    @column_condition_partial(engine=PandasExecutionEngine)
    def _pandas(
        cls,
        column,
        _metrics,
        method: str = _IQR_METHOD,
        multiplier: float = 1.5,
        **kwargs,
    ) -> pd.Series:
        _validate_method(method)
        center = _metrics["column.outlier_center"]
        spread = _metrics["column.outlier_spread"]
        if _is_missing_statistic(center) or _is_missing_statistic(spread):
            return column.notnull() & False
        return (column - center).abs() < multiplier * spread

    @column_condition_partial(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        column,
        _metrics,
        method: str = _IQR_METHOD,
        multiplier: float = 1.5,
        **kwargs,
    ):
        _validate_method(method)
        center = _metrics["column.outlier_center"]
        spread = _metrics["column.outlier_spread"]
        if _is_missing_statistic(center) or _is_missing_statistic(spread):
            return sa.false()
        return sa.func.abs(column - center) < multiplier * spread

    @column_condition_partial(engine=SparkDFExecutionEngine)
    def _spark(
        cls,
        column,
        _metrics,
        method: str = _IQR_METHOD,
        multiplier: float = 1.5,
        **kwargs,
    ):
        _validate_method(method)
        center = _metrics["column.outlier_center"]
        spread = _metrics["column.outlier_spread"]
        if _is_missing_statistic(center) or _is_missing_statistic(spread):
            return F.lit(False)
        return F.abs(column - F.lit(center)) < F.lit(multiplier * spread)

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

        method = metric.metric_value_kwargs.get("method", _IQR_METHOD)
        _validate_method(method)
        statistic_value_kwargs = {"method": method}
        dependencies["column.outlier_center"] = MetricConfiguration(
            metric_name="column.outlier_center",
            metric_domain_kwargs=metric.metric_domain_kwargs,
            metric_value_kwargs=statistic_value_kwargs,
        )
        dependencies["column.outlier_spread"] = MetricConfiguration(
            metric_name="column.outlier_spread",
            metric_domain_kwargs=metric.metric_domain_kwargs,
            metric_value_kwargs=statistic_value_kwargs,
        )
        return dependencies
