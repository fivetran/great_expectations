from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, NamedTuple, Optional, cast

from great_expectations.compatibility import aws
from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.compatibility.typing_extensions import override
from great_expectations.exceptions.exceptions import (
    RedshiftExecutionEngineError,
)
from great_expectations.execution_engine.sqlalchemy_execution_engine import (
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.metric_provider import metric_value
from great_expectations.expectations.metrics.table_metrics.table_column_types import (
    ColumnTypes as BaseColumnTypes,
)

if TYPE_CHECKING:
    from great_expectations.execution_engine.sqlalchemy_batch_data import SqlAlchemyBatchData

logger = logging.getLogger(__name__)


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
        "geometry": aws.redshiftdialect.GEOMETRY,
        "super": aws.redshiftdialect.SUPER,
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
        assert isinstance(execution_engine, RedshiftExecutionEngine)
        table_name, schema_name = cls._get_table_schema(execution_engine, metric_domain_kwargs)
        logger.debug(f"Retrieving columns for table: {table_name}, schema: {schema_name}")

        result = cls._query_information_schema(execution_engine, table_name, schema_name)

        # If information_schema returned no rows (or was skipped for TextClause),
        # fall back to SELECT * LIMIT 0
        if not result:
            result = cls._fallback_to_select_star(execution_engine, table_name, schema_name)

        return result

    @classmethod
    def _query_information_schema(
        cls,
        execution_engine: RedshiftExecutionEngine,
        table_name: str | sa.TextClause,
        schema_name: Optional[str],
    ) -> list[dict[str, Any]]:
        """Query information_schema for column types."""
        # If table_name is a TextClause (custom SQL query), skip information_schema
        # and go directly to fallback method since we can't query information_schema
        # for custom queries
        if isinstance(table_name, sa.TextClause):
            logger.debug(
                "Custom SQL query (TextClause) detected, skipping information_schema query"
            )
            return []

        query = cls._build_information_schema_query(table_name, schema_name)
        rows: sa.CursorResult[RedshiftColumnSchema] = execution_engine.execute_query(query)
        rows_list = list(rows)
        logger.debug(f"information_schema query returned {len(rows_list)} rows")

        return cls._process_information_schema_rows(rows_list)

    @classmethod
    def _build_information_schema_query(
        cls,
        table_name: str,
        schema_name: Optional[str],
    ) -> sa.TextClause:
        """Build parameterized information_schema query to prevent SQL injection."""
        base_query = """
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                datetime_precision
            FROM information_schema.columns
            WHERE table_name = :table_name
        """

        if schema_name:
            base_query += " AND table_schema = :schema_name"

        base_query += " ORDER BY ordinal_position;"

        params = {"table_name": str(table_name)}
        if schema_name:
            params["schema_name"] = str(schema_name)

        return sa.text(base_query).bindparams(**params)

    @classmethod
    def _process_information_schema_rows(
        cls,
        rows_list: list[sa.Row[RedshiftColumnSchema]],
    ) -> list[dict[str, Any]]:
        """Process rows from information_schema query into column type results."""
        result = []
        for row in rows_list:
            column_type = cls._create_column_type(row)
            result.append({"name": row.column_name, "type": column_type})
        return result

    @classmethod
    def _create_column_type(cls, row: sa.Row[RedshiftColumnSchema]) -> Any:
        """Create SQLAlchemy column type from Redshift column metadata."""
        redshift_type = REDSHIFT_TYPES.get(row.data_type)
        if redshift_type is None:
            logger.warning(
                f"Unknown Redshift column type: {row.data_type}, using VARCHAR as fallback"
            )
            redshift_type = sa.VARCHAR

        kwargs = cls._get_sqla_column_type_kwargs(row)

        # use EAFP for convenience https://docs.python.org/3/glossary.html#term-EAFP
        try:
            return redshift_type(**kwargs)
        except Exception:
            return redshift_type()

    @classmethod
    def _fallback_to_select_star(
        cls,
        execution_engine: RedshiftExecutionEngine,
        table_name: str | sa.TextClause,
        schema_name: Optional[str],
    ) -> list[dict[str, Any]]:
        """Fallback to SELECT * LIMIT 0 when information_schema fails."""
        logger.debug("information_schema returned 0 columns, falling back to SELECT * LIMIT 0")
        # Use SQLAlchemy table() to safely construct the query with proper identifier escaping
        # This prevents SQL injection from untrusted table_name and schema_name values
        if isinstance(table_name, str):
            table_obj = sa.table(table_name, schema=schema_name)
            fallback_query = sa.select("*").select_from(table_obj).limit(0)
        else:
            # If table_name is already a TextClause, use it directly but still limit
            fallback_query = sa.select("*").select_from(table_name).limit(0)
        try:
            fallback_result = execution_engine.execute_query(fallback_query)
            column_names = list(fallback_result.keys())
            result = [{"name": col_name, "type": sa.VARCHAR()} for col_name in column_names]
            table_ref = f"{schema_name}.{table_name}" if schema_name else str(table_name)
            logger.info(f"Fallback retrieved {len(result)} columns from {table_ref}")
            return result
        except Exception:
            table_ref = f"{schema_name}.{table_name}" if schema_name else str(table_name)
            logger.exception(f"Fallback SELECT * LIMIT 0 failed for {table_ref}")
            raise RedshiftExecutionEngineError(
                message=(
                    f"Failed to retrieve columns for {table_ref} using both "
                    "information_schema and SELECT * LIMIT 0"
                )
            )

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
        batch_data: SqlAlchemyBatchData = cast("SqlAlchemyBatchData", possible_batch_data)

        # Derive table/schema from batch metadata.
        # Many GX Redshift configs encode "schema.table" in source_table_name with
        # source_schema_name left as None, so we need to normalize this into
        # separate schema/table components for information_schema queries.
        table_selectable: str | sa.TextClause
        schema_name: Optional[str]

        if isinstance(batch_data.selectable, sa.Table):
            table_selectable = batch_data.source_table_name or batch_data.selectable.name or ""
            schema_name = batch_data.source_schema_name or batch_data.selectable.schema
        elif isinstance(batch_data.selectable, sa.TextClause):
            # Custom query: pass through as-is and skip schema filter
            table_selectable = batch_data.selectable
            schema_name = None
            return table_selectable, schema_name
        else:
            table_selectable = batch_data.source_table_name or batch_data.selectable.name or ""
            schema_name = batch_data.source_schema_name or batch_data.selectable.schema

        table_name: str | sa.TextClause

        # If schema is still None but table looks like "schema.table", split it.
        if isinstance(table_selectable, str) and schema_name is None and "." in table_selectable:
            # split on first dot only: "schema.table" or "db.schema.table"
            parts = table_selectable.split(".", 1)
            schema_name = parts[0]
            table_name = parts[1]
        else:
            table_name = table_selectable

        return table_name, schema_name

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
