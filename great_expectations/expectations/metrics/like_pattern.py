from __future__ import annotations

from typing import Any

from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.expectations.metrics.util import (
    get_dialect_like_pattern_expression as _base_like_pattern_expression,
)


def get_dialect_display_name(dialect: Any) -> str:
    """Return a dialect name safe to put in an unsupported-dialect error.

    Callers pass either a SQLAlchemy dialect module or a dialect instance. Several
    modules (``sqlalchemy.dialects.oracle``, ``sqlalchemy_singlestoredb``) have no
    ``name`` attribute, so reading ``dialect.name`` raises AttributeError before the
    intended NotImplementedError can be raised.
    """
    name = getattr(dialect, "name", None)
    if isinstance(name, str) and name:
        return name
    inner = getattr(dialect, "dialect", None)
    inner_name = getattr(inner, "name", None)
    if isinstance(inner_name, str) and inner_name:
        return inner_name
    module_name = getattr(dialect, "__name__", None)
    if isinstance(module_name, str) and module_name:
        return module_name
    return type(dialect).__name__


def _supports_native_like(dialect: Any) -> bool:
    """Oracle and MySQL-compatible dialects (including SingleStore) evaluate LIKE natively.

    The shared allow-list checks ``sa.dialects.mysql.dialect``, which is
    ``MySQLDialect_mysqldb``. SingleStore subclasses ``MySQLDialect`` directly, so that
    check misses it. Oracle is absent from the allow-list entirely.
    """
    try:
        if issubclass(dialect.dialect, sa.dialects.oracle.dialect):  # type: ignore[union-attr, attr-defined]
            return True
    except (AttributeError, TypeError):
        pass
    try:
        if issubclass(dialect.dialect, sa.dialects.mysql.base.MySQLDialect):  # type: ignore[union-attr]
            return True
    except (AttributeError, TypeError):
        pass
    return False


def get_dialect_like_pattern_expression(
    column: sa.Column,
    dialect: Any,
    like_pattern: str,
    positive: bool = True,
    escape: str | None = None,
):
    """Build a LIKE expression, including Oracle and SingleStore.

    Existing dialects keep the shared helper's SQL, including its ESCAPE handling.
    Oracle and SingleStore fall through that helper and use the same ``column.like``
    form, which both databases execute natively.
    """
    expression = _base_like_pattern_expression(
        column, dialect, like_pattern, positive=positive, escape=escape
    )
    if expression is not None or not _supports_native_like(dialect):
        return expression
    try:
        like_expression = column.like(sa.literal(like_pattern), escape=escape)
    except AttributeError:
        return None
    if positive:
        return like_expression
    return sa.not_(like_expression)
