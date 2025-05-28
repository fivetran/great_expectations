from datetime import datetime
from unittest.mock import ANY

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    JUST_PANDAS_DATA_SOURCES,
    NON_SQL_DATA_SOURCES,
    SQL_DATA_SOURCES,
)

EQUAL_STRINGS_A = "equal_strings_a"
EQUAL_STRINGS_B = "equal_strings_b"
UNEQUAL_STRINGS = "unequal_strings"
EQUAL_DATES_A = "equal_dates_a"
EQUAL_DATES_B = "equal_dates_b"
UNEQUAL_DATES = "unequal_dates"
ALL_EQUAL_NUMS_A = "all_equal_nums_a"
ALL_EQUAL_NUMS_B = "all_equal_nums_b"
SOME_EQUAL_NUMS = "some_equal_nums"
NULLS_A = "nulls_a"
NULLS_B = "nulls_b"
ALL_NULLS = "all_nulls"

DATA = pd.DataFrame(
    {
        EQUAL_STRINGS_A: ["foo", "bar", "baz"],
        EQUAL_STRINGS_B: ["foo", "bar", "baz"],
        UNEQUAL_STRINGS: ["foo", "bar", "wat"],
        EQUAL_DATES_A: [
            datetime(2024, 1, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 2, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 3, 1).date(),  # noqa: DTZ001 # FIXME CoP
        ],
        EQUAL_DATES_B: [
            datetime(2024, 1, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 2, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 3, 1).date(),  # noqa: DTZ001 # FIXME CoP
        ],
        UNEQUAL_DATES: [
            datetime(2024, 1, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 2, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 4, 1).date(),  # noqa: DTZ001 # FIXME CoP
        ],
        ALL_EQUAL_NUMS_A: [1, 2, 3],
        ALL_EQUAL_NUMS_B: [1, 2, 3],
        SOME_EQUAL_NUMS: [1, 2, 4],
        NULLS_A: [1, None, 3],
        NULLS_B: [None, 2, 3],
    },
    dtype="object",
)


@parameterize_batch_for_data_sources(data_source_configs=NON_SQL_DATA_SOURCES, data=DATA)
def test_success_complete_non_sql(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnPairValuesToBeEqual(
        column_A=EQUAL_STRINGS_A,
        column_B=EQUAL_STRINGS_B,
    )
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success


@parameterize_batch_for_data_sources(data_source_configs=SQL_DATA_SOURCES, data=DATA)
def test_success_complete_sql(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnPairValuesToBeEqual(
        column_A=EQUAL_STRINGS_A,
        column_B=EQUAL_STRINGS_B,
    )
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success
    assert result.to_json_dict()["result"] == {
        "element_count": 3,
        "unexpected_count": 0,
        "unexpected_percent": 0.0,
        "partial_unexpected_list": [],
        "missing_count": 0,
        "missing_percent": 0.0,
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
            gxe.ExpectColumnPairValuesToBeEqual(
                column_A=EQUAL_STRINGS_A,
                column_B=EQUAL_STRINGS_B,
            ),
            id="equal_strings",
        ),
        pytest.param(
            gxe.ExpectColumnPairValuesToBeEqual(
                column_A=EQUAL_DATES_A,
                column_B=EQUAL_DATES_B,
            ),
            id="equal_dates",
        ),
        pytest.param(
            gxe.ExpectColumnPairValuesToBeEqual(
                column_A=ALL_EQUAL_NUMS_A,
                column_B=ALL_EQUAL_NUMS_B,
            ),
            id="all_equal_numbers",
        ),
        pytest.param(
            gxe.ExpectColumnPairValuesToBeEqual(
                column_A=ALL_EQUAL_NUMS_A,
                column_B=SOME_EQUAL_NUMS,
                mostly=0.6,
            ),
            id="some_equal_numbers",
        ),
        pytest.param(
            gxe.ExpectColumnPairValuesToBeEqual(
                column_A=NULLS_A,
                column_B=NULLS_B,
                ignore_row_if="either_value_is_missing",
            ),
            id="ignore_nulls",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnPairValuesToBeEqual,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnPairValuesToBeEqual(
                column_A=EQUAL_STRINGS_A,
                column_B=UNEQUAL_STRINGS,
            ),
            id="unequal_strings",
        ),
        pytest.param(
            gxe.ExpectColumnPairValuesToBeEqual(
                column_A=EQUAL_DATES_A,
                column_B=UNEQUAL_DATES,
            ),
            id="unequal_dates",
        ),
        pytest.param(
            gxe.ExpectColumnPairValuesToBeEqual(
                column_A=ALL_EQUAL_NUMS_A,
                column_B=SOME_EQUAL_NUMS,
            ),
            id="partially_equal_numbers",
        ),
        pytest.param(
            gxe.ExpectColumnPairValuesToBeEqual(
                column_A=NULLS_A,
                column_B=NULLS_A,
                ignore_row_if="neither",
            ),
            id="matching_nulls",
        ),
        pytest.param(
            gxe.ExpectColumnPairValuesToBeEqual(
                column_A=NULLS_A,
                column_B=NULLS_B,
            ),
            id="neither",
        ),
        pytest.param(
            gxe.ExpectColumnPairValuesToBeEqual(
                column_A=ALL_EQUAL_NUMS_A,
                column_B=SOME_EQUAL_NUMS,
                mostly=0.7,
            ),
            id="some_equal_numbers",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnPairValuesToBeEqual,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success
