"""Integration tests for MySQL.

Covers behavior that only reproduces against a live MySQL server. MySQL refuses to
reference the same temporary table more than once in a single statement ("Can't reopen
table"), so any metric whose SQL reads the batch twice fails when the batch has been
materialized into a temporary table.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Iterator

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations import get_context
from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa

if TYPE_CHECKING:
    from great_expectations.core.expectation_validation_result import (
        ExpectationValidationResult,
    )
    from great_expectations.datasource.fluent.interfaces import Batch

pytestmark = pytest.mark.mysql

CONNECTION_STRING = "mysql+pymysql://root@localhost/test_ci"

ROW_ID = "row_id"
DUPLICATE_VALUES = "duplicate_values"

DATA = pd.DataFrame(
    {
        ROW_ID: [1, 2, 3],
        DUPLICATE_VALUES: [100, 100, 200],
    }
)


@pytest.fixture
def temp_table_batch() -> Iterator[Batch]:
    """A batch backed by a temporary table.

    `create_temp_table=True` on a query asset makes GX materialize the batch into a
    temporary table, which is the configuration that exposes MySQL's single-reference
    restriction.
    """
    engine = sa.create_engine(CONNECTION_STRING)
    table_name = f"gx_ci_test_{uuid.uuid4().hex[:12]}"
    try:
        DATA.to_sql(table_name, engine, index=False)
        context = get_context(mode="ephemeral")
        datasource = context.data_sources.add_sql(
            name="mysql_temp_table_datasource",
            connection_string=CONNECTION_STRING,
            create_temp_table=True,
        )
        asset = datasource.add_query_asset(
            name="mysql_temp_table_asset",
            query=f"SELECT * FROM {table_name}",
        )
        yield asset.add_batch_definition_whole_table("batch_definition").get_batch()
    finally:
        with engine.begin() as connection:
            connection.exec_driver_sql(f"DROP TABLE IF EXISTS {table_name}")
        engine.dispose()


def _assert_no_metric_exceptions(result: ExpectationValidationResult) -> None:
    """Fail loudly if any metric raised instead of producing a value."""
    exception_info = result.exception_info or {}
    if "raised_exception" in exception_info:
        assert not exception_info["raised_exception"], exception_info
    else:
        for info in exception_info.values():
            assert not (info or {}).get("raised_exception"), info


def test_unique_unexpected_index_list_on_temp_table_batch(temp_table_batch: Batch) -> None:
    """Index-list retrieval must read a temp-table batch only once per statement."""
    result = temp_table_batch.validate(
        gxe.ExpectColumnValuesToBeUnique(column=DUPLICATE_VALUES),
        result_format={
            "result_format": "COMPLETE",
            "unexpected_index_column_names": [ROW_ID],
        },
    )

    _assert_no_metric_exceptions(result)
    assert not result.success
    assert result.result["unexpected_count"] == 2
    assert sorted(entry[ROW_ID] for entry in result.result["unexpected_index_list"]) == [1, 2]


def test_unique_unexpected_rows_on_temp_table_batch(temp_table_batch: Batch) -> None:
    """Full-row retrieval must read a temp-table batch only once per statement."""
    result = temp_table_batch.validate(
        gxe.ExpectColumnValuesToBeUnique(column=DUPLICATE_VALUES),
        result_format={"result_format": "SUMMARY", "include_unexpected_rows": True},
    )

    _assert_no_metric_exceptions(result)
    assert not result.success
    unexpected_rows = sorted(result.result["unexpected_rows"], key=lambda row: row[ROW_ID])
    assert unexpected_rows == [
        {ROW_ID: 1, DUPLICATE_VALUES: 100},
        {ROW_ID: 2, DUPLICATE_VALUES: 100},
    ]
