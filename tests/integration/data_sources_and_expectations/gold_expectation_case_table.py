"""The populated gold-tier case table: `GOLD_CASES` and its derived key set.

This module holds the one thing `gold_expectation_cases.py` cannot: real, constructed
`Expectation` instances. Building those requires importing `great_expectations`, and
`gold_expectation_cases.py` must stay importable with no data-source dependency installed at all
(see that module's docstring). This module is the layer in between -- it imports
`great_expectations`, imports the pure data and record shape from `gold_expectation_cases.py`, and
publishes the populated table. `test_gold_expectation_suite.py` consumes `GOLD_CASES` from here; it
does not define cases itself.

Keeping the case table in its own module, rather than inline in the test module, matters as the
table grows: later work adds roughly fifty more cases here, and collapsing that growth into the
same file as the collection-time builder and the case-consuming test functions would make the test
module unreadably long.
"""

from __future__ import annotations

from typing import Final, FrozenSet, Tuple

import great_expectations.expectations as gxe
from tests.integration.data_sources_and_expectations.gold_expectation_cases import (
    EXTRA_TABLE_SELF_REFERENCE,
    GOLD_EXTRA_TABLE_NAME,
    CaseFixtureShape,
    GoldCase,
)
from tests.integration.test_utils.execution_engine_kind import ExecutionEngineKind

_SQL_ONLY: Final[FrozenSet[ExecutionEngineKind]] = frozenset({ExecutionEngineKind.SQL})
_SQL_ONLY_REASON: Final[str] = (
    "the extra-table and comparison-source harness fixtures both assert a SQL batch setup"
)

GOLD_CASES: Final[Tuple[GoldCase, ...]] = (
    GoldCase(
        key=gxe.ExpectColumnValuesToNotBeNull(column="increasing_key").expectation_type,
        passing=gxe.ExpectColumnValuesToNotBeNull(column="increasing_key"),
        failing=gxe.ExpectColumnValuesToNotBeNull(column="nullable_value"),
        fixture_shape=CaseFixtureShape.STANDARD,
    ),
    GoldCase(
        key=gxe.ExpectTableRowCountToEqualOtherTable(
            other_table_name=EXTRA_TABLE_SELF_REFERENCE
        ).expectation_type,
        # Passing: the primary table compared against itself, resolved at test time -- always
        # equal, and never mistaken for "no comparison happened" since the table is real.
        passing=gxe.ExpectTableRowCountToEqualOtherTable(
            other_table_name=EXTRA_TABLE_SELF_REFERENCE
        ),
        # Failing: the primary table (six rows) compared against the shared extra table (seven
        # rows) -- a real, known mismatch.
        failing=gxe.ExpectTableRowCountToEqualOtherTable(other_table_name=GOLD_EXTRA_TABLE_NAME),
        fixture_shape=CaseFixtureShape.EXTRA_TABLE,
        engines=_SQL_ONLY,
        engine_restriction_reason=_SQL_ONLY_REASON,
    ),
    GoldCase(
        key=gxe.ExpectQueryResultsToMatchComparison(
            base_query="SELECT increasing_key FROM {batch} ORDER BY increasing_key",
            comparison_data_source_name=EXTRA_TABLE_SELF_REFERENCE,
            comparison_query="SELECT increasing_key FROM {source_table} ORDER BY increasing_key",
        ).expectation_type,
        # Passing: base and comparison queries select the identical column from the identical
        # (self-paired) data, ordered the same way -- every row matches.
        passing=gxe.ExpectQueryResultsToMatchComparison(
            base_query="SELECT increasing_key FROM {batch} ORDER BY increasing_key",
            comparison_data_source_name=EXTRA_TABLE_SELF_REFERENCE,
            comparison_query="SELECT increasing_key FROM {source_table} ORDER BY increasing_key",
        ),
        # Failing: the comparison query selects a strict subset of the base query's rows, so the
        # match percentage falls below the (default) mostly threshold.
        failing=gxe.ExpectQueryResultsToMatchComparison(
            base_query="SELECT increasing_key FROM {batch} ORDER BY increasing_key",
            comparison_data_source_name=EXTRA_TABLE_SELF_REFERENCE,
            comparison_query=(
                "SELECT increasing_key FROM {source_table} WHERE increasing_key < 3 "
                "ORDER BY increasing_key"
            ),
        ),
        fixture_shape=CaseFixtureShape.COMPARISON,
        engines=_SQL_ONLY,
        engine_restriction_reason=_SQL_ONLY_REASON,
    ),
)
"""Every declared case. One seed case per `CaseFixtureShape` member proves the wiring end to end;
the remaining gallery expectations are added by later work."""

GOLD_CASE_KEYS: Final[FrozenSet[str]] = frozenset(case.key for case in GOLD_CASES)
"""The published case keys, derived from `GOLD_CASES` rather than hand-kept in sync with it."""
