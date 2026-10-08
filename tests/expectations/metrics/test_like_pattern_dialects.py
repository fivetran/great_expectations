from __future__ import annotations

from types import ModuleType

import pytest
import sqlalchemy as sa
import sqlalchemy.dialects.mysql
import sqlalchemy.dialects.oracle

from great_expectations.expectations.metrics.like_pattern import (
    get_dialect_display_name,
    get_dialect_like_pattern_expression,
)


def _column() -> sa.Column:
    return sa.Column("col")


@pytest.mark.unit
def test_like_expression_supports_oracle():
    expression = get_dialect_like_pattern_expression(
        column=_column(),
        dialect=sqlalchemy.dialects.oracle,
        like_pattern="foo%",
        positive=True,
    )
    assert expression is not None
    compiled = str(
        expression.compile(
            dialect=sa.dialects.oracle.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )
    assert "LIKE" in compiled.upper()
    assert "foo%" in compiled


@pytest.mark.unit
def test_like_expression_supports_singlestore():
    class SingleStoreDialect(sa.dialects.mysql.base.MySQLDialect):
        name = "singlestoredb"

    class SingleStoreModule(ModuleType):
        dialect = SingleStoreDialect

    expression = get_dialect_like_pattern_expression(
        column=_column(),
        dialect=SingleStoreModule(name="sqlalchemy_singlestoredb"),
        like_pattern="foo%",
        positive=False,
    )
    assert expression is not None
    compiled = str(expression.compile(compile_kwargs={"literal_binds": True}))
    assert "NOT LIKE" in compiled
    assert "foo%" in compiled


@pytest.mark.unit
def test_display_name_does_not_require_name_attribute():
    class NamelessDialect(ModuleType):
        pass

    nameless = NamelessDialect("sqlalchemy_example")
    assert get_dialect_display_name(nameless) == "sqlalchemy_example"
    assert get_dialect_display_name(sa.dialects.sqlite.dialect()) == "sqlite"


@pytest.mark.unit
def test_unsupported_dialect_is_named_without_attribute_error():
    class NamelessDialect(ModuleType):
        pass

    dialect = NamelessDialect("sqlalchemy_example")
    assert get_dialect_like_pattern_expression(_column(), dialect, "foo%") is None
    assert get_dialect_display_name(dialect) == "sqlalchemy_example"
