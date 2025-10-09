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
from tests.integration.test_utils.data_source_config import PostgreSQLDatasourceTestConfig

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


@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_include_unexpected_rows_pandas(batch_for_datasource: Batch) -> None:
    """Test that include_unexpected_rows works correctly for ExpectCompoundColumnsToBeUnique."""
    expectation = gxe.ExpectCompoundColumnsToBeUnique(column_list=[INT_COL, DUPLICATES])
    result = batch_for_datasource.validate(
        expectation, result_format={"result_format": "BASIC", "include_unexpected_rows": True}
    )

    assert not result.success
    result_dict = result["result"]

    # Verify that unexpected_rows is present and contains the expected data
    assert "unexpected_rows" in result_dict
    assert result_dict["unexpected_rows"] is not None

    # Convert to DataFrame for easier comparison
    unexpected_rows_data = result_dict["unexpected_rows"]
    assert isinstance(unexpected_rows_data, pd.DataFrame)
    unexpected_rows_df = unexpected_rows_data

    # Should contain duplicate compound values
    # (rows where the combination of INT_COL and DUPLICATES is duplicated)
    assert len(unexpected_rows_df) > 0

    # Verify that the unexpected rows contain the duplicated compound values
    # DUPLICATES column has [100, 100, 100, 100, 99, 99] and INT_COL has [1, 2, 1, 3, None, None]
    # So we should see duplicates for combinations that repeat
    assert len(unexpected_rows_df) >= 4  # At least the rows with duplicated combinations


@parameterize_batch_for_data_sources(
    data_source_configs=[PostgreSQLDatasourceTestConfig()], data=DATA
)
def test_include_unexpected_rows_sql(batch_for_datasource: Batch) -> None:
    """Test include_unexpected_rows for ExpectCompoundColumnsToBeUnique with SQL data sources."""
    expectation = gxe.ExpectCompoundColumnsToBeUnique(column_list=[INT_COL, DUPLICATES])
    result = batch_for_datasource.validate(
        expectation, result_format={"result_format": "BASIC", "include_unexpected_rows": True}
    )

    assert not result.success
    result_dict = result["result"]

    # Verify that unexpected_rows is present and contains the expected data
    assert "unexpected_rows" in result_dict
    assert result_dict["unexpected_rows"] is not None

    unexpected_rows_data = result_dict["unexpected_rows"]
    assert isinstance(unexpected_rows_data, list)

    # Should contain duplicate compound values
    assert len(unexpected_rows_data) > 0

    # Verify that the unexpected rows contain the duplicated compound values
    # there are 4 unexpected rows, but our implementation only returns each duplicate once
    assert len(unexpected_rows_data) >= 2

    unexpected_rows_str = str(unexpected_rows_data)
    # Should contain the duplicate values from the DUPLICATES column (100 and 99)
    assert "100" in unexpected_rows_str


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
