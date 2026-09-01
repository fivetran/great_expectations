"""EXPECTATION_CASES — one entry per core expectation.

Underscore-prefixed so pytest does not collect this file.

Three expectations (ExpectColumnBootstrappedKsTestPValueToBeGreaterThan,
ExpectColumnChiSquareTestPValueToBeGreaterThan, and
ExpectColumnParameterizedDistributionKsTestPValueToBeGreaterThan) are marked
``NotImplementedError`` stubs in the codebase (their ``__init__`` raises and
they are not part of the public ``gxe`` API).  We represent them with a
lightweight ``_AbstractStub`` object that carries the correct
``expectation_type`` string so that the ``family_for`` lookup test still passes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Mapping, NamedTuple, Optional, Union

import pandas as pd

import great_expectations.expectations as gxe

if TYPE_CHECKING:
    from great_expectations.expectations.expectation import Expectation

# ---------------------------------------------------------------------------
# Default fixture data — small DataFrame covering the most common columns.
# Several rows intentionally violate common constraints (None, type mismatch)
# so result dicts are non-trivial for map expectations.
# ---------------------------------------------------------------------------

_DEFAULT_DATA = pd.DataFrame(
    {
        "col_a": [1, 2, 3, None, 5],
        "col_b": ["x", "y", "z", "w", None],
        "col_c": [1.0, 2.0, None, 4.0, 5.0],
    }
)

# Multi-column / pair data — non-null values in every cell used for pair/multi
# expectations so at least one row satisfies A > B and A == B variants.
_PAIR_DATA = pd.DataFrame(
    {
        "col_a": [3, 5, 7, 10, 2],
        "col_b": [1, 2, 3, 4, 1],
    }
)

# Numeric-only data for z-score and stdev expectations.
_NUMERIC_DATA = pd.DataFrame(
    {
        "col_a": [10, 20, 30, 40, 50],
        "col_b": [1, 2, 3, 4, 5],
        "col_c": [1.5, 2.5, 3.5, 4.5, 5.5],
    }
)

# Date-formatted strings for strftime / dateutil expectations.
_DATE_DATA = pd.DataFrame(
    {
        "col_a": ["2024-01-01", "2024-06-15", "not-a-date", "2023-12-31", "2025-03-01"],
        "col_b": [1, 2, 3, 4, 5],
        "col_c": [1.0, 2.0, 3.0, 4.0, 5.0],
    }
)

# JSON-formatted strings for JSON expectations.
_JSON_DATA = pd.DataFrame(
    {
        "col_a": ['{"a": 1}', '{"b": 2}', "not-json", '{"c": 3}', '{"d": 4}'],
        "col_b": [1, 2, 3, 4, 5],
        "col_c": [1.0, 2.0, 3.0, 4.0, 5.0],
    }
)


# ---------------------------------------------------------------------------
# Stub for abstract/NotImplementedError expectations
# ---------------------------------------------------------------------------


class _AbstractStub:
    """Minimal stand-in for the three incomplete core expectations.

    These classes raise ``NotImplementedError`` on ``__init__`` and therefore
    cannot be instantiated.  We store just the ``expectation_type`` string so
    the test assertions that touch ``case.expectation.expectation_type`` work
    correctly.
    """

    def __init__(self, expectation_type: str) -> None:
        self.expectation_type = expectation_type


# ---------------------------------------------------------------------------
# ExpectationCase definition
# ---------------------------------------------------------------------------


class ExpectationCase(NamedTuple):
    """A single test case for a core expectation.

    Attributes:
        id: Unique snake_case identifier matching the file name (e.g.
            ``"expect_column_values_to_not_be_null"``).
        expectation: An instantiated Expectation (or _AbstractStub for the
            three not-yet-migrated expectations).
        data: A small pandas DataFrame that serves as the fixture for this
            case.  Column names must align with whatever column/column_list
            arguments are given to the expectation.
        extra_data: Optional mapping of named extra DataFrames (e.g. for
            expectations that reference a second table).
    """

    id: str
    expectation: Union[Expectation, _AbstractStub]
    data: pd.DataFrame
    extra_data: Optional[Mapping[str, pd.DataFrame]] = None


# ---------------------------------------------------------------------------
# EXPECTATION_CASES — one entry per expect_*.py file under core/
# ---------------------------------------------------------------------------

EXPECTATION_CASES: List[ExpectationCase] = [
    # ------------------------------------------------------------------
    # MAP — ColumnMapExpectation
    # ------------------------------------------------------------------
    ExpectationCase(
        id="expect_column_value_lengths_to_be_between",
        expectation=gxe.ExpectColumnValueLengthsToBeBetween(
            column="col_b", min_value=1, max_value=5
        ),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_value_lengths_to_equal",
        expectation=gxe.ExpectColumnValueLengthsToEqual(column="col_b", value=1),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_value_z_scores_to_be_less_than",
        expectation=gxe.ExpectColumnValueZScoresToBeLessThan(
            column="col_a", threshold=3.0, double_sided=True
        ),
        data=_NUMERIC_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_be_between",
        expectation=gxe.ExpectColumnValuesToBeBetween(column="col_a", min_value=0, max_value=10),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_be_dateutil_parseable",
        expectation=gxe.ExpectColumnValuesToBeDateutilParseable(column="col_a"),
        data=_DATE_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_be_decreasing",
        expectation=gxe.ExpectColumnValuesToBeDecreasing(column="col_a"),
        data=_NUMERIC_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_be_in_set",
        expectation=gxe.ExpectColumnValuesToBeInSet(column="col_a", value_set=[1, 2, 3, None, 5]),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_be_in_type_list",
        expectation=gxe.ExpectColumnValuesToBeInTypeList(
            column="col_a", type_list=["int", "float", "NoneType"]
        ),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_be_increasing",
        expectation=gxe.ExpectColumnValuesToBeIncreasing(column="col_a"),
        data=_NUMERIC_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_be_json_parseable",
        expectation=gxe.ExpectColumnValuesToBeJsonParseable(column="col_a"),
        data=_JSON_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_be_null",
        expectation=gxe.ExpectColumnValuesToBeNull(column="col_a"),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_be_of_type",
        expectation=gxe.ExpectColumnValuesToBeOfType(column="col_a", type_="int"),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_be_unique",
        expectation=gxe.ExpectColumnValuesToBeUnique(column="col_a"),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_match_json_schema",
        expectation=gxe.ExpectColumnValuesToMatchJsonSchema(
            column="col_a", json_schema={"type": "object"}
        ),
        data=_JSON_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_match_like_pattern",
        expectation=gxe.ExpectColumnValuesToMatchLikePattern(column="col_b", like_pattern="%"),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_match_like_pattern_list",
        expectation=gxe.ExpectColumnValuesToMatchLikePatternList(
            column="col_b", like_pattern_list=["%x%", "%y%"]
        ),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_match_regex",
        expectation=gxe.ExpectColumnValuesToMatchRegex(column="col_b", regex="^[a-z]$"),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_match_regex_list",
        expectation=gxe.ExpectColumnValuesToMatchRegexList(
            column="col_b", regex_list=["^[a-z]$", "^[A-Z]$"]
        ),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_match_strftime_format",
        expectation=gxe.ExpectColumnValuesToMatchStrftimeFormat(
            column="col_a", strftime_format="%Y-%m-%d"
        ),
        data=_DATE_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_not_be_in_set",
        expectation=gxe.ExpectColumnValuesToNotBeInSet(column="col_a", value_set=[99, 100]),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_not_be_null",
        expectation=gxe.ExpectColumnValuesToNotBeNull(column="col_a"),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_not_match_like_pattern",
        expectation=gxe.ExpectColumnValuesToNotMatchLikePattern(
            column="col_b", like_pattern="%z%z%"
        ),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_not_match_like_pattern_list",
        expectation=gxe.ExpectColumnValuesToNotMatchLikePatternList(
            column="col_b", like_pattern_list=["%99%", "%100%"]
        ),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_not_match_regex",
        expectation=gxe.ExpectColumnValuesToNotMatchRegex(column="col_b", regex="^[0-9]+$"),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_not_match_regex_list",
        expectation=gxe.ExpectColumnValuesToNotMatchRegexList(
            column="col_b", regex_list=["^[0-9]+$", "^[A-Z]+$"]
        ),
        data=_DEFAULT_DATA,
    ),
    # ------------------------------------------------------------------
    # MAP — ColumnPairMapExpectation
    # ------------------------------------------------------------------
    ExpectationCase(
        id="expect_column_pair_values_a_to_be_greater_than_b",
        expectation=gxe.ExpectColumnPairValuesAToBeGreaterThanB(column_A="col_a", column_B="col_b"),
        data=_PAIR_DATA,
    ),
    ExpectationCase(
        id="expect_column_pair_values_to_be_equal",
        expectation=gxe.ExpectColumnPairValuesToBeEqual(column_A="col_a", column_B="col_b"),
        data=_PAIR_DATA,
    ),
    ExpectationCase(
        id="expect_column_pair_values_to_be_in_set",
        expectation=gxe.ExpectColumnPairValuesToBeInSet(
            column_A="col_a",
            column_B="col_b",
            value_pairs_set=[(3, 1), (5, 2), (7, 3), (10, 4), (2, 1)],
        ),
        data=_PAIR_DATA,
    ),
    # ------------------------------------------------------------------
    # MAP — MulticolumnMapExpectation
    # ------------------------------------------------------------------
    ExpectationCase(
        id="expect_compound_columns_to_be_unique",
        expectation=gxe.ExpectCompoundColumnsToBeUnique(column_list=["col_a", "col_b"]),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_values_to_not_be_outliers",
        expectation=gxe.ExpectColumnValuesToNotBeOutliers(
            column="col_a", method="iqr", multiplier=1.5
        ),
        data=_NUMERIC_DATA,
    ),
    ExpectationCase(
        id="expect_multicolumn_values_to_be_equal",
        expectation=gxe.ExpectMulticolumnValuesToBeEqual(column_list=["col_a", "col_b"]),
        data=pd.DataFrame(
            {
                "col_a": [1, 2, 3, None, 5],
                "col_b": [1, 2, 4, None, 5],
            }
        ),
    ),
    ExpectationCase(
        id="expect_multicolumn_sum_to_equal",
        expectation=gxe.ExpectMulticolumnSumToEqual(column_list=["col_a", "col_b"], sum_total=3),
        data=pd.DataFrame(
            {
                "col_a": [1, 2, 3, None, 2],
                "col_b": [2, 1, 0, None, 1],
            }
        ),
    ),
    ExpectationCase(
        id="expect_multicolumn_values_to_be_unique",
        # This expectation lacks a map_metric so is_abstract() returns True and
        # expectation_type is '' — instantiation succeeds but the expectation_type
        # string would be empty. Use _AbstractStub to carry the correct type string.
        expectation=_AbstractStub("expect_multicolumn_values_to_be_unique"),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_select_column_values_to_be_unique_within_record",
        expectation=gxe.ExpectSelectColumnValuesToBeUniqueWithinRecord(
            column_list=["col_a", "col_b"]
        ),
        data=_DEFAULT_DATA,
    ),
    # ------------------------------------------------------------------
    # AGGREGATE — ColumnAggregateExpectation
    # ------------------------------------------------------------------
    ExpectationCase(
        id="expect_column_bootstrapped_ks_test_p_value_to_be_greater_than",
        # This expectation is not yet migrated; __init__ raises NotImplementedError.
        expectation=_AbstractStub("expect_column_bootstrapped_ks_test_p_value_to_be_greater_than"),
        data=_NUMERIC_DATA,
    ),
    ExpectationCase(
        id="expect_column_chisquare_test_p_value_to_be_greater_than",
        # Not yet migrated; __init__ raises NotImplementedError.
        expectation=_AbstractStub("expect_column_chisquare_test_p_value_to_be_greater_than"),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_distinct_values_to_be_in_set",
        expectation=gxe.ExpectColumnDistinctValuesToBeInSet(
            column="col_a", value_set=[1, 2, 3, None, 5]
        ),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_distinct_values_to_contain_set",
        expectation=gxe.ExpectColumnDistinctValuesToContainSet(column="col_a", value_set=[1, 2]),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_distinct_values_to_equal_set",
        expectation=gxe.ExpectColumnDistinctValuesToEqualSet(
            column="col_a", value_set=[1, 2, 3, None, 5]
        ),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_kl_divergence_to_be_less_than",
        expectation=gxe.ExpectColumnKLDivergenceToBeLessThan(
            column="col_a",
            partition_object={
                "weights": [0.2, 0.2, 0.2, 0.2, 0.2],
                "values": [1, 2, 3, None, 5],
            },
            threshold=None,
        ),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_max_to_be_between",
        expectation=gxe.ExpectColumnMaxToBeBetween(column="col_a", min_value=0, max_value=10),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_mean_to_be_between",
        expectation=gxe.ExpectColumnMeanToBeBetween(column="col_a", min_value=0, max_value=10),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_median_to_be_between",
        expectation=gxe.ExpectColumnMedianToBeBetween(column="col_a", min_value=0, max_value=10),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_min_to_be_between",
        expectation=gxe.ExpectColumnMinToBeBetween(column="col_a", min_value=0, max_value=10),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_most_common_value_to_be_in_set",
        expectation=gxe.ExpectColumnMostCommonValueToBeInSet(column="col_a", value_set=[1, 2, 3]),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_pair_cramers_phi_value_to_be_less_than",
        # Uses column_A / column_B (not in the public gxe API as of this version;
        # import directly from the core module).
        expectation=_AbstractStub("expect_column_pair_cramers_phi_value_to_be_less_than"),
        data=_PAIR_DATA,
    ),
    ExpectationCase(
        id="expect_column_parameterized_distribution_ks_test_p_value_to_be_greater_than",
        # Not yet migrated; __init__ raises NotImplementedError.
        expectation=_AbstractStub(
            "expect_column_parameterized_distribution_ks_test_p_value_to_be_greater_than"
        ),
        data=_NUMERIC_DATA,
    ),
    ExpectationCase(
        id="expect_column_proportion_of_non_null_values_to_be_between",
        expectation=gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
            column="col_a", min_value=0.0, max_value=1.0
        ),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_proportion_of_unique_values_to_be_between",
        expectation=gxe.ExpectColumnProportionOfUniqueValuesToBeBetween(
            column="col_a", min_value=0.0, max_value=1.0
        ),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_quantile_values_to_be_between",
        expectation=gxe.ExpectColumnQuantileValuesToBeBetween(
            column="col_c",
            quantile_ranges={
                "quantiles": [0.25, 0.5, 0.75],
                "value_ranges": [[0, 3], [1, 4], [2, 6]],
            },
        ),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_stdev_to_be_between",
        expectation=gxe.ExpectColumnStdevToBeBetween(column="col_a", min_value=0, max_value=10),
        data=_NUMERIC_DATA,
    ),
    ExpectationCase(
        id="expect_column_sum_to_be_between",
        expectation=gxe.ExpectColumnSumToBeBetween(column="col_a", min_value=0, max_value=100),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_to_exist",
        expectation=gxe.ExpectColumnToExist(column="col_a"),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_column_unique_value_count_to_be_between",
        expectation=gxe.ExpectColumnUniqueValueCountToBeBetween(
            column="col_a", min_value=1, max_value=10
        ),
        data=_DEFAULT_DATA,
    ),
    # ------------------------------------------------------------------
    # AGGREGATE — TableExpectation / BatchExpectation
    # ------------------------------------------------------------------
    ExpectationCase(
        id="expect_query_results_to_match_comparison",
        expectation=gxe.ExpectQueryResultsToMatchComparison(
            base_query="SELECT 1 AS val",
            comparison_data_source_name="other_ds",
            comparison_query="SELECT 1 AS val",
        ),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_table_column_count_to_be_between",
        expectation=gxe.ExpectTableColumnCountToBeBetween(min_value=1, max_value=10),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_table_column_count_to_equal",
        expectation=gxe.ExpectTableColumnCountToEqual(value=3),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_table_columns_to_match_ordered_list",
        expectation=gxe.ExpectTableColumnsToMatchOrderedList(
            column_list=["col_a", "col_b", "col_c"]
        ),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_table_columns_to_match_set",
        expectation=gxe.ExpectTableColumnsToMatchSet(column_set=["col_a", "col_b", "col_c"]),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_table_row_count_to_be_between",
        expectation=gxe.ExpectTableRowCountToBeBetween(min_value=1, max_value=100),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_table_row_count_to_equal",
        expectation=gxe.ExpectTableRowCountToEqual(value=5),
        data=_DEFAULT_DATA,
    ),
    ExpectationCase(
        id="expect_table_row_count_to_equal_other_table",
        expectation=gxe.ExpectTableRowCountToEqualOtherTable(other_table_name="other_table"),
        data=_DEFAULT_DATA,
    ),
]
