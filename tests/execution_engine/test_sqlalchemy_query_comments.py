"""SQL ending in a line comment must not swallow the syntax GX appends when wrapping it.

A query asset's raw SQL is reproduced verbatim inside ``(<query>) AS anon_1``, which SQLAlchemy
compiles onto a single line. When the text ends in a line comment, the appended closing paren and
alias land inside that comment and the statement is never terminated, so the database rejects it.

See https://github.com/fivetran/great_expectations/issues/12122.
"""

from __future__ import annotations

import pytest
from sqlalchemy.dialects import (  # noqa: F401 # registers sa.dialects.<name>
    mssql,
    mysql,
    oracle,
    postgresql,
)

from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.core.batch_spec import RuntimeQueryBatchSpec
from great_expectations.execution_engine.sqlalchemy_execution_engine import (
    SqlAlchemyExecutionEngine,
)
from tests.sqlalchemy_test_doubles import MockSaEngine

QUERY_ENDING_IN_LINE_COMMENT = "SELECT col_a FROM test_table -- only the rows we care about"


def _appended_sql_is_commented_out(compiled: str) -> bool:
    """Whether a line comment in `compiled` runs over SQL that follows it on the same line."""
    return any(
        "--" in line and line.index("--") < line.rfind(")") for line in compiled.splitlines()
    )


@pytest.mark.unit
@pytest.mark.parametrize("dialect_name", ["postgresql", "mysql", "mssql", "oracle"])
def test_text_clause_batch_is_wrapped_on_a_fresh_line(dialect_name: str) -> None:
    """Every dialect but SQLite gets the query back as a TextClause, which `get_domain_records`
    wraps with `.columns().subquery()` before running metrics against it."""
    dialect = getattr(sa.dialects, dialect_name).dialect()
    engine = SqlAlchemyExecutionEngine(engine=MockSaEngine(dialect=dialect))

    selectable = engine._build_selectable_from_batch_spec(
        batch_spec=RuntimeQueryBatchSpec(query=QUERY_ENDING_IN_LINE_COMMENT)
    )
    wrapped = sa.select(sa.func.count()).select_from(selectable.columns().subquery())

    assert not _appended_sql_is_commented_out(str(wrapped.compile(dialect=dialect)))


@pytest.mark.sqlite
def test_sqlite_subselect_batch_is_wrapped_on_a_fresh_line() -> None:
    """SQLite takes the other branch, where `_subselectable` wraps the query into a subselect
    immediately rather than handing it back as a TextClause."""
    engine = SqlAlchemyExecutionEngine(connection_string="sqlite://")

    selectable = engine._build_selectable_from_batch_spec(
        batch_spec=RuntimeQueryBatchSpec(query=QUERY_ENDING_IN_LINE_COMMENT)
    )

    assert not _appended_sql_is_commented_out(str(selectable))
