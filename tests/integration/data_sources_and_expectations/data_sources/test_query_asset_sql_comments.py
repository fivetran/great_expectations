"""Regression tests for query assets whose raw SQL ends in a comment.

See https://github.com/fivetran/great_expectations/issues/12122. GX wraps a query
asset's raw SQL in a subquery before running metrics against it. SQLAlchemy compiles
that as the user's text pasted verbatim inside "(<text>) AS anon_1" on a single line,
so if the user's SQL ends in a line comment, the appended ")" and alias land inside
that comment and the statement is never terminated.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import pytest
import sqlalchemy as sa

import great_expectations as gx
import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.sql_datasource import SQLDatasource, TableAsset
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    PostgreSQLDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)

if TYPE_CHECKING:
    import pathlib

    from great_expectations.datasource.fluent.interfaces import Batch

COL_A = "col_a"

DATA = pd.DataFrame({COL_A: ["x", "y"]})


def _add_query_asset(batch_for_datasource: Batch, name: str, query: str) -> Batch:
    asset = batch_for_datasource.data_asset
    assert isinstance(asset, TableAsset)
    datasource = batch_for_datasource.datasource
    assert isinstance(datasource, SQLDatasource)

    query_asset = datasource.add_query_asset(name=name, query=query.format(table=asset.table_name))
    return query_asset.add_batch_definition_whole_table(f"{name}_bd").get_batch()


@parameterize_batch_for_data_sources(
    data_source_configs=[SqliteDatasourceTestConfig(), PostgreSQLDatasourceTestConfig()],
    data=DATA,
)
def test_query_asset_sql_ending_in_line_comment(batch_for_datasource: Batch) -> None:
    """A trailing `--` comment does not change what a query selects."""
    batch = _add_query_asset(
        batch_for_datasource,
        "trailing_comment_asset",
        f"SELECT {COL_A} FROM {{table}} -- only the rows we care about",
    )

    result = batch.validate(gxe.ExpectColumnValuesToNotBeNull(column=COL_A))

    assert result.success, result.exception_info


@pytest.mark.sqlite
def test_query_asset_sql_ending_in_line_comment_without_temp_table(tmp_path: pathlib.Path) -> None:
    """The same trailing-comment case above, but constructed so the query asset's raw SQL
    reaches SqlAlchemyExecutionEngine.get_domain_records() as a TextClause, exercising its
    own wrap fix directly, rather than one already converted to a Subquery further upstream
    (which is what the fixture-driven test above ends up exercising instead). This only
    happens when create_temp_table=False on the datasource, which is in fact the default for
    SQLDatasource, so this is a real, reachable path, not a contrived one, it's just not the
    one the shared test fixture takes.

    Note: as of this fix, every path that reaches get_domain_records() this way has already
    passed through _subselectable(), so this scenario happens to be covered by that fix too.
    That doesn't make get_domain_records()'s own fix untested, both are exercised here, it
    just means this specific test can't isolate one from the other with the current public
    API's set of construction paths.
    """  # FIXME CoP
    db_path = tmp_path / "test.db"

    context = gx.get_context(mode="ephemeral")
    datasource = context.data_sources.add_sqlite(
        name="ds", connection_string=f"sqlite:///{db_path}", create_temp_table=False
    )
    engine = datasource.get_execution_engine().engine
    DATA.to_sql("my_tbl", engine, index=False)

    query_asset = datasource.add_query_asset(
        name="qa", query=f"SELECT {COL_A} FROM my_tbl -- only the rows we care about"
    )
    batch = query_asset.add_batch_definition_whole_table("bd").get_batch()
    assert isinstance(batch.data.selectable, sa.TextClause), (
        "test setup no longer reaches get_domain_records() as a TextClause; this test needs "
        "updating to match whatever now does"
    )

    result = batch.validate(gxe.ExpectColumnValuesToNotBeNull(column=COL_A))

    assert result.success, result.exception_info


@parameterize_batch_for_data_sources(
    data_source_configs=[SqliteDatasourceTestConfig(), PostgreSQLDatasourceTestConfig()],
    data=DATA,
)
def test_query_asset_sql_ending_in_terminated_block_comment(batch_for_datasource: Batch) -> None:
    """A trailing, properly-closed `/* ... */` comment does not change what a query selects."""
    batch = _add_query_asset(
        batch_for_datasource,
        "terminated_block_comment_asset",
        f"SELECT {COL_A} FROM {{table}} /* only the rows we care about */",
    )

    result = batch.validate(gxe.ExpectColumnValuesToNotBeNull(column=COL_A))

    assert result.success, result.exception_info


@parameterize_batch_for_data_sources(
    data_source_configs=[SqliteDatasourceTestConfig(), PostgreSQLDatasourceTestConfig()],
    data=DATA,
)
def test_query_asset_sql_with_comment_not_at_end(batch_for_datasource: Batch) -> None:
    """A comment in the middle of a query, followed by a later clause, is unaffected."""
    batch = _add_query_asset(
        batch_for_datasource,
        "mid_query_comment_asset",
        f"SELECT {COL_A} -- the column we care about\nFROM {{table}}",
    )

    result = batch.validate(gxe.ExpectColumnValuesToNotBeNull(column=COL_A))

    assert result.success, result.exception_info
