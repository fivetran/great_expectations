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

COL_A = "COL_A"
COL_B = "COL_B"
COL_C = "COL_C"
COL_A_BAD = "COL_A_BAD"
ONES_COL = "ONES_COL"


DATA = pd.DataFrame(
    {
        COL_A: [4, 2, 0],
        COL_B: [2, 7, 7],
        COL_C: [1, -2, 0],
        COL_A_BAD: [4, 4, 0],
        ONES_COL: [1, 1, 1],
    }
)


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=DATA)
def test_golden_path(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectMulticolumnSumToEqual(column_list=[COL_A, COL_B, COL_C], sum_total=7)
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectMulticolumnSumToEqual(
                column_list=[COL_A_BAD, COL_B, COL_C], sum_total=7, mostly=0.4
            ),
            id="mostly",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(batch_for_datasource: Batch, expectation: gxe.ExpectMulticolumnSumToEqual) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectMulticolumnSumToEqual(
                column_list=[COL_A_BAD, COL_B, COL_C], sum_total=7, mostly=0.7
            ),
            id="mostly_not_met",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(batch_for_datasource: Batch, expectation: gxe.ExpectMulticolumnSumToEqual) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success


@pytest.mark.parametrize(
    "suite_param_value,expected_result",
    [
        pytest.param(7, True, id="success"),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success_with_suite_param_sum_total_(
    batch_for_datasource: Batch, suite_param_value: int, expected_result: bool
) -> None:
    suite_param_key = "test_expect_multicolumn_sum_to_equal"
    expectation = gxe.ExpectMulticolumnSumToEqual(
        column_list=[COL_A_BAD, COL_B, COL_C],
        sum_total={"$PARAMETER": suite_param_key},
        mostly=0.4,
        result_format=ResultFormat.SUMMARY,
    )
    result = batch_for_datasource.validate(
        expectation, expectation_parameters={suite_param_key: suite_param_value}
    )
    assert result.success == expected_result


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
    suite_param_key = "test_expect_multicolumn_sum_to_equal"
    expectation = gxe.ExpectMulticolumnSumToEqual(
        column_list=[COL_A_BAD, COL_B, COL_C],
        sum_total=7,
        mostly=0.4,
        ignore_row_if={"$PARAMETER": suite_param_key},
        result_format=ResultFormat.SUMMARY,
    )
    result = batch_for_datasource.validate(
        expectation, expectation_parameters={suite_param_key: suite_param_value}
    )
    assert result.success == expected_result
