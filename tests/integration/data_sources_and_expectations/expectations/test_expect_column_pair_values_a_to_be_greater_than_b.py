from datetime import datetime
from unittest.mock import ANY

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.expectations.row_conditions import Column
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.data_source_lists import (
    JUST_PANDAS_DATA_SOURCES,
    NON_SQL_DATA_SOURCES,
)
from tests.integration.test_utils.data_source_config import (
    PANDAS_DATA_SOURCES,
    SQL_DATA_SOURCES,
)

NUMBERS_A = "numbers_a"
NUMBERS_A_EQUAL = "numbers_a_equal"
NUMBERS_B = "numbers_b"
DATES_A = "dates_a"
DATES_B = "dates_b"
STRINGS_A = "strings_a"
STRINGS_B = "strings_b"
NULLS_A = "nulls_a"
NULLS_B = "nulls_b"
NULLS_C = "nulls_c"

DATA = pd.DataFrame(
    {
        NUMBERS_A: [5, 8, 11, 13, 14],
        NUMBERS_A_EQUAL: [5, 8, 11, 13, 14],
        NUMBERS_B: [1, 5, 9, 12, 12],
        DATES_A: [
            datetime(2024, 1, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 2, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 3, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 4, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 5, 1).date(),  # noqa: DTZ001 # FIXME CoP
        ],
        DATES_B: [
            datetime(2023, 12, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 1, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 2, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 3, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 4, 1).date(),  # noqa: DTZ001 # FIXME CoP
        ],
        STRINGS_A: ["b", "m", "y", "z", "zz"],
        STRINGS_B: ["a", "k", "x", "y", "za"],
        NULLS_A: [None, None, None, None, 1],
        NULLS_B: [1, 2, None, 4, 5],
        NULLS_C: [2, 3, None, 5, 6],
    },
    dtype="object",
)


@parameterize_batch_for_data_sources(data_source_configs=NON_SQL_DATA_SOURCES, data=DATA)
def test_success_complete_non_sql(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnPairValuesAToBeGreaterThanB(
        column_A=NUMBERS_A,
        column_B=NUMBERS_B,
        or_equal=False,
        ignore_row_if="either_value_is_missing",
    )
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success


@parameterize_batch_for_data_sources(data_source_configs=SQL_DATA_SOURCES, data=DATA)
def test_success_complete_sql(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnPairValuesAToBeGreaterThanB(
        column_A=NUMBERS_A,
        column_B=NUMBERS_B,
        or_equal=False,
    )
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success
    assert result.to_json_dict()["result"] == {
        "element_count": 5,
        "unexpected_count": 0,
        "unexpected_percent": 0.0,
        "partial_unexpected_list": [],
        "missing_count": 0,
        "missing_percent": 0,
        "unexpected_percent_total": 0.0,
        "unexpected_percent_nonmissing": 0.0,
        "partial_unexpected_counts": [],
        "unexpected_list": [],
        "unexpected_index_query": ANY,
    }


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A=NUMBERS_A,
                column_B=NUMBERS_B,
            ),
            id="basic_number_comparison",
        ),
        pytest.param(
            gxe.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A=NUMBERS_A,
                column_B=NUMBERS_A_EQUAL,
                or_equal=True,
            ),
            id="number_comparison_with_equality",
        ),
        pytest.param(
            gxe.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A=DATES_A,
                column_B=DATES_B,
            ),
            id="date_comparison",
        ),
        pytest.param(
            gxe.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A=STRINGS_A,
                column_B=STRINGS_B,
            ),
            id="string_comparison",
        ),
        pytest.param(
            gxe.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A=STRINGS_A,
                column_B=STRINGS_B,
            ),
            id="string_comparison_with_equality",
        ),
        pytest.param(
            gxe.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A=NULLS_C,
                column_B=NULLS_B,
                ignore_row_if="both_values_are_missing",
            ),
            id="ignore_nulls_both",
        ),
        pytest.param(
            gxe.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A=NUMBERS_A,
                column_B=NUMBERS_B,
            ),
            id="mostly_success",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnPairValuesAToBeGreaterThanB,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A=NUMBERS_A,
                column_B=NUMBERS_A_EQUAL,
                or_equal=False,
            ),
            id="numbers_are_equal",
        ),
        pytest.param(
            gxe.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A=NUMBERS_B,
                column_B=NUMBERS_A,
            ),
            id="reversed_columns",
        ),
        pytest.param(
            gxe.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A=NULLS_A,
                column_B=NULLS_B,
                ignore_row_if="neither",
            ),
            id="null_comparison_not_ignored",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnPairValuesAToBeGreaterThanB,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success


@pytest.mark.parametrize(
    "suite_param_value,expected_result",
    [
        pytest.param(True, True, id="success"),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success_with_suite_param_or_equal_(
    batch_for_datasource: Batch, suite_param_value: bool, expected_result: bool
) -> None:
    suite_param_key = "test_expect_column_pair_values_a_to_be_greater_than_b"
    expectation = gxe.ExpectColumnPairValuesAToBeGreaterThanB(
        column_A=NUMBERS_A,
        column_B=NUMBERS_B,
        or_equal={"$PARAMETER": suite_param_key},
        result_format=ResultFormat.SUMMARY,
    )
    result = batch_for_datasource.validate(
        expectation, expectation_parameters={suite_param_key: suite_param_value}
    )
    assert result.success == expected_result


@pytest.mark.parametrize(
    "suite_param_value,expected_result",
    [
        pytest.param("both_values_are_missing", True, id="success"),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success_with_suite_param_ignore_row_if_(
    batch_for_datasource: Batch, suite_param_value: str, expected_result: bool
) -> None:
    suite_param_key = "test_expect_column_pair_values_a_to_be_greater_than_b"
    expectation = gxe.ExpectColumnPairValuesAToBeGreaterThanB(
        column_A=NUMBERS_A,
        column_B=NUMBERS_B,
        ignore_row_if={"$PARAMETER": suite_param_key},
        result_format=ResultFormat.SUMMARY,
    )
    result = batch_for_datasource.validate(
        expectation, expectation_parameters={suite_param_key: suite_param_value}
    )
    assert result.success == expected_result


PARTIAL_NULL_DATA = pd.DataFrame({"a": [9.0, None], "b": [1.0, 5.0]})


@pytest.mark.parametrize("or_equal", [False, True])
@parameterize_batch_for_data_sources(
    data_source_configs=[*PANDAS_DATA_SOURCES, *SQL_DATA_SOURCES], data=PARTIAL_NULL_DATA
)
def test_row_with_one_null_is_unexpected(batch_for_datasource: Batch, or_equal: bool) -> None:
    # A comparison with one NULL operand is NULL on SQL; the row must still count as unexpected,
    # as it does on pandas, rather than as neither expected nor unexpected.
    expectation = gxe.ExpectColumnPairValuesAToBeGreaterThanB(
        column_A="a", column_B="b", or_equal=or_equal
    )
    result = batch_for_datasource.validate(expectation)
    assert not result.success
    assert result.result["unexpected_count"] == 1


BOTH_NULL_DATA = pd.DataFrame({"a": [9.0, None], "b": [1.0, None]})


@pytest.mark.parametrize("or_equal,unexpected_count", [(False, 1), (True, 0)])
@parameterize_batch_for_data_sources(data_source_configs=SQL_DATA_SOURCES, data=BOTH_NULL_DATA)
def test_row_with_both_nulls_sql(
    batch_for_datasource: Batch, or_equal: bool, unexpected_count: int
) -> None:
    # With or_equal, SQL treats a row where both values are NULL as equal, and so expected.
    # ignore_row_if="neither" keeps the row, which the default would drop before the comparison.
    expectation = gxe.ExpectColumnPairValuesAToBeGreaterThanB(
        column_A="a", column_B="b", or_equal=or_equal, ignore_row_if="neither"
    )
    result = batch_for_datasource.validate(expectation)
    assert result.result["unexpected_count"] == unexpected_count


FILTER_COL = "filter_col"
# A row condition of `filter_col > 0` drops the first row, the only one in which A is not greater
# than B.
ROW_CONDITION_DATA = pd.DataFrame(
    {NUMBERS_A: [1, 8, 11], NUMBERS_B: [5, 5, 9], FILTER_COL: [0, 1, 1]}
)


@parameterize_batch_for_data_sources(data_source_configs=SQL_DATA_SOURCES, data=ROW_CONDITION_DATA)
def test_sql_row_condition_with_no_rows_ignored(batch_for_datasource: Batch) -> None:
    """Ignoring no rows leaves the SQL domain a bare SELECT, which must be wrapped to be used as a
    FROM. The count of rows in that domain is shared by all column pair Expectations.

    `missing_count` is the table's row count less the count of rows in the filtered domain, so it is
    zero only if both counts honor the row condition.
    """
    expectation = gxe.ExpectColumnPairValuesAToBeGreaterThanB(
        column_A=NUMBERS_A,
        column_B=NUMBERS_B,
        ignore_row_if="neither",
        row_condition=Column(FILTER_COL) > 0,
    )
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success, result.exception_info
    assert result.result["element_count"] == 2
    assert result.result["missing_count"] == 0
    assert result.result["unexpected_count"] == 0
