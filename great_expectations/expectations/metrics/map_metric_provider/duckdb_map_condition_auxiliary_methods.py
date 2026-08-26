from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from great_expectations.constants import MAX_RESULT_RECORDS
from great_expectations.execution_engine.duckdb_sql_utils import quote_ident
from great_expectations.expectations.metrics.util import (
    get_dbms_compatible_metric_domain_kwargs,
)

if TYPE_CHECKING:
    from great_expectations.execution_engine import DuckDBExecutionEngine


def _duckdb_map_condition_unexpected_count_aggregate_fn(
    cls,
    execution_engine: DuckDBExecutionEngine,
    metric_domain_kwargs: dict,
    metric_value_kwargs: dict,
    metrics: Dict[str, Any],
    **kwargs,
) -> tuple[str, dict, dict]:
    """Returns unexpected count for MapExpectations, as a bundleable SQL aggregate expression."""
    unexpected_condition, compute_domain_kwargs, accessor_domain_kwargs = metrics[
        "unexpected_condition"
    ]
    return (
        f"SUM(CASE WHEN {unexpected_condition} THEN 1 ELSE 0 END)",
        compute_domain_kwargs,
        accessor_domain_kwargs,
    )


def _duckdb_map_condition_filtered_row_count(
    cls,
    execution_engine: DuckDBExecutionEngine,
    metric_domain_kwargs: dict,
    metric_value_kwargs: dict,
    metrics: Dict[str, Any],
    **kwargs,
) -> int:
    """Return the record count from the specified domain (after `ignore_row_if` filtering)."""
    _, compute_domain_kwargs, accessor_domain_kwargs = metrics["unexpected_condition"]

    accessor_domain_kwargs = get_dbms_compatible_metric_domain_kwargs(
        metric_domain_kwargs=accessor_domain_kwargs,
        batch_columns_list=metrics["table.columns"],
    )

    # get_domain_records() needs every domain_kwargs key present to apply "ignore_row_if"
    # filtering for MULTICOLUMN/COLUMN_PAIR domains.
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    relation = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)

    row = relation.aggregate("COUNT(*)").fetchone()
    return row[0] if row else 0


def _duckdb_map_condition_index(  # noqa: C901 # FIXME CoP
    cls,
    execution_engine: DuckDBExecutionEngine,
    metric_domain_kwargs: dict,
    metric_value_kwargs: dict,
    metrics: Dict[str, Any],
    **kwargs,
) -> list[dict[str, Any]] | None:
    """Returns indices (as dicts keyed by `unexpected_index_column_names`) of the rows which do
    not meet an expected condition. Mirrors the SQL backends' contract: without an explicit
    `unexpected_index_column_names` in `result_format` there's no notion of a row's "index" to
    report, so this returns None rather than inventing one.
    """
    unexpected_condition, compute_domain_kwargs, accessor_domain_kwargs = metrics[
        "unexpected_condition"
    ]

    result_format = metric_value_kwargs["result_format"]
    if "unexpected_index_column_names" not in result_format:
        return None

    domain_column_name_list: list[str] = []
    if "column" in accessor_domain_kwargs:
        domain_column_name_list.append(accessor_domain_kwargs["column"])
    elif "column_list" in accessor_domain_kwargs:
        domain_column_name_list = list(accessor_domain_kwargs["column_list"])
    elif "column_A" in accessor_domain_kwargs and "column_B" in accessor_domain_kwargs:
        domain_column_name_list = [
            accessor_domain_kwargs["column_A"],
            accessor_domain_kwargs["column_B"],
        ]

    all_table_columns: list[str] = metrics.get("table.columns", [])
    unexpected_index_column_names: list[str] = result_format.get(
        "unexpected_index_column_names", []
    )
    for column_name in unexpected_index_column_names:
        if column_name not in all_table_columns:
            raise ValueError(  # noqa: TRY003 # FIXME CoP
                f'The unexpected_index_column: "{column_name}" does not exist in the table. '
                "Please check your configuration and try again."
            )

    select_column_names = list(unexpected_index_column_names)
    for column_name in domain_column_name_list:
        if column_name not in select_column_names:
            select_column_names.append(column_name)

    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    relation = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    project_expr = ", ".join(quote_ident(c) for c in select_column_names)
    filtered = (
        relation.filter(unexpected_condition)
        .project(project_expr)
        .limit(result_format["partial_unexpected_count"])
    )
    rows = filtered.fetchall()

    exclude_unexpected_values: bool = result_format.get("exclude_unexpected_values", False)
    unexpected_index_list: list[dict[str, Any]] = []
    for row in rows:
        index_dict = dict(zip(select_column_names, row, strict=True))
        if exclude_unexpected_values:
            for column_name in domain_column_name_list:
                if column_name not in unexpected_index_column_names:
                    index_dict.pop(column_name, None)
        unexpected_index_list.append(index_dict)
    return unexpected_index_list


def _duckdb_map_condition_query(
    cls,
    execution_engine: DuckDBExecutionEngine,
    metric_domain_kwargs: dict,
    metric_value_kwargs: dict,
    metrics: Dict[str, Any],
    **kwargs,
) -> str | None:
    """Returns the SQL query text that selects the rows which do not meet an expected condition."""
    unexpected_condition, compute_domain_kwargs, accessor_domain_kwargs = metrics[
        "unexpected_condition"
    ]

    result_format = metric_value_kwargs["result_format"]
    if result_format.get("return_unexpected_index_query") is False:
        return None

    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    relation = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    return relation.filter(unexpected_condition).sql_query()


def _duckdb_column_map_condition_values(
    cls,
    execution_engine: DuckDBExecutionEngine,
    metric_domain_kwargs: dict,
    metric_value_kwargs: dict,
    metrics: Dict[str, Any],
    **kwargs,
) -> list:
    """Returns the actual column values which do not meet an expected condition, for
    ColumnMapExpectation Expectations.
    """
    unexpected_condition, compute_domain_kwargs, accessor_domain_kwargs = metrics[
        "unexpected_condition"
    ]

    if "column" not in accessor_domain_kwargs:
        raise ValueError(  # noqa: TRY003 # FIXME CoP
            'No "column" found in provided metric_domain_kwargs, but it is required for a '
            "column map metric (_duckdb_column_map_condition_values)."
        )

    accessor_domain_kwargs = get_dbms_compatible_metric_domain_kwargs(
        metric_domain_kwargs=accessor_domain_kwargs,
        batch_columns_list=metrics["table.columns"],
    )
    column_name: str = accessor_domain_kwargs["column"]

    relation = execution_engine.get_domain_records(domain_kwargs=compute_domain_kwargs)
    filtered = relation.filter(unexpected_condition)

    result_format = metric_value_kwargs["result_format"]
    if result_format["result_format"] != "COMPLETE":
        filtered = filtered.limit(result_format["partial_unexpected_count"])

    rows = filtered.project(quote_ident(column_name)).fetchall()
    return [row[0] for row in rows[:MAX_RESULT_RECORDS]]


def _duckdb_multicolumn_map_condition_values(
    cls,
    execution_engine: DuckDBExecutionEngine,
    metric_domain_kwargs: dict,
    metric_value_kwargs: dict,
    metrics: Dict[str, Any],
    **kwargs,
) -> list[dict[str, Any]]:
    """Returns the rows (as dicts keyed by domain column) which do not meet an expected
    condition, for MULTICOLUMN map expectations.
    """
    unexpected_condition, compute_domain_kwargs, accessor_domain_kwargs = metrics[
        "unexpected_condition"
    ]

    accessor_domain_kwargs = get_dbms_compatible_metric_domain_kwargs(
        metric_domain_kwargs=accessor_domain_kwargs,
        batch_columns_list=metrics["table.columns"],
    )

    if "column_list" not in accessor_domain_kwargs:
        raise ValueError(  # noqa: TRY003 # FIXME CoP
            'No "column_list" found in provided metric_domain_kwargs, but it is required for a '
            "multicolumn map metric (_duckdb_multicolumn_map_condition_values)."
        )
    domain_column_name_list: list[str] = list(accessor_domain_kwargs["column_list"])

    # get_domain_records() needs every domain_kwargs key present to apply "ignore_row_if"
    # filtering for MULTICOLUMN domains.
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    relation = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    filtered = relation.filter(unexpected_condition)

    result_format = metric_value_kwargs["result_format"]
    if result_format["result_format"] != "COMPLETE":
        filtered = filtered.limit(result_format["partial_unexpected_count"])

    project_expr = ", ".join(quote_ident(c) for c in domain_column_name_list)
    rows = filtered.project(project_expr).fetchall()
    return [
        dict(zip(domain_column_name_list, row, strict=True)) for row in rows[:MAX_RESULT_RECORDS]
    ]


def _duckdb_column_pair_map_condition_values(
    cls,
    execution_engine: DuckDBExecutionEngine,
    metric_domain_kwargs: dict,
    metric_value_kwargs: dict,
    metrics: Dict[str, Any],
    **kwargs,
) -> list[tuple[Any, Any]]:
    """Returns the (column_A, column_B) tuples which do not meet an expected condition, for
    COLUMN_PAIR map expectations.
    """
    unexpected_condition, compute_domain_kwargs, accessor_domain_kwargs = metrics[
        "unexpected_condition"
    ]

    accessor_domain_kwargs = get_dbms_compatible_metric_domain_kwargs(
        metric_domain_kwargs=accessor_domain_kwargs,
        batch_columns_list=metrics["table.columns"],
    )

    if not ("column_A" in accessor_domain_kwargs and "column_B" in accessor_domain_kwargs):
        raise ValueError(  # noqa: TRY003 # FIXME CoP
            'No "column_A" and "column_B" found in provided metric_domain_kwargs, but both are '
            "required for a column pair map metric (_duckdb_column_pair_map_condition_values)."
        )
    column_a_name = accessor_domain_kwargs["column_A"]
    column_b_name = accessor_domain_kwargs["column_B"]

    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    relation = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    filtered = relation.filter(unexpected_condition)

    result_format = metric_value_kwargs["result_format"]
    if result_format["result_format"] != "COMPLETE":
        filtered = filtered.limit(result_format["partial_unexpected_count"])

    project_expr = f"{quote_ident(column_a_name)}, {quote_ident(column_b_name)}"
    rows = filtered.project(project_expr).fetchall()
    return [(row[0], row[1]) for row in rows[:MAX_RESULT_RECORDS]]


def _duckdb_column_map_condition_value_counts(
    cls,
    execution_engine: DuckDBExecutionEngine,
    metric_domain_kwargs: dict,
    metric_value_kwargs: dict,
    metrics: Dict[str, Any],
    **kwargs,
) -> list:
    """Returns value counts for the column values which do not meet an expected condition, for
    ColumnMapExpectation Expectations.
    """
    unexpected_condition, compute_domain_kwargs, accessor_domain_kwargs = metrics[
        "unexpected_condition"
    ]

    if "column" not in accessor_domain_kwargs:
        raise ValueError(  # noqa: TRY003 # FIXME CoP
            'No "column" found in provided metric_domain_kwargs, but it is required for a '
            "column map metric (_duckdb_column_map_condition_value_counts)."
        )

    accessor_domain_kwargs = get_dbms_compatible_metric_domain_kwargs(
        metric_domain_kwargs=accessor_domain_kwargs,
        batch_columns_list=metrics["table.columns"],
    )
    column_name: str = accessor_domain_kwargs["column"]
    col = quote_ident(column_name)

    relation = execution_engine.get_domain_records(domain_kwargs=compute_domain_kwargs)
    filtered = relation.filter(unexpected_condition)

    return filtered.aggregate(f"{col}, COUNT(*) AS unexpected_count", group_expr=col).fetchall()
