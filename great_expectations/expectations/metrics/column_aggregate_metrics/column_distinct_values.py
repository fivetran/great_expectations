from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Union

import numpy as np
import pandas as pd
from dateutil.parser import parse

from great_expectations.compatibility.not_imported import is_version_greater_or_equal
from great_expectations.compatibility.pyspark import (
    functions as F,
)
from great_expectations.compatibility.sqlalchemy import (
    __version__ as SQLALCHEMY_VERSION,
)
from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.metric_domain_types import MetricDomainTypes
from great_expectations.execution_engine import (
    ExecutionEngine,
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.column_aggregate_metric_provider import (
    ColumnAggregateMetricProvider,
    column_aggregate_partial,
    column_aggregate_value,
)
from great_expectations.expectations.metrics.metric_provider import metric_value
from great_expectations.validator.metric_configuration import MetricConfiguration

if TYPE_CHECKING:
    from great_expectations.compatibility import pyspark, sqlalchemy
    from great_expectations.expectations.expectation_configuration import (
        ExpectationConfiguration,
    )

# SQLAlchemy 1.4+ uses is_not() instead of isnot()
_SQLALCHEMY_1_4_OR_GREATER = SQLALCHEMY_VERSION is not None and is_version_greater_or_equal(
    SQLALCHEMY_VERSION, "1.4.0"
)


# Type alias for scalar values that can appear in columns or value sets
ScalarValue = Union[str, int, float, bool, datetime.date, datetime.datetime, np.datetime64, None]


def _coerce_scalar_to_datetime64(v: ScalarValue) -> ScalarValue:
    """Coerce a single value to numpy.datetime64 via pd.Timestamp."""
    if isinstance(v, np.datetime64):
        return v
    if isinstance(v, (str, int, float, datetime.date, datetime.datetime)):
        try:
            return pd.Timestamp(v).to_datetime64()
        except (ValueError, TypeError):
            pass
    return v


def _coerce_scalar_to_datetime(v: ScalarValue, target_is_date_only: bool) -> ScalarValue:
    """Coerce a string value to datetime.date or datetime.datetime."""
    if not isinstance(v, str):
        return v
    try:
        return parse(v).date() if target_is_date_only else parse(v)
    except (ValueError, TypeError):
        return v


def _coerce_value_set_to_column_type(
    column_set: Set[ScalarValue], value_set: List[ScalarValue]
) -> Set[ScalarValue]:
    """Coerce value_set items to match the type of values in column_set.

    This handles cases like comparing string dates to datetime.date objects,
    and numpy.datetime64 values from pandas datetime columns.
    Used by Pandas metrics where we have access to actual column values.

    Args:
        column_set: Set of values from the column (determines target type)
        value_set: List of expected values to coerce

    Returns:
        Set of values coerced to match the column's type
    """
    if not column_set or not value_set:
        return set(value_set) if value_set else set()

    sample_value = next(iter(column_set))

    # numpy.datetime64 (from pandas 3.x datetime columns) doesn't hash consistently
    # with Python datetime types, so coerce value_set items to numpy.datetime64.
    if isinstance(sample_value, np.datetime64):
        return {_coerce_scalar_to_datetime64(v) for v in value_set}

    if isinstance(sample_value, (datetime.date, datetime.datetime)):
        target_is_date_only = not isinstance(sample_value, datetime.datetime)
        return {_coerce_scalar_to_datetime(v, target_is_date_only) for v in value_set}

    return set(value_set)


def _coerce_value_set_for_sql(value_set: List[ScalarValue]) -> List[ScalarValue]:
    """Coerce value_set string values that look like dates to datetime.date objects.

    This is needed for databases like BigQuery that require exact type matching.
    For SQLAlchemy metrics where we don't have access to actual column values.

    Args:
        value_set: List of expected values, may contain date strings

    Returns:
        List with date strings converted to datetime.date objects
    """
    if not value_set:
        return []

    coerced: List[ScalarValue] = []
    for v in value_set:
        if isinstance(v, str):
            # Try to parse as date (common format: YYYY-MM-DD)
            try:
                coerced.append(parse(v).date())
            except (ValueError, TypeError):
                coerced.append(v)
        else:
            coerced.append(v)
    return coerced


class ColumnDistinctValues(ColumnAggregateMetricProvider):
    metric_name = "column.distinct_values"

    @column_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(cls, column: pd.Series, **kwargs) -> Set[Any]:
        return set(column.unique())

    @metric_value(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        execution_engine: SqlAlchemyExecutionEngine,
        metric_domain_kwargs: Dict[str, str],
        **kwargs,
    ) -> Set[Any]:
        """
        Past implementations of column.distinct_values depended on column.value_counts.
        This was causing performance issues due to the complex query used in column.value_counts and subsequent
        in-memory operations.
        """  # noqa: E501 # FIXME CoP
        selectable: sqlalchemy.Selectable
        accessor_domain_kwargs: Dict[str, str]
        (
            selectable,
            _,
            accessor_domain_kwargs,
        ) = execution_engine.get_compute_domain(metric_domain_kwargs, MetricDomainTypes.COLUMN)
        column_name: str = accessor_domain_kwargs["column"]
        column: sqlalchemy.ColumnClause = sa.column(column_name)

        distinct_values: List[sqlalchemy.Row]
        if _SQLALCHEMY_1_4_OR_GREATER:
            distinct_values = execution_engine.execute_query(  # type: ignore[assignment] # FIXME CoP
                sa.select(column).where(column.is_not(None)).distinct().select_from(selectable)  # type: ignore[arg-type] # FIXME CoP
            ).fetchall()
        else:
            distinct_values = execution_engine.execute_query(  # type: ignore[assignment] # FIXME CoP
                sa.select(column).where(column.isnot(None)).distinct().select_from(selectable)  # type: ignore[arg-type] # FIXME CoP
            ).fetchall()
        # Vectorized operation is not faster here due to overhead of converting to and from numpy array  # noqa: E501 # FIXME CoP
        return {row[0] for row in distinct_values}

    @metric_value(engine=SparkDFExecutionEngine)
    def _spark(
        cls,
        execution_engine: SparkDFExecutionEngine,
        metric_domain_kwargs: Dict[str, str],
        **kwargs,
    ) -> Set[Any]:
        """
        Past implementations of column.distinct_values depended on column.value_counts.
        This was causing performance issues due to the complex query used in column.value_counts and subsequent
        in-memory operations.
        """  # noqa: E501 # FIXME CoP
        df: pyspark.DataFrame
        accessor_domain_kwargs: Dict[str, str]
        (
            df,
            _,
            accessor_domain_kwargs,
        ) = execution_engine.get_compute_domain(metric_domain_kwargs, MetricDomainTypes.COLUMN)
        column_name: str = accessor_domain_kwargs["column"]
        distinct_values: List[pyspark.Row] = (
            df.select(F.col(column_name))
            .distinct()
            .where(F.col(column_name).isNotNull())
            .rdd.flatMap(lambda x: x)
            .collect()
        )
        return set(distinct_values)


class ColumnDistinctValuesCount(ColumnAggregateMetricProvider):
    metric_name = "column.distinct_values.count"

    @column_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(cls, column: pd.Series, **kwargs) -> int:
        return column.nunique()

    @column_aggregate_partial(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        column: sqlalchemy.ColumnClause,
        **kwargs,
    ) -> sqlalchemy.Selectable:
        """
        Past implementations of column.distinct_values.count depended on column.value_counts and column.distinct_values.
        This was causing performance issues due to the complex query used in column.value_counts and subsequent
        in-memory operations.
        """  # noqa: E501 # FIXME CoP
        return sa.func.count(sa.distinct(column))

    @column_aggregate_partial(engine=SparkDFExecutionEngine)
    def _spark(
        cls,
        column: pyspark.Column,
        **kwargs,
    ) -> pyspark.Column:
        """
        Past implementations of column.distinct_values.count depended on column.value_counts and column.distinct_values.
        This was causing performance issues due to the complex query used in column.value_counts and subsequent
        in-memory operations.
        """  # noqa: E501 # FIXME CoP
        return F.countDistinct(column)


class ColumnDistinctValuesCountUnderThreshold(ColumnAggregateMetricProvider):
    metric_name = "column.distinct_values.count.under_threshold"
    condition_keys = ("threshold",)

    @column_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(cls, column: pd.Series, threshold: int, **kwargs) -> bool:
        return column.nunique() < threshold

    @metric_value(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        metric_value_kwargs: Dict[str, int],
        metrics: Dict[str, int],
        **kwargs,
    ) -> bool:
        return metrics["column.distinct_values.count"] < metric_value_kwargs["threshold"]

    @metric_value(engine=SparkDFExecutionEngine)
    def _spark(
        cls,
        metric_value_kwargs: Dict[str, int],
        metrics: Dict[str, int],
        **kwargs,
    ) -> bool:
        return metrics["column.distinct_values.count"] < metric_value_kwargs["threshold"]

    @classmethod
    @override
    def _get_evaluation_dependencies(
        cls,
        metric: MetricConfiguration,
        configuration: Optional[ExpectationConfiguration] = None,
        execution_engine: Optional[ExecutionEngine] = None,
        runtime_configuration: Optional[Dict] = None,
    ):
        """Returns a dictionary of given metric names and their corresponding configuration,
        specifying the metric types and their respective domains"""
        dependencies: dict = super()._get_evaluation_dependencies(
            metric=metric,
            configuration=configuration,
            execution_engine=execution_engine,
            runtime_configuration=runtime_configuration,
        )
        if metric.metric_name == "column.distinct_values.count.under_threshold":
            dependencies["column.distinct_values.count"] = MetricConfiguration(
                metric_name="column.distinct_values.count",
                metric_domain_kwargs=metric.metric_domain_kwargs,
                metric_value_kwargs=None,
            )
        return dependencies
