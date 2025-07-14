import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    ALL_DATA_SOURCES,
    JUST_PANDAS_DATA_SOURCES,
)

INT_COL_A = "INT_COL_A"
INT_COL_B = "INT_COL_B"
INT_COL_C = "INT_COL_C"
STRING_COL_A = "STRING_COL_A"
STRING_COL_B = "STRING_COL_B"


DATA = pd.DataFrame(
    {
        INT_COL_A: [1, 1, 2, 3],
        INT_COL_B: [2, 2, 3, 4],
        INT_COL_C: [3, 3, 4, 4],
        STRING_COL_A: ["a", "b", "c", "d"],
        STRING_COL_B: ["x", "y", "z", "a"],
    }
)


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=DATA)
def test_golden_path(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectSelectColumnValuesToBeUniqueWithinRecord(
        column_list=[INT_COL_A, INT_COL_B]
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectSelectColumnValuesToBeUniqueWithinRecord(
                column_list=[INT_COL_A, INT_COL_B, INT_COL_C], mostly=0.75
            ),
            id="mostly",
        ),
        pytest.param(
            gxe.ExpectSelectColumnValuesToBeUniqueWithinRecord(
                column_list=[STRING_COL_A, STRING_COL_B]
            ),
            id="strings_dont_error",
        ),
        pytest.param(
            gxe.ExpectSelectColumnValuesToBeUniqueWithinRecord(
                column_list=[STRING_COL_A, INT_COL_A]
            ),
            id="strings_and_ints",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(
    batch_for_datasource: Batch, expectation: gxe.ExpectSelectColumnValuesToBeUniqueWithinRecord
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectSelectColumnValuesToBeUniqueWithinRecord(column_list=[INT_COL_B, INT_COL_C]),
            id="one_non_unique",
        ),
        pytest.param(
            gxe.ExpectSelectColumnValuesToBeUniqueWithinRecord(
                column_list=[INT_COL_A, INT_COL_B, INT_COL_C], mostly=0.8
            ),
            id="mostly_threshold_not_met",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(
    batch_for_datasource: Batch, expectation: gxe.ExpectSelectColumnValuesToBeUniqueWithinRecord
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success


@pytest.mark.parametrize(
    "suite_param_value,expected_result",
    [
        pytest.param("all_values_are_missing", True, id="success"),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success_with_suite_param_ignore_row_if_(
    batch_for_datasource: Batch, suite_param_value: str, expected_result: bool
) -> None:
    suite_param_key = "test_expect_select_column_values_to_be_unique_within_record"
    expectation = gxe.ExpectSelectColumnValuesToBeUniqueWithinRecord(
        column_list=[INT_COL_A, INT_COL_B, INT_COL_C],
        mostly=0.75,
        ignore_row_if={"$PARAMETER": suite_param_key},
        result_format=ResultFormat.SUMMARY,
    )
    result = batch_for_datasource.validate(
        expectation, expectation_parameters={suite_param_key: suite_param_value}
    )
    assert result.success == expected_result
