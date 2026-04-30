from __future__ import annotations

from great_expectations.compatibility import pyspark
from great_expectations.compatibility.pyspark import functions as F
from great_expectations.compatibility.sqlalchemy import (
    sqlalchemy as sa,
)
from great_expectations.core.metric_function_types import MetricPartialFunctionTypes
from great_expectations.execution_engine import (
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.execution_engine.sqlalchemy_dialect import (
    GXSqlDialect,
    quote_str,
)
from great_expectations.expectations.metrics.map_metric_provider import (
    ColumnMapMetricProvider,
    column_condition_partial,
)
from great_expectations.util import generate_temporary_table_name


class ColumnValuesUnique(ColumnMapMetricProvider):
    condition_metric_name = "column_values.unique"

    @column_condition_partial(engine=PandasExecutionEngine)
    def _pandas(cls, column, **kwargs):
        return ~column.duplicated(keep=False)

    # NOTE: 20201119 - JPC - We cannot split per-dialect into window and non-window functions
    # @column_condition_partial(
    #     engine=SqlAlchemyExecutionEngine,
    # )
    # def _sqlalchemy(cls, column, _table, **kwargs):
    #     dup_query = (
    #         sa.select(column)
    #         .select_from(_table)
    #         .group_by(column)
    #         .having(sa.func.count(column) > 1)
    #     )
    #
    #     return column.notin_(dup_query)

    @column_condition_partial(
        engine=SqlAlchemyExecutionEngine,
        partial_fn_type=MetricPartialFunctionTypes.WINDOW_CONDITION_FN,
    )
    def _sqlalchemy_window(cls, column, _table, **kwargs):
        # MySQL and SingleStore cannot reference a temp table more than once in the
        # same query, and SingleStore disallows correlated subselects with GROUP BY.
        # Create a temp table copy of the column to avoid both issues.
        dialect = kwargs.get("_dialect")
        sql_engine = kwargs.get("_sqlalchemy_engine")
        execution_engine = kwargs.get("_execution_engine")
        try:
            dialect_name = dialect.dialect.name
        except AttributeError:
            try:
                dialect_name = dialect.name
            except AttributeError:
                dialect_name = ""
        if sql_engine and dialect and dialect_name in ("mysql", "singlestoredb"):
            gx_dialect = GXSqlDialect(dialect_name)
            quoted_col = quote_str(column.name, gx_dialect)
            temp_table_name = generate_temporary_table_name()
            if isinstance(_table, sa.Select):
                from_clause = _table.subquery().alias("tmp")
            else:
                from_clause = _table
            source_query = sa.select(sa.column(column.name)).select_from(from_clause)
            compiled = source_query.compile(
                dialect=sql_engine.dialect, compile_kwargs={"literal_binds": True}
            )
            temp_table_stmt = f"CREATE TEMPORARY TABLE {temp_table_name} AS {compiled}"
            execution_engine.execute_query_in_transaction(sa.text(temp_table_stmt))
            # SingleStore cannot handle subselects with GROUP BY/HAVING inside
            # expressions, so materialize duplicate values into a second temp table.
            dup_table_name = generate_temporary_table_name()
            dup_stmt = (
                f"CREATE TEMPORARY TABLE {dup_table_name} AS "
                f"SELECT {quoted_col} FROM {temp_table_name} "
                f"GROUP BY {quoted_col} HAVING count({quoted_col}) > 1"
            )
            execution_engine.execute_query_in_transaction(sa.text(dup_stmt))
            dup_query = sa.select(column).select_from(sa.text(dup_table_name))
        else:
            from_clause = _table.subquery() if isinstance(_table, sa.Select) else _table
            dup_query = (
                sa.select(column)
                .select_from(from_clause)
                .group_by(column)
                .having(sa.func.count(column) > 1)
            )
        return column.notin_(dup_query)

    @column_condition_partial(
        engine=SparkDFExecutionEngine,
        partial_fn_type=MetricPartialFunctionTypes.WINDOW_CONDITION_FN,
    )
    def _spark(cls, column, **kwargs):
        return F.count(F.lit(1)).over(pyspark.Window.partitionBy(column)) <= 1
