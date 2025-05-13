import pandas as pd
import pytest

import great_expectations.expectations as gxe
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
