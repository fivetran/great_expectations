"""Dispatcher for typed validation result schemas.

Public API:
    as_typed(result_dict, *, expectation_type, result_format, engine_hint=None) -> Result
    family_for(expectation_type: str) -> str
    Result  (Union alias)
    ParseError  (exception)

All four are re-exported from ``validation_result_schemas/__init__.py``.

Import rules (enforced by ruff banned-api):
- Pydantic symbols come exclusively from ``great_expectations.compatibility.pydantic``.
- No PEP 604 unions (``X | Y``); use ``Optional[X]`` or ``Union[X, Y]``.
- No direct ``import pydantic``.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

from great_expectations.compatibility import pydantic
from great_expectations.core.result_format import ResultFormat
from great_expectations.core.validation_result_schemas.schemas.aggregate_result import (
    AggregateBasicResult,
    AggregateBooleanOnlyResult,
    AggregateCompleteResult,
    AggregateSummaryResult,
)
from great_expectations.core.validation_result_schemas.schemas.map_result import (
    MapBasicResult,
    MapBooleanOnlyResult,
    MapCompleteResult,
    MapSummaryResult,
)
from great_expectations.core.validation_result_schemas.schemas.per_expectation_overrides import (
    ExpectColumnValuesToBeOfTypeSqlSparkResult,
)

# ---------------------------------------------------------------------------
# Public type alias
# ---------------------------------------------------------------------------

Result = Union[
    MapBooleanOnlyResult,
    MapBasicResult,
    MapSummaryResult,
    MapCompleteResult,
    AggregateBooleanOnlyResult,
    AggregateBasicResult,
    AggregateSummaryResult,
    AggregateCompleteResult,
    ExpectColumnValuesToBeOfTypeSqlSparkResult,
]

# ---------------------------------------------------------------------------
# ParseError
# ---------------------------------------------------------------------------


class ParseError(Exception):
    """Raised when as_typed cannot match result_dict to a registered schema variant.

    Wraps pydantic.ValidationError; message names the unmatched fields and the
    candidate variant(s) that were tried.
    """


# Module-level error message templates (TRY003: avoid long messages outside exception class).
def _override_parse_error_msg(
    expectation_type: str, eff_engine: Optional[str], cls_name: str, exc: object
) -> str:
    return f"Failed to parse {expectation_type!r} with engine={eff_engine!r} as {cls_name}: {exc}"


def _family_parse_error_msg(
    expectation_type: str, fmt_value: str, cls_name: str, exc: object
) -> str:
    return f"Failed to parse {expectation_type!r} ({fmt_value}) as {cls_name}: {exc}"


# ---------------------------------------------------------------------------
# _FAMILY_TABLE — hand-authored; covers all 60 core expectations
# ---------------------------------------------------------------------------
#
# Map expectations: those extending ColumnMapExpectation, ColumnPairMapExpectation,
# or MulticolumnMapExpectation (32 total).
#
# Aggregate expectations: everything else — ColumnAggregateExpectation,
# BatchExpectation, TableExpectation, etc. (28 total).

_FAMILY_TABLE: Dict[str, str] = {
    # ---- MAP (ColumnMapExpectation) ----------------------------------------
    "expect_column_value_lengths_to_be_between": "map",
    "expect_column_value_lengths_to_equal": "map",
    "expect_column_value_z_scores_to_be_less_than": "map",
    "expect_column_values_to_be_between": "map",
    "expect_column_values_to_be_dateutil_parseable": "map",
    "expect_column_values_to_be_decreasing": "map",
    "expect_column_values_to_be_in_set": "map",
    "expect_column_values_to_be_in_type_list": "map",
    "expect_column_values_to_be_increasing": "map",
    "expect_column_values_to_be_json_parseable": "map",
    "expect_column_values_to_be_null": "map",
    "expect_column_values_to_be_of_type": "map",
    "expect_column_values_to_be_unique": "map",
    "expect_column_values_to_not_be_outliers": "map",
    "expect_column_values_to_match_json_schema": "map",
    "expect_column_values_to_match_like_pattern": "map",
    "expect_column_values_to_match_like_pattern_list": "map",
    "expect_column_values_to_match_regex": "map",
    "expect_column_values_to_match_regex_list": "map",
    "expect_column_values_to_match_strftime_format": "map",
    "expect_column_values_to_not_be_in_set": "map",
    "expect_column_values_to_not_be_null": "map",
    "expect_column_values_to_not_match_like_pattern": "map",
    "expect_column_values_to_not_match_like_pattern_list": "map",
    "expect_column_values_to_not_match_regex": "map",
    "expect_column_values_to_not_match_regex_list": "map",
    # ---- MAP (ColumnPairMapExpectation) ------------------------------------
    "expect_column_pair_values_a_to_be_greater_than_b": "map",
    "expect_column_pair_values_to_be_equal": "map",
    "expect_column_pair_values_to_be_in_set": "map",
    # ---- MAP (MulticolumnMapExpectation) -----------------------------------
    "expect_compound_columns_to_be_unique": "map",
    "expect_multicolumn_sum_to_equal": "map",
    "expect_multicolumn_values_to_be_equal": "map",
    "expect_multicolumn_values_to_be_unique": "map",
    "expect_select_column_values_to_be_unique_within_record": "map",
    # ---- AGGREGATE (ColumnAggregateExpectation) ----------------------------
    "expect_column_bootstrapped_ks_test_p_value_to_be_greater_than": "aggregate",
    "expect_column_chisquare_test_p_value_to_be_greater_than": "aggregate",
    "expect_column_distinct_values_to_be_in_set": "aggregate",
    "expect_column_distinct_values_to_contain_set": "aggregate",
    "expect_column_distinct_values_to_equal_set": "aggregate",
    "expect_column_kl_divergence_to_be_less_than": "aggregate",
    "expect_column_max_to_be_between": "aggregate",
    "expect_column_mean_to_be_between": "aggregate",
    "expect_column_median_to_be_between": "aggregate",
    "expect_column_min_to_be_between": "aggregate",
    "expect_column_most_common_value_to_be_in_set": "aggregate",
    "expect_column_pair_cramers_phi_value_to_be_less_than": "aggregate",
    "expect_column_parameterized_distribution_ks_test_p_value_to_be_greater_than": "aggregate",
    "expect_column_proportion_of_non_null_values_to_be_between": "aggregate",
    "expect_column_proportion_of_unique_values_to_be_between": "aggregate",
    "expect_column_quantile_values_to_be_between": "aggregate",
    "expect_column_stdev_to_be_between": "aggregate",
    "expect_column_sum_to_be_between": "aggregate",
    "expect_column_to_exist": "aggregate",
    "expect_column_unique_value_count_to_be_between": "aggregate",
    # ---- AGGREGATE (TableExpectation / BatchExpectation) -------------------
    "expect_query_results_to_match_comparison": "aggregate",
    "expect_table_column_count_to_be_between": "aggregate",
    "expect_table_column_count_to_equal": "aggregate",
    "expect_table_columns_to_match_ordered_list": "aggregate",
    "expect_table_columns_to_match_set": "aggregate",
    "expect_table_row_count_to_be_between": "aggregate",
    "expect_table_row_count_to_equal": "aggregate",
    "expect_table_row_count_to_equal_other_table": "aggregate",
}

# ---------------------------------------------------------------------------
# _OVERRIDE_TABLE — per-expectation engine-specific class overrides
# ---------------------------------------------------------------------------

_OVERRIDE_TABLE: Dict[str, Dict[str, Any]] = {
    "expect_column_values_to_be_of_type": {
        "sql": ExpectColumnValuesToBeOfTypeSqlSparkResult,
        "spark": ExpectColumnValuesToBeOfTypeSqlSparkResult,
    }
}

# ---------------------------------------------------------------------------
# Format dispatch tables
# ---------------------------------------------------------------------------

_FORMAT_MAP: Dict[str, Dict[ResultFormat, Any]] = {
    "map": {
        ResultFormat.BOOLEAN_ONLY: MapBooleanOnlyResult,
        ResultFormat.BASIC: MapBasicResult,
        ResultFormat.SUMMARY: MapSummaryResult,
        ResultFormat.COMPLETE: MapCompleteResult,
    },
    "aggregate": {
        ResultFormat.BOOLEAN_ONLY: AggregateBooleanOnlyResult,
        ResultFormat.BASIC: AggregateBasicResult,
        ResultFormat.SUMMARY: AggregateSummaryResult,
        ResultFormat.COMPLETE: AggregateCompleteResult,
    },
}


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def family_for(expectation_type: str) -> str:
    """Return ``'map'`` or ``'aggregate'`` for the given expectation type.

    Falls back to ``'aggregate'`` for unknown types so that novel / third-party
    expectations degrade gracefully rather than raising a hard error.
    """
    return _FAMILY_TABLE.get(expectation_type, "aggregate")


def as_typed(
    result_dict: Dict[str, Any],
    *,
    expectation_type: str,
    result_format: ResultFormat,
    engine_hint: Optional[str] = None,
) -> Result:
    """Dispatch ``result_dict`` to the matching schema variant and return the parsed model.

    Resolution order:
      1. Normalise ``engine_hint``: SQL sniffing when ``engine_hint is None`` and
         ``unexpected_index_query`` is present in ``result_dict``.
      2. Per-expectation override table (e.g. SQL/Spark path for
         ``expect_column_values_to_be_of_type``).
      3. Family-based dispatch via ``_FORMAT_MAP[family][result_format]``.

    Raises:
        ParseError: when pydantic construction fails; message names the
            candidate class and the validation error.
    """
    # 1. Normalise engine_hint — SQL sniffing
    eff_engine = engine_hint
    if eff_engine is None and "unexpected_index_query" in result_dict:
        eff_engine = "sql"

    # 2. Per-expectation override
    override_engines = _OVERRIDE_TABLE.get(expectation_type, {})
    if eff_engine in override_engines:
        schema_cls = override_engines[eff_engine]
        try:
            return schema_cls(**result_dict)
        except pydantic.ValidationError as exc:
            raise ParseError(
                _override_parse_error_msg(expectation_type, eff_engine, schema_cls.__name__, exc)
            ) from exc

    # 3. Family-based dispatch
    family = family_for(expectation_type)
    schema_cls = _FORMAT_MAP[family][result_format]

    # Pass engine_hint into the model only for map-family schemas.  Map schemas
    # declare ``engine_hint`` as a field (MapResultBase) so that root validators
    # can enforce SQL-required fields.  Aggregate schemas do not declare the field
    # and use ``extra = Extra.forbid``, so injecting it would raise a ValidationError.
    data = dict(result_dict)
    if eff_engine is not None and family == "map":
        data["engine_hint"] = eff_engine

    try:
        return schema_cls(**data)
    except pydantic.ValidationError as exc:
        raise ParseError(
            _family_parse_error_msg(expectation_type, result_format.value, schema_cls.__name__, exc)
        ) from exc
