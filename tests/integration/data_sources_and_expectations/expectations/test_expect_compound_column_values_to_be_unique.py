import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.compatibility import pydantic
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    ALL_DATA_SOURCES,
    JUST_PANDAS_DATA_SOURCES,
)

STRING_COL = "string_col"
INT_COL = "int_col"
INT_COL_2 = "int_col_2"
DUPLICATES = "duplicates"

try:
    from great_expectations.compatibility.pyspark import types as PYSPARK_TYPES

    SPARK_COLUMN_TYPES = {
        STRING_COL: PYSPARK_TYPES.StringType,
        INT_COL: PYSPARK_TYPES.IntegerType,
        INT_COL_2: PYSPARK_TYPES.IntegerType,
        DUPLICATES: PYSPARK_TYPES.IntegerType,
    }
except ModuleNotFoundError:
    SPARK_COLUMN_TYPES = {}


DATA = pd.DataFrame(
    {
        STRING_COL: ["foo", "bar", "foo", "baz", None, None],
        INT_COL: [1, 2, 1, 3, None, None],
        INT_COL_2: [1, 2, 3, 4, None, None],
        DUPLICATES: [100, 100, 100, 100, 99, 99],
    }
)


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=DATA)
def test_golden_path(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectCompoundColumnsToBeUnique(
        column_list=[STRING_COL, INT_COL, INT_COL_2],
        ignore_row_if="any_value_is_missing",
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectCompoundColumnsToBeUnique(column_list=[INT_COL, INT_COL_2]),
            id="two_cols",
        ),
        pytest.param(
            gxe.ExpectCompoundColumnsToBeUnique(column_list=[STRING_COL, INT_COL, INT_COL_2]),
            id="three_cols",
        ),
        pytest.param(
            gxe.ExpectCompoundColumnsToBeUnique(column_list=[INT_COL, DUPLICATES], mostly=0.3),
            id="mostly",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(
    batch_for_datasource: Batch, expectation: gxe.ExpectCompoundColumnsToBeUnique
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectCompoundColumnsToBeUnique(column_list=[INT_COL, DUPLICATES]),
        ),
        pytest.param(
            gxe.ExpectCompoundColumnsToBeUnique(column_list=[INT_COL, DUPLICATES], mostly=0.4),
            id="mostly_threshold_not_met",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(
    batch_for_datasource: Batch, expectation: gxe.ExpectCompoundColumnsToBeUnique
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success


@pytest.mark.unit
@pytest.mark.parametrize(
    "column_list",
    [
        pytest.param([], id="no_cols"),
        pytest.param([INT_COL_2], id="one_col"),
    ],
)
def test_invalid_config(column_list: list[str]) -> None:
    with pytest.raises(pydantic.ValidationError):
        gxe.ExpectCompoundColumnsToBeUnique(column_list=column_list)
