from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from dateutil.parser import parse

from great_expectations.compatibility.pyspark import (
    functions as F,
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
    import pandas as pd

    from great_expectations.compatibility import pyspark, sqlalchemy
    from great_expectations.expectations.expectation_configuration import (
        ExpectationConfiguration,
    )


def _coerce_value_set_to_column_type(column_set: Set[Any], value_set: List[Any]) -> Set[Any]:
    """Coerce value_set items to match the type of values in column_set.

    This handles cases like comparing string dates to datetime.date objects.
    Used by Pandas metrics where we have access to actual column values.
    """
    if not column_set or not value_set:
        return set(value_set) if value_set else set()

    # Get a sample value from the column to determine its type
    sample_value = next(iter(column_set))

    # If column contains datetime types and value_set contains strings, try to parse
    if isinstance(sample_value, (datetime.date, datetime.datetime)):
        coerced_set: Set[Any] = set()
        for v in value_set:
            if isinstance(v, str):
                try:
                    if isinstance(sample_value, datetime.date) and not isinstance(
                        sample_value, datetime.datetime
                    ):
                        coerced_set.add(parse(v).date())
                    else:
                        coerced_set.add(parse(v))
                except (ValueError, TypeError):
                    coerced_set.add(v)
            else:
                coerced_set.add(v)
        return coerced_set

    return set(value_set)


def _coerce_value_set_for_sql(value_set: List[Any]) -> List[Any]:
    """Coerce value_set string values that look like dates to datetime.date objects.

    This is needed for databases like BigQuery that require exact type matching.
    For SQLAlchemy metrics where we don't have access to actual column values.
    """
    if not value_set:
        return []

    coerced: List[Any] = []
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
        if hasattr(column, "is_not"):
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
            if hasattr(column, "is_not"):
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
        elif hasattr(column, "is_not"):
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
        cls, column: pd.Series, value_set: List[Any], limit: int = 20, **kwargs
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
        limit = metric_value_kwargs.get("limit", 20)

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
            if hasattr(column, "is_not"):
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
        elif hasattr(column, "is_not"):
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
        limit = metric_value_kwargs.get("limit", 20)

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


class ColumnDistinctValuesMissingFromSetCount(ColumnAggregateMetricProvider):
    """Metric that returns count of expected values missing from the column.

    Used for expect_column_distinct_values_to_contain_set to determine pass/fail
    without fetching all distinct values.
    """

    metric_name = "column.distinct_values.missing_from_set.count"
    value_keys = ("value_set",)

    @column_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(cls, column: pd.Series, value_set: List[Any], **kwargs) -> int:
        column_set = set(column.dropna().unique())
        expected_set = _coerce_value_set_to_column_type(column_set, value_set)
        missing = expected_set - column_set
        return len(missing)

    @metric_value(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        execution_engine: SqlAlchemyExecutionEngine,
        metric_domain_kwargs: Dict[str, str],
        metric_value_kwargs: Dict[str, Any],
        **kwargs,
    ) -> int:
        """Count values in the expected set that are missing from the column."""
        value_set = _coerce_value_set_for_sql(metric_value_kwargs.get("value_set", []))
        if not value_set:
            return 0

        selectable: sqlalchemy.Selectable
        accessor_domain_kwargs: Dict[str, str]
        (
            selectable,
            _,
            accessor_domain_kwargs,
        ) = execution_engine.get_compute_domain(metric_domain_kwargs, MetricDomainTypes.COLUMN)
        column_name: str = accessor_domain_kwargs["column"]
        column: sqlalchemy.ColumnClause = sa.column(column_name)

        # Count how many expected values exist in the column
        if hasattr(column, "is_not"):
            query = (
                sa.select(sa.func.count(sa.distinct(column)))
                .where(column.is_not(None))
                .where(column.in_(value_set))
                .select_from(selectable)  # type: ignore[arg-type] # FIXME CoP
            )
        else:
            query = (
                sa.select(sa.func.count(sa.distinct(column)))
                .where(column.isnot(None))
                .where(column.in_(value_set))
                .select_from(selectable)  # type: ignore[arg-type] # FIXME CoP
            )

        found_count = execution_engine.execute_query(query).scalar() or 0
        return len(value_set) - found_count

    @metric_value(engine=SparkDFExecutionEngine)
    def _spark(
        cls,
        execution_engine: SparkDFExecutionEngine,
        metric_domain_kwargs: Dict[str, str],
        metric_value_kwargs: Dict[str, Any],
        **kwargs,
    ) -> int:
        """Count values in the expected set that are missing from the column."""
        value_set = metric_value_kwargs.get("value_set", [])
        if not value_set:
            return 0

        df: pyspark.DataFrame
        accessor_domain_kwargs: Dict[str, str]
        (
            df,
            _,
            accessor_domain_kwargs,
        ) = execution_engine.get_compute_domain(metric_domain_kwargs, MetricDomainTypes.COLUMN)
        column_name: str = accessor_domain_kwargs["column"]

        # Count how many expected values exist in the column
        found_count = (
            (
                df.where(F.col(column_name).isNotNull())
                .where(F.col(column_name).isin(value_set))
                .select(F.countDistinct(F.col(column_name)))
                .collect()[0][0]
            )
            or 0
        )

        return len(value_set) - found_count


class ColumnDistinctValuesMissingFromSet(ColumnAggregateMetricProvider):
    """Metric that returns values in the expected set that are missing from the column.

    Used for expect_column_distinct_values_to_contain_set to check which
    required values are not present in the column.
    """

    metric_name = "column.distinct_values.missing_from_set"
    value_keys = ("value_set", "limit")

    @column_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(
        cls, column: pd.Series, value_set: List[Any], limit: int = 20, **kwargs
    ) -> List[Any]:
        column_set = set(column.dropna().unique())
        expected_set = _coerce_value_set_to_column_type(column_set, value_set)
        missing = list(expected_set - column_set)
        return missing[:limit]

    @metric_value(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        execution_engine: SqlAlchemyExecutionEngine,
        metric_domain_kwargs: Dict[str, str],
        metric_value_kwargs: Dict[str, Any],
        **kwargs,
    ) -> List[Any]:
        """Return values in the expected set that are missing from the column."""
        value_set = _coerce_value_set_for_sql(metric_value_kwargs.get("value_set", []))
        limit = metric_value_kwargs.get("limit", 20)

        selectable: sqlalchemy.Selectable
        accessor_domain_kwargs: Dict[str, str]
        (
            selectable,
            _,
            accessor_domain_kwargs,
        ) = execution_engine.get_compute_domain(metric_domain_kwargs, MetricDomainTypes.COLUMN)
        column_name: str = accessor_domain_kwargs["column"]
        column: sqlalchemy.ColumnClause = sa.column(column_name)

        # Get distinct values in the column
        if hasattr(column, "is_not"):
            column_values_query = (
                sa.select(column).where(column.is_not(None)).distinct().select_from(selectable)  # type: ignore[arg-type] # FIXME CoP
            )
        else:
            column_values_query = (
                sa.select(column).where(column.isnot(None)).distinct().select_from(selectable)  # type: ignore[arg-type] # FIXME CoP
            )

        column_values_result = execution_engine.execute_query(column_values_query).fetchall()
        column_values_set = {row[0] for row in column_values_result}

        # Find missing values
        missing = [v for v in value_set if v not in column_values_set]
        return missing[:limit]

    @metric_value(engine=SparkDFExecutionEngine)
    def _spark(
        cls,
        execution_engine: SparkDFExecutionEngine,
        metric_domain_kwargs: Dict[str, str],
        metric_value_kwargs: Dict[str, Any],
        **kwargs,
    ) -> List[Any]:
        """Return values in the expected set that are missing from the column."""
        value_set = metric_value_kwargs.get("value_set", [])
        limit = metric_value_kwargs.get("limit", 20)

        df: pyspark.DataFrame
        accessor_domain_kwargs: Dict[str, str]
        (
            df,
            _,
            accessor_domain_kwargs,
        ) = execution_engine.get_compute_domain(metric_domain_kwargs, MetricDomainTypes.COLUMN)
        column_name: str = accessor_domain_kwargs["column"]

        # Get distinct values in the column
        column_values = (
            df.select(F.col(column_name))
            .where(F.col(column_name).isNotNull())
            .distinct()
            .rdd.flatMap(lambda x: x)
            .collect()
        )
        column_values_set = set(column_values)

        # Find missing values
        missing = [v for v in value_set if v not in column_values_set]
        return missing[:limit]
