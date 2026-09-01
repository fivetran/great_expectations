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

_PANDAS_ONLY: Final[FrozenSet[ExecutionEngineKind]] = frozenset({ExecutionEngineKind.PANDAS})

_PANDAS_AND_SPARK: Final[FrozenSet[ExecutionEngineKind]] = frozenset(
    {ExecutionEngineKind.PANDAS, ExecutionEngineKind.SPARK}
)
_NO_SQL_PROVIDER_REASON: Final[str] = (
    "the shipped package registers no SQL metric provider for this expectation"
)
_PANDAS_ONLY_PROVIDER_REASON: Final[str] = (
    "the shipped package registers a metric provider for this expectation on the pandas engine "
    "only, with neither a SQL nor a Spark provider"
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
    # ----------------------------------------------------------------------------------------
    # Column-map expectations
    # ----------------------------------------------------------------------------------------
    GoldCase(
        key=gxe.ExpectColumnValueLengthsToBeBetween(
            column="pattern_code", min_value=4, max_value=4
        ).expectation_type,
        # Passing: every `pattern_code` value is exactly four characters ("A100" .. "A600").
        passing=gxe.ExpectColumnValueLengthsToBeBetween(
            column="pattern_code", min_value=4, max_value=4
        ),
        # Failing: no value is five characters long.
        failing=gxe.ExpectColumnValueLengthsToBeBetween(
            column="pattern_code", min_value=5, max_value=10
        ),
    ),
    GoldCase(
        key=gxe.ExpectColumnValueLengthsToEqual(column="pattern_code", value=4).expectation_type,
        passing=gxe.ExpectColumnValueLengthsToEqual(column="pattern_code", value=4),
        failing=gxe.ExpectColumnValueLengthsToEqual(column="pattern_code", value=5),
    ),
    GoldCase(
        key=gxe.ExpectColumnValueZScoresToBeLessThan(
            column="float_value", threshold=2.0, double_sided=True
        ).expectation_type,
        # `float_value` is an evenly-spaced sequence, so every z-score sits well under 2.
        passing=gxe.ExpectColumnValueZScoresToBeLessThan(
            column="float_value", threshold=2.0, double_sided=True
        ),
        # A threshold this small excludes every non-zero z-score.
        failing=gxe.ExpectColumnValueZScoresToBeLessThan(
            column="float_value", threshold=0.01, double_sided=True
        ),
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToBeBetween(
            column="float_value", min_value=10.0, max_value=22.5
        ).expectation_type,
        passing=gxe.ExpectColumnValuesToBeBetween(
            column="float_value", min_value=10.0, max_value=22.5
        ),
        # The column's max (22.5) exceeds this upper bound.
        failing=gxe.ExpectColumnValuesToBeBetween(
            column="float_value", min_value=10.0, max_value=20.0
        ),
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToBeDateutilParseable(column="strftime_code").expectation_type,
        # `strftime_code` values ("2024-01-01" ...) are dateutil-parseable dates.
        passing=gxe.ExpectColumnValuesToBeDateutilParseable(column="strftime_code"),
        # `category` values ("red", "green", "blue") are not parseable as dates.
        failing=gxe.ExpectColumnValuesToBeDateutilParseable(column="category"),
        engines=_PANDAS_ONLY,
        engine_restriction_reason=_PANDAS_ONLY_PROVIDER_REASON,
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToBeDecreasing(column="decreasing_value").expectation_type,
        passing=gxe.ExpectColumnValuesToBeDecreasing(column="decreasing_value"),
        # `increasing_key` is strictly increasing, not decreasing.
        failing=gxe.ExpectColumnValuesToBeDecreasing(column="increasing_key"),
        engines=_PANDAS_AND_SPARK,
        engine_restriction_reason=_NO_SQL_PROVIDER_REASON,
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToBeInSet(
            column="category", value_set=["red", "green", "blue"]
        ).expectation_type,
        passing=gxe.ExpectColumnValuesToBeInSet(
            column="category", value_set=["red", "green", "blue"]
        ),
        # `category` also holds "green" and "blue", outside this narrower set.
        failing=gxe.ExpectColumnValuesToBeInSet(column="category", value_set=["red"]),
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToBeInTypeList(
            column="increasing_key", type_list=["INTEGER", "BIGINT", "SMALLINT"]
        ).expectation_type,
        # `increasing_key` is an integer column under every SQL backend this table runs against.
        passing=gxe.ExpectColumnValuesToBeInTypeList(
            column="increasing_key", type_list=["INTEGER", "BIGINT", "SMALLINT"]
        ),
        # No backend registers an integer column under a character type name.
        failing=gxe.ExpectColumnValuesToBeInTypeList(
            column="increasing_key", type_list=["VARCHAR"]
        ),
        engines=_SQL_ONLY,
        engine_restriction_reason=(
            "the type name vocabulary this case checks against is SQL dialect type names, which "
            "have no meaning on a non-SQL engine"
        ),
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToBeIncreasing(column="increasing_key").expectation_type,
        passing=gxe.ExpectColumnValuesToBeIncreasing(column="increasing_key"),
        # `decreasing_value` is strictly decreasing, not increasing.
        failing=gxe.ExpectColumnValuesToBeIncreasing(column="decreasing_value"),
        engines=_PANDAS_AND_SPARK,
        engine_restriction_reason=_NO_SQL_PROVIDER_REASON,
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToBeJsonParseable(column="json_payload").expectation_type,
        passing=gxe.ExpectColumnValuesToBeJsonParseable(column="json_payload"),
        # `category` values are plain strings, not JSON documents.
        failing=gxe.ExpectColumnValuesToBeJsonParseable(column="category"),
        engines=_PANDAS_AND_SPARK,
        engine_restriction_reason=_NO_SQL_PROVIDER_REASON,
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToBeNull(column="nullable_value", mostly=0.3).expectation_type,
        # Two of six `nullable_value` rows are null (0.333...), clearing a 0.3 `mostly` floor.
        passing=gxe.ExpectColumnValuesToBeNull(column="nullable_value", mostly=0.3),
        # The default `mostly` (1.0) demands every row be null; four of six are not.
        failing=gxe.ExpectColumnValuesToBeNull(column="nullable_value"),
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToBeOfType(
            column="increasing_key", type_="INTEGER"
        ).expectation_type,
        passing=gxe.ExpectColumnValuesToBeOfType(column="increasing_key", type_="INTEGER"),
        failing=gxe.ExpectColumnValuesToBeOfType(column="increasing_key", type_="VARCHAR"),
        engines=_SQL_ONLY,
        engine_restriction_reason=(
            "the type name this case checks against is a SQL dialect type name, which has no "
            "meaning on a non-SQL engine"
        ),
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToBeUnique(column="increasing_key").expectation_type,
        passing=gxe.ExpectColumnValuesToBeUnique(column="increasing_key"),
        # `category` repeats "red", "green", and "blue" across six rows.
        failing=gxe.ExpectColumnValuesToBeUnique(column="category"),
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToMatchJsonSchema(
            column="json_payload",
            json_schema={
                "type": "object",
                "properties": {"a": {"type": "number"}},
                "required": ["a"],
            },
        ).expectation_type,
        passing=gxe.ExpectColumnValuesToMatchJsonSchema(
            column="json_payload",
            json_schema={
                "type": "object",
                "properties": {"a": {"type": "number"}},
                "required": ["a"],
            },
        ),
        # `a` is always a number, never a string.
        failing=gxe.ExpectColumnValuesToMatchJsonSchema(
            column="json_payload",
            json_schema={
                "type": "object",
                "properties": {"a": {"type": "string"}},
                "required": ["a"],
            },
        ),
        engines=_PANDAS_AND_SPARK,
        engine_restriction_reason=_NO_SQL_PROVIDER_REASON,
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToMatchLikePattern(
            column="pattern_code", like_pattern="A%"
        ).expectation_type,
        passing=gxe.ExpectColumnValuesToMatchLikePattern(column="pattern_code", like_pattern="A%"),
        # No `pattern_code` value starts with "B".
        failing=gxe.ExpectColumnValuesToMatchLikePattern(column="pattern_code", like_pattern="B%"),
        engines=_SQL_ONLY,
        engine_restriction_reason="a SQL `LIKE` pattern has no meaning on a non-SQL engine",
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToMatchLikePatternList(
            column="pattern_code",
            like_pattern_list=["A1%", "A2%", "A3%", "A4%", "A5%", "A6%"],
            match_on="any",
        ).expectation_type,
        # Each row matches exactly one of these six patterns.
        passing=gxe.ExpectColumnValuesToMatchLikePatternList(
            column="pattern_code",
            like_pattern_list=["A1%", "A2%", "A3%", "A4%", "A5%", "A6%"],
            match_on="any",
        ),
        # No row starts with "B".
        failing=gxe.ExpectColumnValuesToMatchLikePatternList(
            column="pattern_code", like_pattern_list=["B%"], match_on="any"
        ),
        engines=_SQL_ONLY,
        engine_restriction_reason="a SQL `LIKE` pattern has no meaning on a non-SQL engine",
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToMatchRegex(
            column="pattern_code", regex=r"^A[0-9]{3}$"
        ).expectation_type,
        passing=gxe.ExpectColumnValuesToMatchRegex(column="pattern_code", regex=r"^A[0-9]{3}$"),
        # No `pattern_code` value starts with "B".
        failing=gxe.ExpectColumnValuesToMatchRegex(column="pattern_code", regex=r"^B"),
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToMatchRegexList(
            column="pattern_code", regex_list=[r"^A", r"[0-9]{3}$"], match_on="all"
        ).expectation_type,
        passing=gxe.ExpectColumnValuesToMatchRegexList(
            column="pattern_code", regex_list=[r"^A", r"[0-9]{3}$"], match_on="all"
        ),
        # No value matches a leading "B".
        failing=gxe.ExpectColumnValuesToMatchRegexList(
            column="pattern_code", regex_list=[r"^B"], match_on="all"
        ),
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToMatchStrftimeFormat(
            column="strftime_code", strftime_format="%Y-%m-%d"
        ).expectation_type,
        passing=gxe.ExpectColumnValuesToMatchStrftimeFormat(
            column="strftime_code", strftime_format="%Y-%m-%d"
        ),
        # `strftime_code` values are not slash-delimited.
        failing=gxe.ExpectColumnValuesToMatchStrftimeFormat(
            column="strftime_code", strftime_format="%m/%d/%Y"
        ),
        engines=_PANDAS_AND_SPARK,
        engine_restriction_reason=_NO_SQL_PROVIDER_REASON,
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToNotBeInSet(
            column="category", value_set=["purple"]
        ).expectation_type,
        # `category` never holds "purple".
        passing=gxe.ExpectColumnValuesToNotBeInSet(column="category", value_set=["purple"]),
        # `category` does hold "red".
        failing=gxe.ExpectColumnValuesToNotBeInSet(column="category", value_set=["red"]),
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToNotBeOutliers(
            column="float_value", method="std", multiplier=2.0
        ).expectation_type,
        # `float_value` is an evenly-spaced sequence with no point more than two standard
        # deviations from the mean.
        passing=gxe.ExpectColumnValuesToNotBeOutliers(
            column="float_value", method="std", multiplier=2.0
        ),
        # A near-zero multiplier admits only values equal to the mean, flagging the rest.
        failing=gxe.ExpectColumnValuesToNotBeOutliers(
            column="float_value", method="std", multiplier=0.01
        ),
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToNotMatchLikePattern(
            column="pattern_code", like_pattern="B%"
        ).expectation_type,
        passing=gxe.ExpectColumnValuesToNotMatchLikePattern(
            column="pattern_code", like_pattern="B%"
        ),
        # Every `pattern_code` value starts with "A".
        failing=gxe.ExpectColumnValuesToNotMatchLikePattern(
            column="pattern_code", like_pattern="A%"
        ),
        engines=_SQL_ONLY,
        engine_restriction_reason="a SQL `LIKE` pattern has no meaning on a non-SQL engine",
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToNotMatchLikePatternList(
            column="pattern_code", like_pattern_list=["B%", "C%"]
        ).expectation_type,
        passing=gxe.ExpectColumnValuesToNotMatchLikePatternList(
            column="pattern_code", like_pattern_list=["B%", "C%"]
        ),
        # Every value matches one of these six "A"-prefixed patterns.
        failing=gxe.ExpectColumnValuesToNotMatchLikePatternList(
            column="pattern_code",
            like_pattern_list=["A1%", "A2%", "A3%", "A4%", "A5%", "A6%"],
        ),
        engines=_SQL_ONLY,
        engine_restriction_reason="a SQL `LIKE` pattern has no meaning on a non-SQL engine",
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToNotMatchRegex(
            column="pattern_code", regex=r"^B"
        ).expectation_type,
        passing=gxe.ExpectColumnValuesToNotMatchRegex(column="pattern_code", regex=r"^B"),
        # Every `pattern_code` value starts with "A".
        failing=gxe.ExpectColumnValuesToNotMatchRegex(column="pattern_code", regex=r"^A"),
    ),
    GoldCase(
        key=gxe.ExpectColumnValuesToNotMatchRegexList(
            column="pattern_code", regex_list=[r"^B", r"^C"]
        ).expectation_type,
        passing=gxe.ExpectColumnValuesToNotMatchRegexList(
            column="pattern_code", regex_list=[r"^B", r"^C"]
        ),
        # Every `pattern_code` value starts with "A".
        failing=gxe.ExpectColumnValuesToNotMatchRegexList(
            column="pattern_code", regex_list=[r"^A"]
        ),
    ),
)
"""Every declared case. One seed case per `CaseFixtureShape` member proves the wiring end to end;
the column-map expectation family fills out most of the gallery, and the remaining families are
added by later work."""

GOLD_CASE_KEYS: Final[FrozenSet[str]] = frozenset(case.key for case in GOLD_CASES)
"""The published case keys, derived from `GOLD_CASES` rather than hand-kept in sync with it."""
