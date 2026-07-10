from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

import numpy as np

from great_expectations.compatibility.pyspark import functions as F
from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.metric_domain_types import MetricDomainTypes
from great_expectations.core.util import get_sql_dialect_floating_point_infinity_value
from great_expectations.execution_engine import (
    ExecutionEngine,
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.column_map_metrics.column_values_between import (
    _column_type_from_metrics,
    _raise_if_invalid_column_type,
    _should_reject_incomparable_spark_column_type,
)
from great_expectations.expectations.metrics.metric_provider import (
    MetricProvider,
    metric_value,
)
from great_expectations.validator.metric_configuration import MetricConfiguration

if TYPE_CHECKING:
    from great_expectations.expectations.expectation_configuration import (
        ExpectationConfiguration,
    )


class ColumnValuesBetweenCount(MetricProvider):
    """This metric is an aggregate helper for rare cases."""

    metric_name = "column_values.between.count"
    value_keys = (
        "min_value",
        "max_value",
        "strict_min",
        "strict_max",
    )

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
        # The Spark path resolves the column's type from this metric to decide whether an
        # incomparable string<->numeric comparison must be rejected under ANSI mode.
        table_domain_kwargs: dict = {
            k: v for k, v in metric.metric_domain_kwargs.items() if k != "column"
        }
        dependencies["table.column_types"] = MetricConfiguration(
            metric_name="table.column_types",
            metric_domain_kwargs=table_domain_kwargs,
            metric_value_kwargs={
                "include_nested": True,
            },
        )
        return dependencies

    @metric_value(engine=PandasExecutionEngine)
    def _pandas(  # noqa: C901, PLR0912 # FIXME CoP
        cls,
        execution_engine: PandasExecutionEngine,
        metric_domain_kwargs: dict,
        metric_value_kwargs: dict,
        metrics: Dict[str, Any],
        runtime_configuration: dict,
    ):
        min_value = metric_value_kwargs.get("min_value")
        max_value = metric_value_kwargs.get("max_value")
        strict_min = metric_value_kwargs.get("strict_min")
        strict_max = metric_value_kwargs.get("strict_max")
        if min_value is None and max_value is None:
            raise ValueError("min_value and max_value cannot both be None")  # noqa: TRY003 # FIXME CoP

        if min_value is not None and max_value is not None and min_value > max_value:
            raise ValueError("min_value cannot be greater than max_value")  # noqa: TRY003 # FIXME CoP

        (
            df,
            _compute_domain_kwargs,
            accessor_domain_kwargs,
        ) = execution_engine.get_compute_domain(
            domain_kwargs=metric_domain_kwargs, domain_type=MetricDomainTypes.COLUMN
        )
        val = df[accessor_domain_kwargs["column"]]

        if min_value is not None and max_value is not None:
            if strict_min and strict_max:
                series = min_value < val < max_value
            elif strict_min:
                series = min_value < val <= max_value
            elif strict_max:
                series = min_value <= val < max_value
            else:
                series = min_value <= val <= max_value

        elif min_value is None and max_value is not None:
            if strict_max:
                series = val < max_value
            else:
                series = val <= max_value

        elif min_value is not None and max_value is None:
            if strict_min:
                series = min_value < val
            else:
                series = min_value <= val
        else:
            raise ValueError("unable to parse domain and value kwargs")  # noqa: TRY003 # FIXME CoP

        return np.count_nonzero(series)

    @metric_value(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(  # noqa: C901, PLR0912 # FIXME CoP
        cls,
        execution_engine: SqlAlchemyExecutionEngine,
        metric_domain_kwargs: dict,
        metric_value_kwargs: dict,
        metrics: Dict[str, Any],
        runtime_configuration: dict,
    ):
        min_value = metric_value_kwargs.get("min_value")
        max_value = metric_value_kwargs.get("max_value")
        strict_min = metric_value_kwargs.get("strict_min")
        strict_max = metric_value_kwargs.get("strict_max")
        if min_value is not None and max_value is not None and min_value > max_value:
            raise ValueError("min_value cannot be greater than max_value")  # noqa: TRY003 # FIXME CoP

        if min_value is None and max_value is None:
            raise ValueError("min_value and max_value cannot both be None")  # noqa: TRY003 # FIXME CoP
        dialect_name = execution_engine.engine.dialect.name.lower()

        if (
            min_value
            == get_sql_dialect_floating_point_infinity_value(schema="api_np", negative=True)
        ) or (
            min_value
            == get_sql_dialect_floating_point_infinity_value(schema="api_cast", negative=True)
        ):
            min_value = get_sql_dialect_floating_point_infinity_value(
                schema=dialect_name, negative=True
            )

        if (
            min_value
            == get_sql_dialect_floating_point_infinity_value(schema="api_np", negative=False)
        ) or (
            min_value
            == get_sql_dialect_floating_point_infinity_value(schema="api_cast", negative=False)
        ):
            min_value = get_sql_dialect_floating_point_infinity_value(
                schema=dialect_name, negative=False
            )

        if (
            max_value
            == get_sql_dialect_floating_point_infinity_value(schema="api_np", negative=True)
        ) or (
            max_value
            == get_sql_dialect_floating_point_infinity_value(schema="api_cast", negative=True)
        ):
            max_value = get_sql_dialect_floating_point_infinity_value(
                schema=dialect_name, negative=True
            )

        if (
            max_value
            == get_sql_dialect_floating_point_infinity_value(schema="api_np", negative=False)
        ) or (
            max_value
            == get_sql_dialect_floating_point_infinity_value(schema="api_cast", negative=False)
        ):
            max_value = get_sql_dialect_floating_point_infinity_value(
                schema=dialect_name, negative=False
            )

        (
            selectable,
            _compute_domain_kwargs,
            accessor_domain_kwargs,
        ) = execution_engine.get_compute_domain(
            domain_kwargs=metric_domain_kwargs, domain_type=MetricDomainTypes.COLUMN
        )
        column = sa.column(accessor_domain_kwargs["column"])  # type: ignore[var-annotated] # FIXME CoP

        if min_value is None:
            if strict_max:
                condition = column < max_value
            else:
                condition = column <= max_value

        elif max_value is None:
            if strict_min:
                condition = column > min_value
            else:
                condition = column >= min_value

        else:  # noqa: PLR5501 # FIXME CoP
            if strict_min and strict_max:
                condition = sa.and_(column > min_value, column < max_value)
            elif strict_min:
                condition = sa.and_(column > min_value, column <= max_value)
            elif strict_max:
                condition = sa.and_(column >= min_value, column < max_value)
            else:
                condition = sa.and_(column >= min_value, column <= max_value)

        return execution_engine.execute_query(
            sa.select(sa.func.count()).select_from(selectable).where(condition)  # type: ignore[arg-type] # FIXME CoP
        ).scalar()

    @metric_value(engine=SparkDFExecutionEngine)
    def _spark(  # noqa: C901, PLR0912 # FIXME CoP
        cls,
        execution_engine: SparkDFExecutionEngine,
        metric_domain_kwargs: dict,
        metric_value_kwargs: dict,
        metrics: Dict[str, Any],
        runtime_configuration: dict,
    ):
        min_value = metric_value_kwargs.get("min_value")
        max_value = metric_value_kwargs.get("max_value")
        strict_min = metric_value_kwargs.get("strict_min")
        strict_max = metric_value_kwargs.get("strict_max")
        if min_value is not None and max_value is not None and min_value > max_value:
            raise ValueError("min_value cannot be greater than max_value")  # noqa: TRY003 # FIXME CoP

        if min_value is None and max_value is None:
            raise ValueError("min_value and max_value cannot both be None")  # noqa: TRY003 # FIXME CoP

        (
            df,
            _compute_domain_kwargs,
            accessor_domain_kwargs,
        ) = execution_engine.get_compute_domain(
            domain_kwargs=metric_domain_kwargs, domain_type=MetricDomainTypes.COLUMN
        )
        column_name = accessor_domain_kwargs["column"]
        column = F.col(column_name)

        # Reject incomparable column types up front so an implicit string<->numeric
        # comparison does not surface as an opaque engine error under ANSI mode. The type
        # is resolved from the metric rather than df.schema[...] so a column name that
        # Spark SQL would resolve case-insensitively does not raise a KeyError.
        if _should_reject_incomparable_spark_column_type(min_value, max_value):
            column_type = _column_type_from_metrics(metrics, column_name)
            _raise_if_invalid_column_type(column_type)

        if min_value is not None and max_value is not None and min_value > max_value:
            raise ValueError("min_value cannot be greater than max_value")  # noqa: TRY003 # FIXME CoP

        if min_value is None and max_value is None:
            raise ValueError("min_value and max_value cannot both be None")  # noqa: TRY003 # FIXME CoP

        if min_value is None:
            if strict_max:
                condition = column < F.lit(max_value)
            else:
                condition = column <= F.lit(max_value)

        elif max_value is None:
            if strict_min:
                condition = column > F.lit(min_value)
            else:
                condition = column >= F.lit(min_value)

        else:  # noqa: PLR5501 # FIXME CoP
            if strict_min and strict_max:
                condition = (column > F.lit(min_value)) & (column < F.lit(max_value))
            elif strict_min:
                condition = (column > F.lit(min_value)) & (column <= F.lit(max_value))
            elif strict_max:
                condition = (column >= F.lit(min_value)) & (column < F.lit(max_value))
            else:
                condition = (column >= F.lit(min_value)) & (column <= F.lit(max_value))

        return df.filter(condition).count()
