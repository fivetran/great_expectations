from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Union

import great_expectations.exceptions as gx_exceptions
from great_expectations.compatibility import pyspark, sqlalchemy
from great_expectations.compatibility.pyspark import functions as F
from great_expectations.compatibility.sqlalchemy import (
    Select,
)
from great_expectations.compatibility.sqlalchemy import (
    sqlalchemy as sa,
)
from great_expectations.compatibility.typing_extensions import override
from great_expectations.constants import MAX_RESULT_RECORDS
from great_expectations.core.metric_function_types import (
    MetricFunctionTypes,
    MetricPartialFunctionTypes,
    MetricPartialFunctionTypeSuffixes,
    SummarizationMetricNameSuffixes,
)
from great_expectations.execution_engine import (
    ExecutionEngine,
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.map_metric_provider import (
    ColumnMapMetricProvider,
    column_condition_partial,
    column_function_partial,
)
from great_expectations.expectations.registry import register_metric
from great_expectations.util import get_sqlalchemy_selectable
from great_expectations.validator.validation_graph import MetricConfiguration

if TYPE_CHECKING:
    from great_expectations.expectations.expectation_configuration import (
        ExpectationConfiguration,
    )


_DUP_KEY_COUNT_LABEL = "_num_rows"
_DUP_KEY_SUBQUERY_ALIAS = "column_values_count_per_value_subquery"


def _named_source_subquery(selectable, table_columns: List[str]):
    """Return a named subquery that explicitly projects "table_columns" from
    the source selectable.

    "SqlAlchemyBatchData" exposes the source table as a metadata-less
    "sa.Table" shell (no reflected columns), so its ".c" accessor is empty.
    Wrapping it in an explicit projection gives us a subquery whose ".c"
    collection is populated and can be used to unambiguously reference
    source-side columns inside a join with the dup-keys subquery.
    """
    base = (
        selectable
        if isinstance(selectable, Select)
        else sa.select(*[sa.column(c) for c in table_columns]).select_from(selectable)
    )
    return base.subquery("column_values_unique_source")


def _build_dup_keys_subquery(
    execution_engine: SqlAlchemyExecutionEngine,
    metric_domain_kwargs: Dict[str, Any],
    column_name: str,
):
    """Narrow GROUP BY/HAVING subquery: one row per duplicated value.

    Reads only the target column from the source table; partial-aggregation
    friendly on distributed engines and avoids wide-row window sort.
    """
    selectable = execution_engine.get_domain_records(domain_kwargs=metric_domain_kwargs)
    selectable = get_sqlalchemy_selectable(selectable)
    return (
        sa.select(sa.column(column_name))
        .select_from(selectable)
        .where(sa.column(column_name).is_not(None))
        .group_by(sa.column(column_name))
        .having(sa.func.count() >= 2)  # noqa: PLR2004
        .subquery("column_values_unique_dup_keys")
    )


def _sqlalchemy_unique_unexpected_rows(
    cls,
    execution_engine: SqlAlchemyExecutionEngine,
    metric_domain_kwargs: Dict[str, Any],
    metric_value_kwargs: Dict[str, Any],
    metrics: Dict[str, Any],
    **kwargs,
) -> Sequence[Any]:
    """Return full source rows for values that appear more than once.

    Source is scanned twice (cheap narrow hash-aggregate + hash join back),
    but only when the caller requests "unexpected_rows" (typically COMPLETE
    result_format). The dominant "unexpected_count" path stays single-scan.
    """
    column_name: str = metric_domain_kwargs["column"]
    table_columns: List[str] = metrics["table.columns"]
    source_selectable = _named_source_subquery(
        execution_engine.get_domain_records(domain_kwargs=metric_domain_kwargs),
        table_columns,
    )
    dup_keys = _build_dup_keys_subquery(
        execution_engine=execution_engine,
        metric_domain_kwargs=metric_domain_kwargs,
        column_name=column_name,
    )
    column_selector = [source_selectable.c[c] for c in table_columns]
    query = sa.select(*column_selector).select_from(
        source_selectable.join(
            dup_keys,
            source_selectable.c[column_name] == dup_keys.c[column_name],
        )
    )
    result_format = metric_value_kwargs["result_format"]
    if result_format["result_format"] != "COMPLETE":
        limit = min(result_format["partial_unexpected_count"], MAX_RESULT_RECORDS)
        query = query.limit(limit)
    try:
        return [
            row._asdict()
            for row in execution_engine.execute_query(query).fetchmany(MAX_RESULT_RECORDS)
        ]
    except sqlalchemy.OperationalError as oe:
        raise gx_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
            message=f"An SQL execution Exception occurred: {oe!s}."
        )


def _sqlalchemy_unique_unexpected_index_list(
    cls,
    execution_engine: SqlAlchemyExecutionEngine,
    metric_domain_kwargs: Dict[str, Any],
    metric_value_kwargs: Dict[str, Any],
    metrics: Dict[str, Any],
    **kwargs,
) -> Union[List[Dict[str, Any]], None]:
    """Return specified index columns + target column for duplicate rows."""
    result_format = metric_value_kwargs["result_format"]
    unexpected_index_column_names = result_format.get("unexpected_index_column_names")
    if not unexpected_index_column_names:
        return None

    column_name: str = metric_domain_kwargs["column"]
    all_table_columns: List[str] = metrics.get("table.columns", [])
    for idx_col in unexpected_index_column_names:
        if idx_col not in all_table_columns:
            raise gx_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                message=(
                    f'Error: The unexpected_index_column: "{idx_col}" does not exist in '
                    "SQL Table. Please check your configuration and try again."
                )
            )

    source_selectable = _named_source_subquery(
        execution_engine.get_domain_records(domain_kwargs=metric_domain_kwargs),
        all_table_columns,
    )
    dup_keys = _build_dup_keys_subquery(
        execution_engine=execution_engine,
        metric_domain_kwargs=metric_domain_kwargs,
        column_name=column_name,
    )
    column_selector = [source_selectable.c[c] for c in unexpected_index_column_names]
    column_selector.append(source_selectable.c[column_name])
    query = (
        sa.select(*column_selector)
        .select_from(
            source_selectable.join(
                dup_keys,
                source_selectable.c[column_name] == dup_keys.c[column_name],
            )
        )
        .limit(result_format["partial_unexpected_count"])
    )
    exclude_unexpected_values: bool = result_format.get("exclude_unexpected_values", False)
    try:
        query_result = execution_engine.execute_query(query).fetchall()
    except sqlalchemy.OperationalError as oe:
        raise gx_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
            message=f"An SQL execution Exception occurred: {oe!s}."
        )

    if exclude_unexpected_values:
        return [
            {col: row[i] for i, col in enumerate(unexpected_index_column_names)}
            for row in query_result
        ]
    return [
        {
            **{col: row[i] for i, col in enumerate(unexpected_index_column_names)},
            column_name: row[-1],
        }
        for row in query_result
    ]


class ColumnValuesUnique(ColumnMapMetricProvider):
    """Detects duplicate values in a column.

    The "SqlAlchemyExecutionEngine" implementation materializes a *narrow* windowed
    subquery that exposes only the target column and a "_num_rows" count per value.
    Because the source table is scanned exactly once and the window operator carries
    only one column through the sort/partition phase, this avoids both:

    * the "col NOT IN (dup_subquery)" double-scan pattern (original failure mode),
    * the "SELECT *table_columns, count() OVER ... FROM source" wide-row window that
      forced Redshift to materialize every column (including JSON/SUPER fields)
      through the sort, occasionally tripping the WLM "low_timeout" rule on
      column-store backends even after the double-scan was removed.

    Auxiliary metrics that need the full source row ("unexpected_rows") or specific
    "unexpected_index_column_names" are served by a separate join-back path that
    re-reads only the necessary columns from the source table, keeping the common
    "BASIC" result_format (only "unexpected_count" requested) on the single-scan
    fast path.
    """

    function_metric_name = "column_values.count_per_value"
    condition_metric_name = "column_values.unique"

    @column_condition_partial(engine=PandasExecutionEngine)
    def _pandas(cls, column, **kwargs):
        return ~column.duplicated(keep=False)

    @column_function_partial(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy_function(cls, column, _table, **kwargs):
        # Narrow projection: only the target column and the window count per value.
        # Auxiliary methods that consume this selectable (unexpected_count,
        # unexpected_values, unexpected_value_counts) only ever read these two
        # columns. Paths that need additional source columns ("unexpected_rows",
        # "unexpected_index_list") are overridden in _register_metric_functions
        # to join back to source.
        from_clause = _table.subquery() if isinstance(_table, Select) else _table
        return (
            sa.select(
                sa.column(column.name),
                sa.func.count()
                .over(partition_by=sa.column(column.name))
                .label(_DUP_KEY_COUNT_LABEL),
            )
            .select_from(from_clause)
            .alias(_DUP_KEY_SUBQUERY_ALIAS)
        )

    @column_condition_partial(
        engine=SqlAlchemyExecutionEngine,
        partial_fn_type=MetricPartialFunctionTypes.WINDOW_CONDITION_FN,
    )
    def _sqlalchemy_condition(cls, column, **kwargs):
        metrics = kwargs.get("_metrics")
        count_per_value_query, _, _ = metrics[
            f"column_values.count_per_value.{MetricPartialFunctionTypeSuffixes.MAP.value}"
        ]
        return count_per_value_query.c[_DUP_KEY_COUNT_LABEL] < 2  # noqa: PLR2004

    @column_condition_partial(
        engine=SparkDFExecutionEngine,
        partial_fn_type=MetricPartialFunctionTypes.WINDOW_CONDITION_FN,
    )
    def _spark(cls, column, **kwargs):
        return F.count(F.lit(1)).over(pyspark.Window.partitionBy(column)) <= 1

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

        if isinstance(execution_engine, SqlAlchemyExecutionEngine) and (
            metric.metric_name
            == f"column_values.unique.{MetricPartialFunctionTypeSuffixes.CONDITION.value}"
        ):
            dependencies[
                f"column_values.count_per_value.{MetricPartialFunctionTypeSuffixes.MAP.value}"
            ] = MetricConfiguration(
                metric_name=f"column_values.count_per_value.{MetricPartialFunctionTypeSuffixes.MAP.value}",
                metric_domain_kwargs=metric.metric_domain_kwargs,
                metric_value_kwargs=None,
            )

        return dependencies

    @classmethod
    @override
    def _register_metric_functions(cls):
        super()._register_metric_functions()
        # The narrow windowed subquery (above) carries only the target column.
        # The default map-condition auxiliary methods for row-retrieval paths
        # assume the selectable carries every table column (compound_columns.unique
        # pattern), which would re-introduce the wide-row window on Redshift.
        # Override those two paths with a single narrow dup-keys subquery joined
        # back to source.
        register_metric(
            metric_name=f"{cls.condition_metric_name}."
            f"{SummarizationMetricNameSuffixes.UNEXPECTED_ROWS.value}",
            metric_domain_keys=cls.condition_domain_keys,
            metric_value_keys=(*cls.condition_value_keys, "result_format"),
            execution_engine=SqlAlchemyExecutionEngine,
            metric_class=cls,
            metric_provider=_sqlalchemy_unique_unexpected_rows,
            metric_fn_type=MetricFunctionTypes.VALUE,
        )
        register_metric(
            metric_name=f"{cls.condition_metric_name}."
            f"{SummarizationMetricNameSuffixes.UNEXPECTED_INDEX_LIST.value}",
            metric_domain_keys=cls.condition_domain_keys,
            metric_value_keys=(*cls.condition_value_keys, "result_format"),
            execution_engine=SqlAlchemyExecutionEngine,
            metric_class=cls,
            metric_provider=_sqlalchemy_unique_unexpected_index_list,
            metric_fn_type=MetricFunctionTypes.VALUE,
        )
