import pandas as pd

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

DATA = pd.DataFrame(
    {
        COL_A: ["a", "b", "c"],
        COL_B: ["a", "b", "c"],
        COL_C: ["a", "b", "c"],
    }
)


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=DATA)
def test_golden_path(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectMulticolumnValuesToBeEqual(column_list=[COL_A, COL_B, COL_C])

    result = batch_for_datasource.validate(expectation)

    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES,
    data=pd.DataFrame(
        {
            COL_A: ["a", "b", "c"],
            COL_B: ["a", "different", "c"],
            COL_C: ["a", "b", "c"],
        }
    ),
)
def test_mostly_allows_a_partial_match(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectMulticolumnValuesToBeEqual(
        column_list=[COL_A, COL_B, COL_C], mostly=0.6
    )

    result = batch_for_datasource.validate(expectation)

    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES,
    data=pd.DataFrame(
        {
            COL_A: ["a", "b", "c"],
            COL_B: ["a", "different", "c"],
            COL_C: ["a", "b", "c"],
        }
    ),
)
def test_fails_when_a_row_contains_different_values(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectMulticolumnValuesToBeEqual(column_list=[COL_A, COL_B, COL_C])

    result = batch_for_datasource.validate(expectation)

    assert not result.success
    assert result.result["unexpected_count"] == 1


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=pd.DataFrame(
        {
            COL_A: [None, None, "same"],
            COL_B: [None, "value", "same"],
            COL_C: [None, None, "same"],
        }
    ),
)
def test_nulls_are_compared_as_values(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectMulticolumnValuesToBeEqual(
        column_list=[COL_A, COL_B, COL_C], ignore_row_if="never"
    )

    result = batch_for_datasource.validate(expectation)

    assert not result.success
    assert result.result["unexpected_count"] == 1
