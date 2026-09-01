"""The declarative case table for the gallery-wide expectation suite, and its shared fixture data.

This module holds pure data: a case record per expectation, the fixture-shape vocabulary a case
declares, and the data frame(s) that back every case sharing the default shape. It imports the
tier and engine vocabularies and the shipped expectation classes, but never a data-source registry
accessor, so it stays importable in a lane with no data-source dependency installed at all — the
registry-derived accounting that turns this table into a live parameterization lives beside the
test functions that consume it, not here.

Cases are collected under one shared data frame wherever possible. A shared frame means every
standard-shape case resolves to a single cached batch setup per data source per session rather than
one setup per case, so adding a case that can be expressed with an existing column is preferred to
adding a new column, and a new column changes every standard-shape case's batch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Final, FrozenSet, Optional, Tuple

import pandas as pd

from tests.integration.test_utils.execution_engine_kind import ExecutionEngineKind

if TYPE_CHECKING:
    from great_expectations.expectations.expectation import Expectation


class CaseFixtureShape(Enum):
    """The closed set of fixture arrangements a case can require.

    Every case falls into exactly one of these three shapes. A case that does not fit any of them
    is not a case this table can express; the shared frame it needs is the extension point, not a
    fourth shape.
    """

    STANDARD = "standard"
    """The shared table alone: one cached batch setup per data source."""

    EXTRA_TABLE = "extra_table"
    """The shared table plus one additional named table, set up together as a second setup shared
    by every case that needs it."""

    COMPARISON = "comparison"
    """A base source and a comparison source, both the same data source, via the multi-source
    setup."""


_ALL_ENGINES: FrozenSet[ExecutionEngineKind] = frozenset(ExecutionEngineKind)


@dataclass(frozen=True, kw_only=True)
class GoldCase:
    """One declarative case: an expectation, proven both ways, against the shared fixture.

    ``passing`` and ``failing`` are configurations of the *same* expectation type — one expected
    to report success against the shared fixture data, the other expected to report failure
    against that same data. Holding constructed instances rather than factories keeps the table
    readable as a specification of what each expectation is being asked, since construction is a
    side-effect-free model instantiation.
    """

    key: str
    """The expectation type name. Equal to a member of the registry-derived gallery set this
    table is checked against."""

    passing: Expectation
    """A configuration expected to report success against the shared fixture data."""

    failing: Expectation
    """A configuration of the same expectation expected to report failure against that data."""

    fixture_shape: CaseFixtureShape = CaseFixtureShape.STANDARD
    """Which fixture arrangement this case needs. Defaults to the shared table alone."""

    engines: FrozenSet[ExecutionEngineKind] = field(default_factory=lambda: _ALL_ENGINES)
    """The execution engines this case applies to. Applies to every engine when left at its
    default (the full set); a case that means to restrict itself declares a proper, non-empty
    subset and must also state why in ``engine_restriction_reason``."""

    engine_restriction_reason: Optional[str] = None
    """Why the expectation has no meaning on the engines ``engines`` excludes. Required whenever
    ``engines`` is a proper subset of every engine; states what does not apply, not which backend
    failed."""

    def __post_init__(self) -> None:
        if not self.engines:
            raise ValueError(
                f"Gold case {self.key!r} declares an empty engine set. A case that applies to no "
                "execution engine proves nothing; either restrict it to a non-empty subset of "
                "engines, with a reason, or leave `engines` at its default to apply to all of them."
            )


GOLD_CASES: Final[Tuple[GoldCase, ...]] = ()
"""Every declared case. Populated as expectations are added to the table; empty here by design —
an empty table still satisfies "the module imports cleanly" and "an empty case set is a state the
suite can report," both of which later work depends on being able to observe."""

GOLD_CASE_KEYS: Final[FrozenSet[str]] = frozenset(case.key for case in GOLD_CASES)
"""The published case keys, derived from ``GOLD_CASES`` rather than hand-kept in sync with it."""


# --------------------------------------------------------------------------------------------
# Shared fixture data
# --------------------------------------------------------------------------------------------
#
# One data frame serves every STANDARD case. Adding a column here changes every STANDARD case's
# batch setup, so a new case should first ask whether an existing column already expresses what it
# needs.

INCREASING_KEY_COL = "increasing_key"
"""A unique, strictly increasing integer key: uniqueness, increasing, row-count, min/max, sum, and
any case needing a well-ordered numeric column."""

DECREASING_COL = "decreasing_value"
"""A strictly decreasing integer column: the decreasing expectation, which no other column can
serve."""

FLOAT_COL = "float_value"
"""A float column with a known distribution: mean, median, stdev, quantiles, z-scores, and
between-value checks."""

CATEGORY_COL = "category"
"""A short string column drawn from a small closed value set: value-set, distinct-value,
most-common-value, length, and category checks."""

PATTERN_COL = "pattern_code"
"""A string column matching a simple anchored pattern: regex, like-pattern, and match-list
checks."""

NULLABLE_COL = "nullable_value"
"""A nullable column with a known null ratio: null, not-null, and ``mostly`` checks."""

DATE_COL = "record_date"
"""A date column: date comparisons."""

TIMESTAMP_COL = "record_timestamp"
"""A timestamp column: datetime comparisons."""

JSON_COL = "json_payload"
"""A string column holding valid JSON: JSON-parseable and JSON-schema checks."""

STRFTIME_COL = "strftime_code"
"""A string column in a fixed strftime format: strftime-format checks."""

PAIR_LOW_COL = "pair_low"
PAIR_HIGH_COL = "pair_high"
"""A pair of numeric columns with a known ordering between them (``pair_low`` < ``pair_high`` in
every row): column-pair comparisons."""

MULTICOLUMN_A_COL = "multicolumn_a"
MULTICOLUMN_B_COL = "multicolumn_b"
MULTICOLUMN_C_COL = "multicolumn_c"
"""Three numeric columns with a known row sum and no duplicate row: multicolumn sum and
multicolumn uniqueness."""

MULTICOLUMN_ROW_SUM = 30
"""The known, constant sum of ``multicolumn_a`` + ``multicolumn_b`` + ``multicolumn_c`` in every
row of the shared frame."""

_ROW_COUNT = 6

GOLD_FIXTURE_DATA: pd.DataFrame = pd.DataFrame(
    {
        INCREASING_KEY_COL: [1, 2, 3, 4, 5, 6],
        DECREASING_COL: [60, 50, 40, 30, 20, 10],
        FLOAT_COL: [10.0, 12.5, 15.0, 17.5, 20.0, 22.5],
        CATEGORY_COL: ["red", "green", "blue", "red", "green", "blue"],
        PATTERN_COL: ["A100", "A200", "A300", "A400", "A500", "A600"],
        NULLABLE_COL: [1.0, None, 3.0, None, 5.0, 6.0],
        DATE_COL: [
            date(2024, 1, 1),
            date(2024, 1, 2),
            date(2024, 1, 3),
            date(2024, 1, 4),
            date(2024, 1, 5),
            date(2024, 1, 6),
        ],
        TIMESTAMP_COL: [
            datetime(2024, 1, 1, 8, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 2, 8, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 3, 8, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 4, 8, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 5, 8, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 6, 8, 0, 0, tzinfo=timezone.utc),
        ],
        JSON_COL: [
            '{"a": 1}',
            '{"a": 2}',
            '{"a": 3}',
            '{"a": 4}',
            '{"a": 5}',
            '{"a": 6}',
        ],
        STRFTIME_COL: [
            "2024-01-01",
            "2024-01-02",
            "2024-01-03",
            "2024-01-04",
            "2024-01-05",
            "2024-01-06",
        ],
        PAIR_LOW_COL: [1, 2, 3, 4, 5, 6],
        PAIR_HIGH_COL: [10, 20, 30, 40, 50, 60],
        MULTICOLUMN_A_COL: [10, 9, 8, 7, 6, 5],
        MULTICOLUMN_B_COL: [10, 11, 12, 13, 14, 15],
        MULTICOLUMN_C_COL: [10, 10, 10, 10, 10, 10],
    }
)
"""The one shared frame every ``STANDARD``-shape case validates against. Carries no additional
tables — the ``EXTRA_TABLE`` shape's second table lives in ``GOLD_EXTRA_TABLE_DATA`` below, kept
separate so this frame alone still resolves every ``STANDARD`` case to one cached batch setup."""


def _validate_gold_fixture_data() -> None:
    """Check the invariants the shared frame's docstrings promise, as real (non-strippable)
    checks -- a bare module-level ``assert`` is removed entirely under ``python -O``, silently
    dropping the guarantee for every consumer of this module in an optimized run."""
    if len(GOLD_FIXTURE_DATA) != _ROW_COUNT:
        raise ValueError(
            f"GOLD_FIXTURE_DATA must have exactly {_ROW_COUNT} rows, got {len(GOLD_FIXTURE_DATA)}."
        )
    row_sums = (
        GOLD_FIXTURE_DATA[MULTICOLUMN_A_COL]
        + GOLD_FIXTURE_DATA[MULTICOLUMN_B_COL]
        + GOLD_FIXTURE_DATA[MULTICOLUMN_C_COL]
    )
    if not (row_sums == MULTICOLUMN_ROW_SUM).all():
        raise ValueError(
            "Every row of multicolumn_a + multicolumn_b + multicolumn_c must equal "
            f"MULTICOLUMN_ROW_SUM ({MULTICOLUMN_ROW_SUM}); got {row_sums.tolist()}."
        )
    if (
        GOLD_FIXTURE_DATA[[MULTICOLUMN_A_COL, MULTICOLUMN_B_COL, MULTICOLUMN_C_COL]]
        .duplicated()
        .any()
    ):
        raise ValueError(
            "multicolumn_a/multicolumn_b/multicolumn_c must have no duplicate row, for the "
            "multicolumn uniqueness case."
        )


_validate_gold_fixture_data()


GOLD_EXTRA_TABLE_NAME = "gold_extra_table"
"""The name every ``EXTRA_TABLE``-shape case's second table is set up under."""

EXTRA_TABLE_KEY_COL = "extra_key"
EXTRA_TABLE_VALUE_COL = "extra_value"

GOLD_EXTRA_TABLE_DATA: pd.DataFrame = pd.DataFrame(
    {
        EXTRA_TABLE_KEY_COL: [1, 2, 3, 4, 5, 6],
        EXTRA_TABLE_VALUE_COL: ["a", "b", "c", "d", "e", "f"],
    }
)
"""The one additional table shared by every ``EXTRA_TABLE``-shape case, so those cases collapse to
a single second setup rather than one per case."""
