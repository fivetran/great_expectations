from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional, cast

from great_expectations.compatibility import pyspark, sqlalchemy
from great_expectations.core.metric_domain_types import MetricDomainTypes
from great_expectations.exceptions import GreatExpectationsError
from great_expectations.execution_engine import (
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.metric_provider import metric_value
from great_expectations.expectations.metrics.table_metric_provider import (
    TableMetricProvider,
)
from great_expectations.expectations.metrics.util import get_sqlalchemy_column_metadata

if TYPE_CHECKING:
    from great_expectations.execution_engine.sqlalchemy_batch_data import SqlAlchemyBatchData

logger = logging.getLogger(__name__)


class ColumnTypes(TableMetricProvider):
    metric_name = "table.column_types"
    value_keys = ("include_nested",)
    default_kwarg_values = {"include_nested": True}

    @metric_value(engine=PandasExecutionEngine)
    def _pandas(
        cls,
        execution_engine: PandasExecutionEngine,
        metric_domain_kwargs: dict,
        metric_value_kwargs: dict,
        metrics: Dict[str, Any],
        runtime_configuration: dict,
    ):
        df, _, _ = execution_engine.get_compute_domain(
            metric_domain_kwargs, domain_type=MetricDomainTypes.TABLE
        )
        return [
            {"name": name, "type": dtype}
            for (name, dtype) in zip(df.columns, df.dtypes, strict=False)
        ]

    @metric_value(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        execution_engine: SqlAlchemyExecutionEngine,
        metric_domain_kwargs: dict,
        metric_value_kwargs: dict,
        metrics: Dict[str, Any],
        runtime_configuration: dict,
    ):
        batch_id: Optional[str] = metric_domain_kwargs.get("batch_id")
        if batch_id is None:
            if execution_engine.batch_manager.active_batch_data_id is not None:
                batch_id = execution_engine.batch_manager.active_batch_data_id
            else:
                raise GreatExpectationsError(  # noqa: TRY003 # FIXME CoP
                    "batch_id could not be determined from domain kwargs and no active_batch_data is loaded into the "  # noqa: E501 # FIXME CoP
                    "execution engine"
                )

        batch_data: SqlAlchemyBatchData = cast(
            "SqlAlchemyBatchData",
            execution_engine.batch_manager.batch_data_cache.get(batch_id),
        )
        if batch_data is None:
            raise GreatExpectationsError(  # noqa: TRY003 # FIXME CoP
                "the requested batch is not available; please load the batch into the execution engine."  # noqa: E501 # FIXME CoP
            )

        return _get_sqlalchemy_column_metadata(execution_engine, batch_data)

    @metric_value(engine=SparkDFExecutionEngine)
    def _spark(
        cls,
        execution_engine: SparkDFExecutionEngine,
        metric_domain_kwargs: dict,
        metric_value_kwargs: dict,
        metrics: Dict[str, Any],
        runtime_configuration: dict,
    ):
        df, _, _ = execution_engine.get_compute_domain(
            metric_domain_kwargs, domain_type=MetricDomainTypes.TABLE
        )
        spark_column_metadata = _get_spark_column_metadata(
            df.schema, include_nested=metric_value_kwargs["include_nested"]
        )
        return spark_column_metadata


def _get_sqlalchemy_column_metadata(
    execution_engine: SqlAlchemyExecutionEngine, batch_data: SqlAlchemyBatchData
):
    """
    Helper to obtain column metadata for SqlAlchemyExecutionEngine batches.

    For Redshift, many configurations encode fully-qualified names like
    \"schema.table\" in `source_table_name` with `source_schema_name` left as None.
    We normalize this into separate schema/table components so that
    `get_sqlalchemy_column_metadata` can reflect correctly via the dialect.
    """
    dialect_name = getattr(execution_engine.dialect, "name", "").lower()

    logger.debug(f"_get_sqlalchemy_column_metadata called for dialect: {dialect_name}")
    logger.debug(
        f"  source_table_name: {batch_data.source_table_name}, "
        f"source_schema_name: {batch_data.source_schema_name}"
    )

    # Special handling for Redshift: normalize "schema.table" into separate parts.
    if dialect_name == "redshift":
        table_selectable: str | sqlalchemy.TextClause

        # Check selectable type before accessing .name attribute
        # TextClause objects don't have .name attribute
        if sqlalchemy.TextClause and isinstance(batch_data.selectable, sqlalchemy.TextClause):  # type: ignore[truthy-function] # FIXME CoP
            # Custom query: pass through as-is
            table_selectable = batch_data.selectable
            schema_name = None
            result = get_sqlalchemy_column_metadata(
                execution_engine=execution_engine,
                table_selectable=table_selectable,  # type: ignore[arg-type]
                schema_name=schema_name,
            )
            logger.debug(
                f"Returned {len(result) if result else 0} columns for Redshift TextClause query"
            )
            return result

        # For Table or other selectable types, safely access .name
        if sqlalchemy.Table and isinstance(batch_data.selectable, sqlalchemy.Table):  # type: ignore[truthy-function] # FIXME CoP
            raw_table_name = batch_data.source_table_name or batch_data.selectable.name
            schema_name = batch_data.source_schema_name or batch_data.selectable.schema
        else:
            # Fallback for other selectable types
            raw_table_name = batch_data.source_table_name or (
                batch_data.selectable.name if hasattr(batch_data.selectable, "name") else None
            )
            schema_name = batch_data.source_schema_name or (
                batch_data.selectable.schema if hasattr(batch_data.selectable, "schema") else None
            )

        if raw_table_name is None:
            raise ValueError(  # noqa: TRY003 # FIXME CoP
                "Could not determine table name from batch_data for Redshift dialect"
            )

        if isinstance(raw_table_name, str) and schema_name is None and "." in raw_table_name:
            schema_name, table_name = raw_table_name.split(".", 1)
            logger.debug(
                f"Split '{raw_table_name}' into schema='{schema_name}', table='{table_name}'"
            )
        else:
            table_name = raw_table_name
            logger.debug(f"Using table='{table_name}', schema='{schema_name}'")

        table_selectable = table_name

        result = get_sqlalchemy_column_metadata(
            execution_engine=execution_engine,
            table_selectable=table_selectable,  # type: ignore[arg-type]
            schema_name=schema_name,
        )
        logger.debug(
            f"Returned {len(result) if result else 0} columns for Redshift table {table_name}"
        )
        return result

    # Default path for non-Redshift dialects.
    if sqlalchemy.Table and isinstance(batch_data.selectable, sqlalchemy.Table):  # type: ignore[truthy-function] # FIXME CoP
        table_selectable = batch_data.source_table_name or batch_data.selectable.name
        schema_name = batch_data.source_schema_name or batch_data.selectable.schema

    # if custom query was passed in
    elif sqlalchemy.TextClause and isinstance(batch_data.selectable, sqlalchemy.TextClause):  # type: ignore[truthy-function] # FIXME CoP
        table_selectable = batch_data.selectable
        schema_name = None
    else:
        table_selectable = batch_data.source_table_name or batch_data.selectable.name
        schema_name = batch_data.source_schema_name or batch_data.selectable.schema

    return get_sqlalchemy_column_metadata(
        execution_engine=execution_engine,
        table_selectable=table_selectable,  # type: ignore[arg-type] # FIXME CoP
        schema_name=schema_name,
    )


def _get_spark_column_metadata(field, parent_name="", include_nested=True):  # noqa: C901 #  too complex
    cols = []
    if parent_name != "":
        parent_name = f"{parent_name}."

    if pyspark.types and isinstance(field, pyspark.types.StructType):
        for child in field.fields:
            cols += _get_spark_column_metadata(
                child, parent_name=parent_name, include_nested=include_nested
            )
    elif pyspark.types and isinstance(field, pyspark.types.StructField):
        if include_nested and "." in field.name:
            # Only add backticks to escape dotted fields if they don't already exist
            if field.name.startswith("`") and field.name.endswith("`"):
                name = f"{parent_name}{field.name}"
            else:
                name = f"{parent_name}`{field.name}`"
        else:
            name = parent_name + field.name

        field_metadata = {"name": name, "type": field.dataType}
        cols.append(field_metadata)

        if (
            include_nested
            and pyspark.types
            and isinstance(field.dataType, pyspark.types.StructType)
        ):
            for child in field.dataType.fields:
                cols += _get_spark_column_metadata(
                    child,
                    parent_name=parent_name + field.name,
                    include_nested=include_nested,
                )
    else:
        raise ValueError("unrecognized field type")  # noqa: TRY003 # FIXME CoP

    return cols
