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
        missing = [v for v in value_set if v not in column_set]
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
