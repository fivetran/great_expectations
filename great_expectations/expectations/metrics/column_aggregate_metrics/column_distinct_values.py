from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

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
    """Metric that counts distinct column values NOT in a provided set.

    This metric pushes the comparison logic to the database, avoiding the need
    to fetch all distinct values into memory. Used for optimizing
    expect_column_distinct_values_to_be_in_set expectations.
    """

    metric_name = "column.distinct_values.not_in_set.count"
    value_keys = ("value_set",)

    @column_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(cls, column: pd.Series, value_set: List[Any], **kwargs) -> int:
        value_set_set = set(value_set)
        return column[~column.isin(value_set_set)].nunique()

    @column_aggregate_partial(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        column: sqlalchemy.ColumnClause,
        value_set: List[Any],
        **kwargs,
    ) -> sqlalchemy.Selectable:
        """Count distinct values NOT in the provided set."""
        if hasattr(column, "is_not"):
            return sa.func.count(
                sa.distinct(sa.case((column.notin_(value_set) & column.is_not(None), column)))
            )
        else:
            return sa.func.count(
                sa.distinct(sa.case((column.notin_(value_set) & column.isnot(None), column)))
            )

    @column_aggregate_partial(engine=SparkDFExecutionEngine)
    def _spark(
        cls,
        column: pyspark.Column,
        value_set: List[Any],
        **kwargs,
    ) -> pyspark.Column:
        """Count distinct values NOT in the provided set."""
        return F.countDistinct(F.when((~column.isin(value_set)) & column.isNotNull(), column))


class ColumnDistinctValuesNotInSet(ColumnAggregateMetricProvider):
    """Metric that returns a sample of distinct column values NOT in a provided set.

    This metric pushes the comparison logic to the database and uses LIMIT to
    restrict the number of values returned. Used for optimizing
    expect_column_distinct_values_to_be_in_set expectations.
    """

    metric_name = "column.distinct_values.not_in_set"
    value_keys = ("value_set", "limit")

    @column_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(
        cls, column: pd.Series, value_set: List[Any], limit: int = 20, **kwargs
    ) -> List[Any]:
        value_set_set = set(value_set)
        not_in_set = column[~column.isin(value_set_set)].dropna().unique()
        return not_in_set[:limit].tolist()

    @metric_value(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        execution_engine: SqlAlchemyExecutionEngine,
        metric_domain_kwargs: Dict[str, str],
        metric_value_kwargs: Dict[str, Any],
        **kwargs,
    ) -> List[Any]:
        """Return a sample of distinct values NOT in the provided set."""
        value_set = metric_value_kwargs.get("value_set", [])
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

        if hasattr(column, "is_not"):
            query = (
                sa.select(column)
                .where(column.is_not(None))
                .where(column.notin_(value_set))
                .distinct()
                .limit(limit)
            )
        else:
            query = (
                sa.select(column)
                .where(column.isnot(None))
                .where(column.notin_(value_set))
                .distinct()
                .limit(limit)
            )

        results = execution_engine.execute_query(  # type: ignore[assignment] # FIXME CoP
            query.select_from(selectable)  # type: ignore[arg-type] # FIXME CoP
        ).fetchall()
        return [row[0] for row in results]

    @metric_value(engine=SparkDFExecutionEngine)
    def _spark(
        cls,
        execution_engine: SparkDFExecutionEngine,
        metric_domain_kwargs: Dict[str, str],
        metric_value_kwargs: Dict[str, Any],
        **kwargs,
    ) -> List[Any]:
        """Return a sample of distinct values NOT in the provided set."""
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

        distinct_values = (
            df.select(F.col(column_name))
            .where(F.col(column_name).isNotNull())
            .where(~F.col(column_name).isin(value_set))
            .distinct()
            .limit(limit)
            .rdd.flatMap(lambda x: x)
            .collect()
        )
        return list(distinct_values)
