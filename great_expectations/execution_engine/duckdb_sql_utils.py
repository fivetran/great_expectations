from __future__ import annotations

from typing import Any


def quote_ident(name: str) -> str:
    """Quote a DuckDB identifier (column/table name), escaping embedded double quotes.

    DuckDB, like Postgres, uses double quotes for identifiers, so this must not be
    confused with `sql_literal`, which quotes *values* with single quotes.
    """
    return '"' + name.replace('"', '""') + '"'


def sql_literal(value: Any) -> str:
    """Render a Python value as a DuckDB SQL literal.

    Metric partials build raw SQL text (see DuckDBExecutionEngine.resolve_metric_bundle),
    so every value interpolated into a query must go through here rather than an f-string
    to avoid SQL-injection-shaped bugs from user-controlled values such as `in_set`
    members or regex patterns.
    """
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return repr(value)
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def sql_literal_list(values: Any) -> str:
    """Render an iterable of Python values as a parenthesized DuckDB SQL literal list."""
    return "(" + ", ".join(sql_literal(v) for v in values) + ")"
