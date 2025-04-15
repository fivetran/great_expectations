from __future__ import annotations

from typing import Any, Optional, cast

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
        # Redshift has this type but the dialect doesn't so we map it to sa.TIME.
        "time without time zone": sa.TIME,
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
        table_name, schema_name = cls._get_table_schema(execution_engine, metric_domain_kwargs)
        full_table_name = f'"{schema_name}"."{table_name}"' if schema_name else f"{table_name}"
        # Query for the column information
        query = sa.text(f"""
            select * from pg_get_cols('{full_table_name}')
            cols(view_schema name, view_name name, col_name name, col_type varchar, col_num int);
        """)
        raw_result = execution_engine.execute_query(query)
        # Parse out metadata
        column_metadata = []
        # The raw result is a tuple of strings, one for each row.
        for r in raw_result:
            _schema, _table, column, raw_column_type, _column_num = r
            # If the type is parameterized, we must removed the arguments to the types to do a
            # string lookup from the type string to the actual type.
            column_type_str_parts = raw_column_type.split("(")
            column_base_type = REDSHIFT_TYPES.get(column_type_str_parts[0])
            if column_base_type is None:
                raise RedshiftExecutionEngineError(
                    message=f"Unknown Redshift column type: {raw_column_type}"
                )
            # We expect our split on the raw column type to be either:
            #  length 1: no arguments
            #  length 2: has arguments
            # We don't expect any argument nesting.
            expected_column_type_str_parts = [1, 2]
            if len(column_type_str_parts) == expected_column_type_str_parts[0]:
                column_type = column_base_type()
            elif len(column_type_str_parts) == expected_column_type_str_parts[1]:
                column_type_args = column_type_str_parts[1].rstrip(")").split(",")
                column_type = column_base_type(*column_type_args)
            else:
                raise RedshiftExecutionEngineError(
                    message=f"Unexpected nesting of arguments in column type: {raw_column_type}"
                )
            column_metadata.append({"name": column, "type": column_type})
        return column_metadata

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
