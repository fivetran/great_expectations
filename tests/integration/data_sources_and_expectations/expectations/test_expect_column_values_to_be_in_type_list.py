import pandas as pd
import pytest
import sqlalchemy.types as sqltypes

import great_expectations.expectations as gxe
from great_expectations.compatibility.snowflake import SNOWFLAKE_TYPES
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
    type_list = [
        "INTEGER",
        "Integer",
        "int",
        "int64",
        "int32",
        "IntegerType",
        "_CUSTOM_DECIMAL",
    ]
    expectation = gxe.ExpectColumnValuesToBeInTypeList(column=INTEGER_COLUMN, type_list=type_list)
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    result_dict = result.to_json_dict()["result"]

    assert result.success
    assert isinstance(result_dict, dict)
    assert result_dict["observed_value"] in type_list


@pytest.mark.xfail
@parameterize_batch_for_data_sources(
    data_source_configs=[DatabricksDatasourceTestConfig()],
    data=DATA,
)
def test_success_complete_errors(batch_for_datasource: Batch) -> None:
    # TODO: get this fixed
    type_list = [
        "INTEGER",
        "Integer",
        "int",
        "int64",
        "int32",
        "IntegerType",
        "_CUSTOM_DECIMAL",
    ]
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


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(
                column="CHARACTER", type_list=["CHARACTER", "VARCHAR(1)"]
            ),
            id="CHARACTER",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(
                column="DEC", type_list=["DEC", "DECIMAL", "DECIMAL(38, 0)"]
            ),
            id="DEC",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(
                column="FIXED", type_list=["FIXED", "DECIMAL", "DECIMAL(38, 0)"]
            ),
            id="FIXED",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(column="GEOGRAPHY", type_list=["GEOGRAPHY"]),
            id="GEOGRAPHY",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(column="GEOMETRY", type_list=["GEOMETRY"]),
            id="GEOMETRY",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(
                column="NUMBER",
                type_list=[
                    "NUMBER",
                    "DECIMAL",
                    "NUMERIC",
                    "DECIMAL(38, 0)",  # 38, 0 is the default precision and scale
                ],
            ),
            id="NUMBER",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(
                column="STRING", type_list=["STRING", "VARCHAR", "VARCHAR(16777216)"]
            ),
            id="STRING",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(
                column="TEXT", type_list=["TEXT", "VARCHAR", "VARCHAR(16777216)"]
            ),
            id="TEXT",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(
                column="TIMESTAMP_LTZ", type_list=["TIMESTAMP_LTZ"]
            ),
            id="TIMESTAMP_LTZ",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(
                column="TIMESTAMP_NTZ", type_list=["TIMESTAMP_NTZ"]
            ),
            id="TIMESTAMP_NTZ",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(column="TIMESTAMP_TZ", type_list=["TIMESTAMP_TZ"]),
            id="TIMESTAMP_TZ",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(
                column="VARBINARY", type_list=["VARBINARY", "BINARY"]
            ),
            id="VARBINARY",
        ),
        # INT , INTEGER , BIGINT , SMALLINT , TINYINT , BYTEINT are Synonymous with NUMBER,
        # except that precision and scale cannot be specified (i.e. always defaults to NUMBER(38, 0)
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(column="BYTEINT", type_list=["DECIMAL(38, 0)"]),
            id="BYTEINT",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(column="TINYINT", type_list=["DECIMAL(38, 0)"]),
            id="TINYINT",
        ),
        # Complex data types which are not hashable by testing framework currently
        # pytest.param(
        #     gxe.ExpectColumnValuesToBeInTypeList(
        #         column="VARIANT", type_list=["VARIANT"]
        #     ),
        #     id="VARIANT",
        # ),
        # pytest.param(
        #     gxe.ExpectColumnValuesToBeInTypeList(column="OBJECT", type_list=["OBJECT"]),
        #     id="OBJECT",
        # ),
        # pytest.param(
        #     gxe.ExpectColumnValuesToBeInTypeList(column="ARRAY", type_list=["ARRAY"]),
        #     id="ARRAY",
        # ),
        # These sqlachemy types map to _CUSTOM_* types in snowflake-sqlalchemy
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(column="_CUSTOM_Date", type_list=["DATE"]),
            id="_CUSTOM_Date",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(
                column="_CUSTOM_DateTime", type_list=["TIMESTAMP_NTZ"]
            ),
            id="_CUSTOM_DateTime",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(column="_CUSTOM_Time", type_list=["TIME"]),
            id="_CUSTOM_Time",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(column="_CUSTOM_Float", type_list=["FLOAT"]),
            id="_CUSTOM_Float",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInTypeList(
                column="_CUSTOM_DECIMAL", type_list=["INTEGER", "DECIMAL(38, 0)"]
            ),
            id="_CUSTOM_DECIMAL",
        ),
    ],
)
@parameterize_batch_for_data_sources(
    data_source_configs=[
        SnowflakeDatasourceTestConfig(
            column_types={
                "ARRAY": SNOWFLAKE_TYPES.ARRAY,
                "BYTEINT": SNOWFLAKE_TYPES.BYTEINT,
                "CHARACTER": SNOWFLAKE_TYPES.CHARACTER,
                "DEC": SNOWFLAKE_TYPES.DEC,
                "FIXED": SNOWFLAKE_TYPES.FIXED,
                "GEOGRAPHY": SNOWFLAKE_TYPES.GEOGRAPHY,
                "GEOMETRY": SNOWFLAKE_TYPES.GEOMETRY,
                "NUMBER": SNOWFLAKE_TYPES.NUMBER,
                "OBJECT": SNOWFLAKE_TYPES.OBJECT,
                "STRING": SNOWFLAKE_TYPES.STRING,
                "TEXT": SNOWFLAKE_TYPES.TEXT,
                "TIMESTAMP_LTZ": SNOWFLAKE_TYPES.TIMESTAMP_LTZ,
                "TIMESTAMP_NTZ": SNOWFLAKE_TYPES.TIMESTAMP_NTZ,
                "TIMESTAMP_TZ": SNOWFLAKE_TYPES.TIMESTAMP_TZ,
                "TINYINT": SNOWFLAKE_TYPES.TINYINT,
                "VARBINARY": SNOWFLAKE_TYPES.VARBINARY,
                "VARIANT": SNOWFLAKE_TYPES.VARIANT,
                # These sqlachemy types map to _CUSTOM_* types in snowflake-sqlalchemy
                "_CUSTOM_Date": sqltypes.Date,
                "_CUSTOM_DateTime": sqltypes.DateTime,
                "_CUSTOM_Time": sqltypes.Time,
                "_CUSTOM_Float": sqltypes.Float,
                "_CUSTOM_DECIMAL": sqltypes.INTEGER,
            }
        )
    ],
    data=pd.DataFrame(
        {
            "BYTEINT": [1, 2, 3],
            "CHARACTER": ["a", "b", "c"],
            "DEC": [1.0, 2.0, 3.0],
            "FIXED": [1.0, 2.0, 3.0],
            "GEOGRAPHY": ["POINT(1 1)", "POINT(2 2)", "POINT(3 3)"],
            "GEOMETRY": ["POINT(1 1)", "POINT(2 2)", "POINT(3 3)"],
            "NUMBER": [1, 2, 3],
            "STRING": ["a", "b", "c"],
            "TEXT": ["a", "b", "c"],
            "TIMESTAMP_LTZ": [
                "2021-01-01 00:00:00",
                "2021-01-02 00:00:00",
                "2021-01-03 00:00:00",
            ],
            "TIMESTAMP_NTZ": [
                "2021-01-01 00:00:00",
                "2021-01-02 00:00:00",
                "2021-01-03 00:00:00",
            ],
            "TIMESTAMP_TZ": [
                "2021-01-01 00:00:00",
                "2021-01-02 00:00:00",
                "2021-01-03 00:00:00",
            ],
            "TINYINT": [1, 2, 3],
            "VARBINARY": [b"1", b"2", b"3"],
            # Complex data types which are not hashable by testing framework currently
            # "ARRAY": pd.Series([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype="object"),
            # "OBJECT": [{"a": 1}, {"b": 2}, {"c": 3}],
            # "VARIANT": [{"a": 1}, {"b": 2}, {"c": 3}],
            # These sqlachemy types map to _CUSTOM_* types in snowflake-sqlalchemy
            "_CUSTOM_Date": [
                # Date in isoformat
                "2021-01-01",
                "2021-01-02",
                "2021-01-03",
            ],
            "_CUSTOM_DateTime": [
                # isoformat with microseconds
                "2021-01-01 00:00:00.000000",
                "2021-01-02 00:00:00.000000",
                "2021-01-03 00:00:00.000000",
            ],
            "_CUSTOM_Time": [
                "00:00:00.878281",
                "01:00:00.000000",
                "00:10:43.000000",
            ],
            "_CUSTOM_Float": [1.0, 2.0, 3.0],
            "_CUSTOM_DECIMAL": [1, 2, 3],
        },
        dtype="object",
    ),
)
def test_success_complete_snowflake(
    batch_for_datasource: Batch, expectation: gxe.ExpectColumnValuesToBeInTypeList
) -> None:
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    result_dict = result.to_json_dict()["result"]

    assert result.success
    assert isinstance(result_dict, dict)
    assert isinstance(result_dict["observed_value"], str)
    assert isinstance(expectation.type_list, list)
    assert result_dict["observed_value"] in expectation.type_list
