from __future__ import annotations

from typing import Any, NamedTuple, Optional, cast

from great_expectations.compatibility import aws
from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.compatibility.typing_extensions import override
from great_expectations.exceptions.exceptions import (
    RedshiftExecutionEngineError,
)
from great_expectations.execution_engine.sqlalchemy_batch_data import SqlAlchemyBatchData
from great_expectations.execution_engine.sqlalchemy_execution_engine import (
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.metric_provider import metric_value
from great_expectations.expectations.metrics.table_metrics.table_column_types import (
    ColumnTypes as BaseColumnTypes,
)


class RedshiftColumnSchema(NamedTuple):
    character_maximum_length: int | None
    numeric_precision: int | None
    numeric_scale: int | None
    datetime_precision: int | None
    data_type: str
    column_name: str


class RedshiftExecutionEngine(SqlAlchemyExecutionEngine):
    """SqlAlchemyExecutionEngine for Redshift databases."""

    pass


# The complete list of reshift types can be found here:
# https://docs.aws.amazon.com/redshift/latest/dg/c_Supported_data_types.html
REDSHIFT_TYPES = (
    {
        "boolean": aws.redshiftdialect.BOOLEAN,
        "smallint": aws.redshiftdialect.SMALLINT,
        "integer": aws.redshiftdialect.INTEGER,
        "bigint": aws.redshiftdialect.BIGINT,
        "real": aws.redshiftdialect.REAL,
        "double precision": aws.redshiftdialect.DOUBLE_PRECISION,
        # Numeric is odd since the data returns numeric as a type to pg_get_cols
        # In sqlalchemy 1.4 we get the type sa.sql.sqltypes.NUMERIC returned.
        # However, the sqlalchemy redshift dialect only has DECIMAL. The official
        # redshift docs say 'DECIMAL' is the correct type and NUMER is an alias:
        # https://docs.aws.amazon.com/redshift/latest/dg/c_Supported_data_types.html
        # So we are settling on DECIMAL here.
        "numeric": aws.redshiftdialect.DECIMAL,
        "character": aws.redshiftdialect.CHAR,
        "character varying": aws.redshiftdialect.VARCHAR,
        "date": aws.redshiftdialect.DATE,
        "time without time zone": sa.TIME,  # NOTE: no equivalent in aws.redshiftdialect
        "time with time zone": aws.redshiftdialect.TIMETZ,
        "timestamp without time zone": aws.redshiftdialect.TIMESTAMP,
        "timestamp with time zone": aws.redshiftdialect.TIMESTAMPTZ,
    }
    if aws.redshiftdialect
    else {}
)


class ColumnTypes(BaseColumnTypes):
    """MetricProvider Class for Aggregate Column Types metric for Redshift databases."""

    @override
    @metric_value(engine=RedshiftExecutionEngine)
    def _sqlalchemy(
        cls,
        execution_engine: SqlAlchemyExecutionEngine,
        metric_domain_kwargs: dict,
        metric_value_kwargs: dict,
        metrics: dict[str, Any],
        runtime_configuration: dict,
    ):
        # For sqlalchemy version < 2 fallback to default implementation
        if sa.__version__[0] != "2":
            return BaseColumnTypes._sqlalchemy(
                cls=cls,
                execution_engine=execution_engine,
                metric_domain_kwargs=metric_domain_kwargs,
                metric_value_kwargs=metric_value_kwargs,
                metrics=metrics,
                runtime_configuration=runtime_configuration,
            )

        # For sqlalchemy 2 use this new implementation which avoids incompatible parts of dialect
        # Get the table information
        assert isinstance(execution_engine, RedshiftExecutionEngine)
        result = []
        table_name, schema_name = cls._get_table_schema(execution_engine, metric_domain_kwargs)
        schema_filter: str = f"and table_schema = '{schema_name}'" if schema_name else ""
        query = sa.text(
            f"""
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                datetime_precision
            FROM information_schema.columns
            WHERE table_name = '{table_name}' {schema_filter}
            ORDER BY ordinal_position;
            """
        )
        rows: sa.CursorResult[RedshiftColumnSchema] = execution_engine.execute_query(query)

        for row in rows:
            redshift_type = REDSHIFT_TYPES.get(row.data_type)
            if redshift_type is None:
                raise RedshiftExecutionEngineError(
                    message=f"Unknown Redshift column type: {row.data_type}"
                )

            kwargs = cls._get_sqla_column_type_kwargs(row)

            # use EAFP for convenience https://docs.python.org/3/glossary.html#term-EAFP
            try:
                column_type = redshift_type(**kwargs)
            except Exception:
                column_type = redshift_type()

            result.append({"name": row.column_name, "type": column_type})

        return result

    @classmethod
    def _get_table_schema(
        cls,
        execution_engine: RedshiftExecutionEngine,
        metric_domain_kwargs: dict,
    ) -> tuple[str | sa.TextClause, Optional[str]]:
        batch_id: Optional[str] = metric_domain_kwargs.get("batch_id")
        if batch_id is None:
            if execution_engine.batch_manager.active_batch_data_id is not None:
                batch_id = execution_engine.batch_manager.active_batch_data_id
            else:
                raise RedshiftExecutionEngineError(
                    message="batch_id could not be determined from domain kwargs and no "
                    "active_batch_data is loaded into the execution engine"
                )

        possible_batch_data = execution_engine.batch_manager.batch_data_cache.get(batch_id)
        if possible_batch_data is None:
            raise RedshiftExecutionEngineError(
                message="the requested batch is not available; please load the batch into the "
                "execution engine."
            )
        batch_data: SqlAlchemyBatchData = cast(SqlAlchemyBatchData, possible_batch_data)

        table_selectable: str | sa.TextClause

        if isinstance(batch_data.selectable, sa.Table):
            table_selectable = batch_data.source_table_name or batch_data.selectable.name
            schema_name = batch_data.source_schema_name or batch_data.selectable.schema
        elif isinstance(batch_data.selectable, sa.TextClause):
            table_selectable = batch_data.selectable
            schema_name = None
        else:
            table_selectable = batch_data.source_table_name or batch_data.selectable.name
            schema_name = batch_data.source_schema_name or batch_data.selectable.schema

        return table_selectable, schema_name

    @classmethod
    def _get_sqla_column_type_kwargs(cls, row: sa.Row[RedshiftColumnSchema]) -> dict:
        """
        Build a dict based on mapping redshift column metadata to SQLAlchemy Type named kwargs.
        """
        result = {}
        if row.character_maximum_length is not None:
            result["length"] = row.character_maximum_length
        if row.numeric_scale is not None:
            result["scale"] = row.numeric_scale
        if row.numeric_precision is not None:
            result["precision"] = row.numeric_precision
        if row.datetime_precision is not None and "with time zone" in row.data_type:
            result["precision"] = row.datetime_precision
            result["timezone"] = True
        return result
