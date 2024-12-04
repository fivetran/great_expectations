import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    ALL_DATA_SOURCES,
    JUST_PANDAS_DATA_SOURCES,
)

COL_A = "col_a"
COL_B = "col_b"


DATA = pd.DataFrame({COL_A: [1, 2, None], COL_B: ["a", "b", None]})
EMPTY_DATA = pd.DataFrame({COL_A: [], COL_B: []})


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=DATA)
def test_golden_path(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectTableRowCountToBeBetween(min_value=2, max_value=4)
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectTableRowCountToBeBetween(min_value=None, max_value=None),
            id="vacuously_true",
        ),
        pytest.param(
            gxe.ExpectTableRowCountToBeBetween(min_value=2, max_value=None),
            id="just_min",
        ),
        pytest.param(
            gxe.ExpectTableRowCountToBeBetween(min_value=None, max_value=4),
            id="just_max",
        ),
        pytest.param(
            gxe.ExpectTableRowCountToBeBetween(min_value=3, max_value=5),
            id="inclusivity",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(
    batch_for_datasource: Batch, expectation: gxe.ExpectTableRowCountToBeBetween
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=EMPTY_DATA)
def test_empty_data(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectTableRowCountToBeBetween(min_value=0, max_value=0)
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectTableRowCountToBeBetween(min_value=8, max_value=None),
            id="just_min",
        ),
        pytest.param(
            gxe.ExpectTableRowCountToBeBetween(min_value=None, max_value=1),
            id="just_max",
        ),
        pytest.param(
            gxe.ExpectTableRowCountToBeBetween(min_value=4, max_value=4),
            id="bad_range",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(
    batch_for_datasource: Batch, expectation: gxe.ExpectTableRowCountToBeBetween
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success


@pytest.mark.xfail(reason="Fails at validation, but should fail when instantiating")
@pytest.mark.unit
def test_valid_range() -> None:
    with pytest.raises(ValueError):
        gxe.ExpectTableRowCountToBeBetween(min_value=5, max_value=4)
