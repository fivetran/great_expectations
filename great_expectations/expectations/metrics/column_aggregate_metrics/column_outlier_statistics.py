from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, NamedTuple, Optional

from great_expectations.compatibility.pyspark import functions as F
from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.core.metric_domain_types import MetricDomainTypes
from great_expectations.execution_engine import (
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.execution_engine.sqlalchemy_dialect import GXSqlDialect
from great_expectations.expectations.metrics.column_aggregate_metric_provider import (
    ColumnAggregateMetricProvider,
    column_aggregate_value,
)
from great_expectations.expectations.metrics.metric_provider import metric_value
from great_expectations.expectations.metrics.util import (
    get_dbms_compatible_metric_domain_kwargs,
)

if TYPE_CHECKING:
    import pandas as pd

IQR_METHOD = "iqr"
STD_METHOD = "std"
SUPPORTED_METHODS = (IQR_METHOD, STD_METHOD)

_FIRST_QUARTILE = 0.25
_THIRD_QUARTILE = 0.75
_QUARTILES = (_FIRST_QUARTILE, _THIRD_QUARTILE)
_MINIMUM_SAMPLE_SIZE_FOR_STANDARD_DEVIATION = 2


class OutlierStatistics(NamedTuple):
    """The references and spread a column's window of acceptable values is built from.

    The window runs from `lower_reference - multiplier * spread` to
    `upper_reference + multiplier * spread`. The two methods differ in where the
    references sit: "iqr" puts them on the first and third quartiles, so the window is
    Tukey's fences and follows a skewed column out to whichever side is longer; "std"
    puts both on the mean, so the window is symmetric.

    Any field is None when the batch cannot supply it: an empty column has no references,
    and a sample standard deviation is undefined for fewer than two values.
    """

    lower_reference: Optional[float]
    upper_reference: Optional[float]
    spread: Optional[float]

    @classmethod
    def symmetric(cls, center: Optional[float], spread: Optional[float]) -> OutlierStatistics:
        """Build a window centered on a single statistic, with both references on it."""
        return cls(lower_reference=center, upper_reference=center, spread=spread)


def validate_method(method: str) -> None:
    if method not in SUPPORTED_METHODS:
        raise NotImplementedError(f"method {method!r} has not been implemented")


def _to_float(value: Any) -> Optional[float]:
    """Normalize an engine-native statistic to a finite float, or None if there is none.

    Engines return statistics in whatever type the column carries - notably Decimal for
    SQL numeric columns and for Spark DecimalType - and those do not mix with the Python
    floats the threshold arithmetic uses.

    None means the batch has no statistic to offer: an empty column, or a sample standard
    deviation of fewer than two values. NaN and infinity are folded into that, because
    arithmetic on either silently reverses the comparison - `abs(x - inf) < inf` is False
    for every finite value, which would report every row an outlier and none of the
    infinite ones.

    A value that is not a number at all is a different situation, and raises: it means the
    column is not numeric, and reporting it as "no statistic" would pass every row and
    leave the Expectation permanently, silently green.
    """
    if value is None:
        return None
    try:
        converted = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(  # noqa: TRY003 # FIXME CoP
            "Cannot detect outliers in a non-numerical column: the column statistic "
            f"{value!r} could not be read as a number."
        ) from error
    return converted if math.isfinite(converted) else None


def _spread_between(lower: Optional[float], upper: Optional[float]) -> Optional[float]:
    if lower is None or upper is None:
        return None
    return upper - lower


def _get_sql_compute_domain(
    execution_engine: SqlAlchemyExecutionEngine,
    metric_domain_kwargs: dict,
    batch_columns_list: list,
):
    metric_domain_kwargs = get_dbms_compatible_metric_domain_kwargs(
        metric_domain_kwargs=metric_domain_kwargs,
        batch_columns_list=batch_columns_list,
    )
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

    # Rank on the same numeric scale the interpolation reads, not on the raw column.
    # The algorithm assumes the value at rank k is the k-th smallest *number*; ordering by
    # the raw column instead would rank a text column lexically ("100" before "2") and
    # then interpolate over numerically-cast values at those ranks.
    numeric_column = sa.cast(column, sa.Float)
    ordered_values = (
        sa.select(
            numeric_column.label(value_label),
            sa.func.row_number().over(order_by=numeric_column.asc()).label(row_number_label),
            sa.func.count(column).over().label(count_label),
        )
        .where(column.is_not(None))
        .select_from(selectable)
        .subquery()
    )

    value = ordered_values.c[value_label]
    row_number = ordered_values.c[row_number_label]
    row_count = ordered_values.c[count_label]

    percentile_expressions = []
    for index, quantile in enumerate(quantiles):
        position = quantile * (row_count - 1) + 1
        aggregate_position = sa.func.max(position)
        lower_value = sa.func.max(sa.case((row_number <= position, value), else_=None))
        upper_value = sa.func.min(sa.case((row_number >= position, value), else_=None))
        # The rank of the value below the target position - the floor of the position,
        # expressed as an aggregate over the ranks themselves. Deriving it this way keeps
        # the arithmetic exact on every dialect: CAST(position AS INTEGER) truncates on
        # SQLite but rounds half away from zero on MySQL, which would drive the fraction
        # negative and extrapolate below the lower value instead of interpolating.
        lower_position = sa.func.max(sa.case((row_number <= position, row_number), else_=None))
        interpolation_fraction = aggregate_position - lower_position
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
    return tuple(_to_float(value) for value in row)


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
    return tuple(_to_float(value) for value in row)


def _get_sqlite_mean_and_standard_deviation(
    *,
    column,
    selectable,
    execution_engine: SqlAlchemyExecutionEngine,
) -> OutlierStatistics:
    """Compute the sample standard deviation on SQLite, which has no STDDEV_SAMP.

    Uses the same two-pass form as the SQLite override of `column.standard_deviation`:
    the mean is resolved first, then the deviations are squared against it. The one-pass
    identity `sum(x**2) - n * mean**2` is avoided because it cancels catastrophically once
    the mean is large relative to the spread, which silently reports a spread of zero.
    """
    numeric_column = sa.cast(column, sa.Float)
    row = execution_engine.execute_query(
        sa.select(sa.func.count(column), sa.func.avg(numeric_column)).select_from(selectable)
    ).fetchone()
    if row is None or not row[0]:
        return OutlierStatistics.symmetric(center=None, spread=None)

    count = int(row[0])
    mean = _to_float(row[1])
    if mean is None or count < _MINIMUM_SAMPLE_SIZE_FOR_STANDARD_DEVIATION:
        return OutlierStatistics.symmetric(center=mean, spread=None)

    deviation = numeric_column - mean
    row = execution_engine.execute_query(
        sa.select(sa.func.sqrt(sa.func.sum(deviation * deviation) / (count - 1.0))).select_from(
            selectable
        )
    ).fetchone()
    return OutlierStatistics.symmetric(
        center=mean, spread=None if row is None else _to_float(row[0])
    )


def _get_sql_mean_and_standard_deviation(
    *,
    column,
    selectable,
    execution_engine: SqlAlchemyExecutionEngine,
) -> OutlierStatistics:
    dialect_name = execution_engine.dialect_name
    if dialect_name == GXSqlDialect.SQLITE:
        return _get_sqlite_mean_and_standard_deviation(
            column=column,
            selectable=selectable,
            execution_engine=execution_engine,
        )

    numeric_column = sa.cast(column, sa.Float)
    # STDDEV_SAMP is standard SQL and every dialect that reaches here has it, including
    # the ones outside SUPPORTED_DATA_SOURCES - ClickHouse and Trino both accept it, and
    # both were checked. Only SQL Server renames it and only SQLite lacks it, so this is
    # deliberately a fall-through rather than an allow-list: the percentile path needs one
    # because PERCENTILE_CONT genuinely differs in syntax per dialect, and this does not.
    if dialect_name == GXSqlDialect.SQL_SERVER:
        standard_deviation = sa.func.stdev(numeric_column)
    else:
        standard_deviation = sa.func.stddev_samp(numeric_column)

    row = execution_engine.execute_query(
        sa.select(sa.func.avg(numeric_column), standard_deviation).select_from(selectable)
    ).fetchone()
    if row is None:
        return OutlierStatistics.symmetric(center=None, spread=None)
    return OutlierStatistics.symmetric(center=_to_float(row[0]), spread=_to_float(row[1]))


def _spark_column_reference(column_name: str) -> str:
    """Render a column name for use inside a Spark SQL expression.

    A dotted column name already arrives backticked from the `table.columns` metric, so
    it is passed through untouched; anything else is quoted here, doubling any backtick
    the name itself carries.
    """
    if column_name.startswith("`") and column_name.endswith("`") and len(column_name) >= 2:  # noqa: PLR2004
        return column_name
    escaped_column_name = column_name.replace("`", "``")
    return f"`{escaped_column_name}`"


def _spark_exact_percentile(column_name: str, quantile: float):
    """Build Spark's exact, linearly interpolated percentile aggregate.

    `F.percentile_approx` returns an element of the dataset rather than an interpolated
    value at any accuracy, which would put Spark's quartiles on a different definition
    from pandas' and from PERCENTILE_CONT. The SQL `percentile` aggregate interpolates and
    predates the Python-side `F.percentile` wrapper, which only exists on pyspark 3.5+.
    """
    return F.expr(f"percentile({_spark_column_reference(column_name)}, {quantile})")


class ColumnOutlierStatistics(ColumnAggregateMetricProvider):
    """Return the references and spread the configured outlier method measures against.

    Every statistic comes from a single pass over the column so that a validation does not
    scan - and, on the dialects that need a sorted subquery, sort - the column twice.
    """

    metric_name = "column.outlier_statistics"
    value_keys = ("method",)
    filter_column_isnull = True

    @column_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(cls, column: pd.Series, method: str, **kwargs) -> OutlierStatistics:
        validate_method(method)
        if method == IQR_METHOD:
            # `Series.quantile` is used in preference to `scipy.stats.iqr`, which routes
            # through `numpy.percentile` and rejects object-dtype columns outright. Both
            # interpolate linearly, so the numbers agree wherever scipy accepts the input.
            first_quartile = _to_float(column.quantile(_FIRST_QUARTILE))
            third_quartile = _to_float(column.quantile(_THIRD_QUARTILE))
            return OutlierStatistics(
                lower_reference=first_quartile,
                upper_reference=third_quartile,
                spread=_spread_between(first_quartile, third_quartile),
            )
        return OutlierStatistics.symmetric(
            center=_to_float(column.mean()), spread=_to_float(column.std())
        )

    @metric_value(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        execution_engine: SqlAlchemyExecutionEngine,
        metric_domain_kwargs: dict,
        metric_value_kwargs: dict,
        metrics: dict[str, Any],
        runtime_configuration: dict,
    ) -> OutlierStatistics:
        method = metric_value_kwargs["method"]
        validate_method(method)
        selectable, column = _get_sql_compute_domain(
            execution_engine=execution_engine,
            metric_domain_kwargs=metric_domain_kwargs,
            batch_columns_list=metrics["table.columns"],
        )

        if method == STD_METHOD:
            return _get_sql_mean_and_standard_deviation(
                column=column,
                selectable=selectable,
                execution_engine=execution_engine,
            )

        first_quartile, third_quartile = _get_sql_percentiles(
            column=column,
            quantiles=_QUARTILES,
            selectable=selectable,
            execution_engine=execution_engine,
        )
        return OutlierStatistics(
            lower_reference=first_quartile,
            upper_reference=third_quartile,
            spread=_spread_between(first_quartile, third_quartile),
        )

    @metric_value(engine=SparkDFExecutionEngine)
    def _spark(
        cls,
        execution_engine: SparkDFExecutionEngine,
        metric_domain_kwargs: dict,
        metric_value_kwargs: dict,
        metrics: dict[str, Any],
        runtime_configuration: dict,
    ) -> OutlierStatistics:
        method = metric_value_kwargs["method"]
        validate_method(method)
        metric_domain_kwargs = get_dbms_compatible_metric_domain_kwargs(
            metric_domain_kwargs=metric_domain_kwargs,
            batch_columns_list=metrics["table.columns"],
        )
        df, _, accessor_domain_kwargs = execution_engine.get_compute_domain(
            domain_kwargs=metric_domain_kwargs, domain_type=MetricDomainTypes.COLUMN
        )
        column_name = accessor_domain_kwargs["column"]
        column = F.col(column_name)

        # Every aggregate below ignores nulls, so no explicit null filter is needed.
        if method == STD_METHOD:
            row = df.agg(F.mean(column), F.stddev_samp(column)).collect()[0]
            return OutlierStatistics.symmetric(center=_to_float(row[0]), spread=_to_float(row[1]))

        row = df.agg(
            *(_spark_exact_percentile(column_name, quantile) for quantile in _QUARTILES)
        ).collect()[0]
        first_quartile, third_quartile = (_to_float(value) for value in row)
        return OutlierStatistics(
            lower_reference=first_quartile,
            upper_reference=third_quartile,
            spread=_spread_between(first_quartile, third_quartile),
        )
