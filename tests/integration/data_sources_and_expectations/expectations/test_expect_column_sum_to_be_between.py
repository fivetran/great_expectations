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

COL_NAME = "my_col"

DATA = pd.DataFrame({COL_NAME: [0, -1, 1, 2, 100, 9000, -1, -40, -60, None, None]}, dtype="object")


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=DATA)
def test_its_over_9000(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnSumToBeBetween(column=COL_NAME, min_value=9001, max_value=9001)
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success
    assert result.to_json_dict()["result"] == {"observed_value": 9001}


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnSumToBeBetween(column=COL_NAME),
            id="vacuous_truth",
        ),
        pytest.param(
            gxe.ExpectColumnSumToBeBetween(column=COL_NAME, min_value=9000),
            id="no_max",
        ),
        pytest.param(
            gxe.ExpectColumnSumToBeBetween(column=COL_NAME, max_value=9002),
            id="no_min",
        ),
        pytest.param(
            gxe.ExpectColumnSumToBeBetween(
                column=COL_NAME, min_value=9000, max_value=9002, strict_min=True, strict_max=True
            ),
            id="stict_bounds",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(batch_for_datasource: Batch, expectation: gxe.ExpectColumnSumToBeBetween) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnSumToBeBetween(column=COL_NAME, min_value=9002, max_value=9002),
            id="bad_range",
        ),
        pytest.param(
            gxe.ExpectColumnSumToBeBetween(column=COL_NAME, min_value=9001, strict_min=True),
            id="strict_min",
        ),
        pytest.param(
            gxe.ExpectColumnSumToBeBetween(column=COL_NAME, max_value=9001, strict_max=True),
            id="strict_max",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(batch_for_datasource: Batch, expectation: gxe.ExpectColumnSumToBeBetween) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success
