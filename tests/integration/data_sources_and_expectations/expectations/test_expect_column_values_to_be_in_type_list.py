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
from tests.integration.test_utils.data_source_config import (
    DatabricksDatasourceTestConfig,
    PandasDataFrameDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
)

INTEGER_COLUMN = "integers"
INTEGER_AND_NULL_COLUMN = "integers_and_nulls"
STRING_COLUMN = "strings"
NULL_COLUMN = "nulls"


DATA = pd.DataFrame(
    {
        INTEGER_COLUMN: [1, 2, 3, 4, 5],
        INTEGER_AND_NULL_COLUMN: [1, 2, 3, 4, None],
        STRING_COLUMN: ["a", "b", "c", "d", "e"],
        NULL_COLUMN: pd.Series([None, None, None, None, None]),
    },
    dtype="object",
)

PASSING_DATA_SOURCES_EXCEPT_DATA_FRAMES = [
    ds
    for ds in ALL_DATA_SOURCES
    if not isinstance(
        ds,
        (
            PandasDataFrameDatasourceTestConfig,
            SnowflakeDatasourceTestConfig,
            DatabricksDatasourceTestConfig,
        ),
    )
]


@parameterize_batch_for_data_sources(
    data_source_configs=PASSING_DATA_SOURCES_EXCEPT_DATA_FRAMES, data=DATA
)
def test_success_complete(batch_for_datasource: Batch) -> None:
    type_list = ["INTEGER", "Integer", "int", "int64", "int32", "IntegerType", "_CUSTOM_DECIMAL"]
    expectation = gxe.ExpectColumnValuesToBeInTypeList(column=INTEGER_COLUMN, type_list=type_list)
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    result_dict = result.to_json_dict()["result"]

    assert result.success
    assert isinstance(result_dict, dict)
    assert result_dict["observed_value"] in type_list


@pytest.mark.xfail
@parameterize_batch_for_data_sources(
    data_source_configs=[SnowflakeDatasourceTestConfig(), DatabricksDatasourceTestConfig()],
    data=DATA,
)
def test_success_complete_errors(batch_for_datasource: Batch) -> None:
    # TODO: get this fixed
    type_list = ["INTEGER", "Integer", "int", "int64", "int32", "IntegerType", "_CUSTOM_DECIMAL"]
    expectation = gxe.ExpectColumnValuesToBeInTypeList(column=INTEGER_COLUMN, type_list=type_list)
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    result_dict = result.to_json_dict()["result"]

    assert result.success
    assert isinstance(result_dict, dict)
    assert result_dict["observed_value"] in type_list


@parameterize_batch_for_data_sources(
    data_source_configs=[PandasDataFrameDatasourceTestConfig()], data=DATA
)
def test_success_complete_pandas(batch_for_datasource: Batch) -> None:
    type_list = ["INTEGER", "int", "int64", "int32", "IntegerType"]
    expectation = gxe.ExpectColumnValuesToBeInTypeList(column=INTEGER_COLUMN, type_list=type_list)
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)

    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(column=INTEGER_COLUMN, type_list=["int"]),
            id="integer_types",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(
                column=INTEGER_AND_NULL_COLUMN, type_list=["int", "float64"], mostly=0.8
            ),
            id="mostly",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(column=STRING_COLUMN, type_list=["str"]),
            id="string_types",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(column=NULL_COLUMN, type_list=["float"]),
            id="null_float_types",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnValuesToBeInTypeList,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(column=INTEGER_COLUMN, type_list=["str"]),
            id="wrong_type",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnValuesToBeInTypeList,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success
