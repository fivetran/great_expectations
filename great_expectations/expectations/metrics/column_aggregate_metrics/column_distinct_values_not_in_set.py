from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from great_expectations.compatibility.not_imported import is_version_greater_or_equal
from great_expectations.compatibility.pyspark import (
    functions as F,
)
from great_expectations.compatibility.sqlalchemy import (
    __version__ as SQLALCHEMY_VERSION,
)
from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.constants import MAX_DISTINCT_VALUES
from great_expectations.core.metric_domain_types import MetricDomainTypes
from great_expectations.execution_engine import (
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.column_aggregate_metric_provider import (
    ColumnAggregateMetricProvider,
    column_aggregate_value,
)
from great_expectations.expectations.metrics.column_aggregate_metrics.column_distinct_values import (  # noqa: E501
    _coerce_value_set_for_sql,
    _coerce_value_set_to_column_type,
)
from great_expectations.expectations.metrics.metric_provider import metric_value

if TYPE_CHECKING:
    import pandas as pd

    from great_expectations.compatibility import pyspark, sqlalchemy

# SQLAlchemy 1.4+ uses is_not() instead of isnot()
_SQLALCHEMY_1_4_OR_GREATER = SQLALCHEMY_VERSION is not None and is_version_greater_or_equal(
    SQLALCHEMY_VERSION, "1.4.0"
)


class ColumnDistinctValuesNotInSetCount(ColumnAggregateMetricProvider):
    """Metric that returns count of column values NOT in the expected set.

    Used for expect_column_distinct_values_to_be_in_set to determine pass/fail
    without fetching all distinct values.
    """

    metric_name = "column.distinct_values.not_in_set.count"
    value_keys = ("value_set",)

    @column_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(cls, column: pd.Series, value_set: List[Any], **kwargs) -> int:
        column_set = set(column.dropna().unique())
        expected_set = _coerce_value_set_to_column_type(column_set, value_set)
        return len(column_set - expected_set)

    @metric_value(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        execution_engine: SqlAlchemyExecutionEngine,
        metric_domain_kwargs: Dict[str, str],
        metric_value_kwargs: Dict[str, Any],
        **kwargs,
    ) -> int:
        """Count distinct values in column that are NOT in the expected set."""
        value_set = _coerce_value_set_for_sql(metric_value_kwargs.get("value_set", []))

        selectable: sqlalchemy.Selectable
        accessor_domain_kwargs: Dict[str, str]
        (
            selectable,
            _,
            accessor_domain_kwargs,
        ) = execution_engine.get_compute_domain(metric_domain_kwargs, MetricDomainTypes.COLUMN)
        column_name: str = accessor_domain_kwargs["column"]
        column: sqlalchemy.ColumnClause = sa.column(column_name)

        # Count distinct values NOT in the provided set
        if value_set:
            if _SQLALCHEMY_1_4_OR_GREATER:
                query = (
                    sa.select(sa.func.count(sa.distinct(column)))
                    .where(column.is_not(None))
                    .where(column.notin_(value_set))
                    .select_from(selectable)  # type: ignore[arg-type] # FIXME CoP
                )
            else:
                query = (
                    sa.select(sa.func.count(sa.distinct(column)))
                    .where(column.isnot(None))
                    .where(column.notin_(value_set))
                    .select_from(selectable)  # type: ignore[arg-type] # FIXME CoP
                )
        # Empty value_set means all non-null values are violations
        elif _SQLALCHEMY_1_4_OR_GREATER:
            query = (
                sa.select(sa.func.count(sa.distinct(column)))
                .where(column.is_not(None))
                .select_from(selectable)  # type: ignore[arg-type] # FIXME CoP
            )
        else:
            query = (
                sa.select(sa.func.count(sa.distinct(column)))
                .where(column.isnot(None))
                .select_from(selectable)  # type: ignore[arg-type] # FIXME CoP
            )

        result = execution_engine.execute_query(query).scalar()
        return result or 0

    @metric_value(engine=SparkDFExecutionEngine)
    def _spark(
        cls,
        execution_engine: SparkDFExecutionEngine,
        metric_domain_kwargs: Dict[str, str],
        metric_value_kwargs: Dict[str, Any],
        **kwargs,
    ) -> int:
        """Count distinct values in column that are NOT in the expected set."""
        value_set = metric_value_kwargs.get("value_set", [])

        df: pyspark.DataFrame
        accessor_domain_kwargs: Dict[str, str]
        (
            df,
            _,
            accessor_domain_kwargs,
        ) = execution_engine.get_compute_domain(metric_domain_kwargs, MetricDomainTypes.COLUMN)
        column_name: str = accessor_domain_kwargs["column"]

        # Filter to values NOT in the set and count distinct
        filtered_df = df.where(F.col(column_name).isNotNull())
        if value_set:
            filtered_df = filtered_df.where(~F.col(column_name).isin(value_set))

        result = filtered_df.select(F.countDistinct(F.col(column_name))).collect()[0][0]
        return result or 0


class ColumnDistinctValuesNotInSet(ColumnAggregateMetricProvider):
    """Metric that returns sample of column values NOT in the expected set.

    Used for expect_column_distinct_values_to_be_in_set to report violations
    without fetching all distinct values.
    """

    metric_name = "column.distinct_values.not_in_set"
    value_keys = ("value_set", "limit")

    @column_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(
        cls,
        column: pd.Series,
        value_set: List[Any],
        limit: int = MAX_DISTINCT_VALUES,
        **kwargs,
    ) -> List[Any]:
        column_set = set(column.dropna().unique())
        expected_set = _coerce_value_set_to_column_type(column_set, value_set)
        not_in_set = list(column_set - expected_set)
        # Sort for deterministic results, handling mixed types gracefully
        try:
            not_in_set = sorted(not_in_set)
        except TypeError:
            pass  # Mixed types can't be sorted, return unsorted
        return not_in_set[:limit]

    @metric_value(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        execution_engine: SqlAlchemyExecutionEngine,
        metric_domain_kwargs: Dict[str, str],
        metric_value_kwargs: Dict[str, Any],
        **kwargs,
    ) -> List[Any]:
        """Return sample of distinct values in column that are NOT in the expected set."""
        value_set = _coerce_value_set_for_sql(metric_value_kwargs.get("value_set", []))
        limit = metric_value_kwargs.get("limit") or MAX_DISTINCT_VALUES

        selectable: sqlalchemy.Selectable
        accessor_domain_kwargs: Dict[str, str]
        (
            selectable,
            _,
            accessor_domain_kwargs,
        ) = execution_engine.get_compute_domain(metric_domain_kwargs, MetricDomainTypes.COLUMN)
        column_name: str = accessor_domain_kwargs["column"]
        column: sqlalchemy.ColumnClause = sa.column(column_name)

        # Get distinct values NOT in the provided set (with limit)
        if value_set:
            if _SQLALCHEMY_1_4_OR_GREATER:
                query = (
                    sa.select(column)
                    .where(column.is_not(None))
                    .where(column.notin_(value_set))
                    .distinct()
                    .limit(limit)
                    .select_from(selectable)  # type: ignore[arg-type] # FIXME CoP
                )
            else:
                query = (
                    sa.select(column)
                    .where(column.isnot(None))
                    .where(column.notin_(value_set))
                    .distinct()
                    .limit(limit)
                    .select_from(selectable)  # type: ignore[arg-type] # FIXME CoP
                )
        # Empty value_set means all non-null values are violations
        elif _SQLALCHEMY_1_4_OR_GREATER:
            query = (
                sa.select(column)
                .where(column.is_not(None))
                .distinct()
                .limit(limit)
                .select_from(selectable)  # type: ignore[arg-type] # FIXME CoP
            )
        else:
            query = (
                sa.select(column)
                .where(column.isnot(None))
                .distinct()
                .limit(limit)
                .select_from(selectable)  # type: ignore[arg-type] # FIXME CoP
            )

        results = execution_engine.execute_query(query).fetchall()
        return [row[0] for row in results]

    @metric_value(engine=SparkDFExecutionEngine)
    def _spark(
        cls,
        execution_engine: SparkDFExecutionEngine,
        metric_domain_kwargs: Dict[str, str],
        metric_value_kwargs: Dict[str, Any],
        **kwargs,
    ) -> List[Any]:
        """Return sample of distinct values in column that are NOT in the expected set."""
        value_set = metric_value_kwargs.get("value_set", [])
        limit = metric_value_kwargs.get("limit") or MAX_DISTINCT_VALUES

        df: pyspark.DataFrame
        accessor_domain_kwargs: Dict[str, str]
        (
            df,
            _,
            accessor_domain_kwargs,
        ) = execution_engine.get_compute_domain(metric_domain_kwargs, MetricDomainTypes.COLUMN)
        column_name: str = accessor_domain_kwargs["column"]

        # Filter to values NOT in the set
        filtered_df = df.where(F.col(column_name).isNotNull())
        if value_set:
            filtered_df = filtered_df.where(~F.col(column_name).isin(value_set))

        # Get distinct values with limit
        results = (
            filtered_df.select(F.col(column_name))
            .distinct()
            .limit(limit)
            .rdd.flatMap(lambda x: x)
            .collect()
        )
        return list(results)
