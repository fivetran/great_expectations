"""Query assets whose SQL carries a comment.

Great Expectations wraps a query asset's SQL in a subquery, ``(<query>) AS anon_1``, before
running metrics against it, appending the wrapping syntax to the user's raw text. SQL that ends
in a line comment therefore used to put the appended closing paren and alias *inside* that
comment, leaving the statement unterminated and rejected by the database on every SQL backend.

See https://github.com/fivetran/great_expectations/issues/12122.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.sql_datasource import SQLDatasource, TableAsset
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import SQL_DATA_SOURCES

if TYPE_CHECKING:
    from great_expectations.core.expectation_validation_result import (
        ExpectationValidationResult,
    )
    from great_expectations.datasource.fluent.interfaces import Batch

COL_A = "col_a"

DATA = pd.DataFrame({COL_A: ["x", "y"]})


def _validate_query_asset(batch: Batch, name: str, query: str) -> ExpectationValidationResult:
    """Validate `query` as a query asset on the same datasource as `batch`."""
    datasource = batch.datasource
    assert isinstance(datasource, SQLDatasource)

    query_asset = datasource.add_query_asset(name=name, query=query)
    query_batch = query_asset.add_batch_definition_whole_table(f"{name}_bd").get_batch()
    return query_batch.validate(gxe.ExpectColumnValuesToNotBeNull(column=COL_A))


def _table_name(batch: Batch) -> str:
    asset = batch.data_asset
    assert isinstance(asset, TableAsset)
    return asset.table_name


@parameterize_batch_for_data_sources(data_source_configs=SQL_DATA_SOURCES, data=DATA)
def test_query_asset_sql_ending_in_line_comment(batch_for_datasource: Batch) -> None:
    """A trailing line comment does not change what a query selects, so it must not change the
    result of validating a batch from that query."""
    table = _table_name(batch_for_datasource)

    without_comment = _validate_query_asset(
        batch_for_datasource,
        name="no_trailing_comment_asset",
        query=f"SELECT {COL_A} FROM {table}",
    )
    with_comment = _validate_query_asset(
        batch_for_datasource,
        name="trailing_comment_asset",
        query=f"SELECT {COL_A} FROM {table} -- only the rows we care about",
    )

    assert with_comment.success, with_comment.exception_info
    assert with_comment.success == without_comment.success
    assert with_comment.result == without_comment.result


@parameterize_batch_for_data_sources(data_source_configs=SQL_DATA_SOURCES, data=DATA)
def test_query_asset_sql_with_comment_before_the_end(batch_for_datasource: Batch) -> None:
    """A comment that is followed by more SQL was never affected by the subquery wrapping, and
    stays unaffected."""
    table = _table_name(batch_for_datasource)

    result = _validate_query_asset(
        batch_for_datasource,
        name="interior_comment_asset",
        query=f"SELECT {COL_A} -- the only column we need\nFROM {table}",
    )

    assert result.success, result.exception_info
