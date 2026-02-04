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


class ColumnDistinctValuesMissingFromColumnCount(ColumnAggregateMetricProvider):
    """Metric that returns count of expected values missing from the column.

    Used for expect_column_distinct_values_to_contain_set to determine pass/fail
    without fetching all distinct values.
    """

    metric_name = "column.distinct_values.missing_from_column.count"
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
        if _SQLALCHEMY_1_4_OR_GREATER:
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


class ColumnDistinctValuesMissingFromColumn(ColumnAggregateMetricProvider):
    """Metric that returns values in the expected set that are missing from the column.

    Used for expect_column_distinct_values_to_contain_set to check which
    required values are not present in the column.
    """

    metric_name = "column.distinct_values.missing_from_column"
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

        # Get distinct values in the column
        if _SQLALCHEMY_1_4_OR_GREATER:
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
        limit = metric_value_kwargs.get("limit") or MAX_DISTINCT_VALUES

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
