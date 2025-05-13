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

COL_NAME = "my_strings"

DATA = pd.DataFrame({COL_NAME: ["AA", "AAA", None]}, dtype="object")


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=DATA)
def test_success_complete(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValueLengthsToBeBetween(column=COL_NAME, min_value=2, max_value=3)
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValueLengthsToBeBetween(column=COL_NAME, min_value=2),
            id="no_max",
        ),
        pytest.param(
            gxe.ExpectColumnValueLengthsToBeBetween(column=COL_NAME, max_value=3),
            id="no_min",
        ),
        pytest.param(
            gxe.ExpectColumnValueLengthsToBeBetween(
                column=COL_NAME, min_value=1, max_value=4, strict_min=True, strict_max=True
            ),
            id="strict_bounds",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(
    batch_for_datasource: Batch, expectation: gxe.ExpectColumnValueLengthsToBeBetween
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValueLengthsToBeBetween(column=COL_NAME, min_value=0, max_value=1),
            id="range_too_low",
        ),
        pytest.param(
            gxe.ExpectColumnValueLengthsToBeBetween(column=COL_NAME, min_value=6, max_value=8),
            id="range_too_high",
        ),
        pytest.param(
            gxe.ExpectColumnValueLengthsToBeBetween(column=COL_NAME, min_value=2, strict_min=True),
            id="strict_min",
        ),
        pytest.param(
            gxe.ExpectColumnValueLengthsToBeBetween(column=COL_NAME, max_value=3, strict_max=True),
            id="strict_max",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(
    batch_for_datasource: Batch, expectation: gxe.ExpectColumnValueLengthsToBeBetween
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success
