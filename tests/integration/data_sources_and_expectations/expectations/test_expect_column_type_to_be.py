import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.data_source_lists import (
    JUST_PANDAS_DATA_SOURCES,
)
from tests.integration.test_utils.data_source_config import (
    BigQueryDatasourceTestConfig,
    DatabricksDatasourceTestConfig,
    GenericSQLDatasourceTestConfig,
    MySQLDatasourceTestConfig,
    PandasDataFrameDatasourceTestConfig,
    PandasFilesystemCsvDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    RedshiftDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
    SqliteDatasourceTestConfig,
    SQLServerDatasourceTestConfig,
)

INTEGER_COLUMN = "integers"
STRING_COLUMN = "strings"
FLOAT_COLUMN = "floats"

DATA = pd.DataFrame(
    {
        INTEGER_COLUMN: [1, 2, 3, 4, 5],
        STRING_COLUMN: ["a", "b", "c", "d", "e"],
        FLOAT_COLUMN: [1.5, 2.5, 3.5, 4.5, 5.5],
    },
    dtype="object",
)

TYPED_DATA = pd.DataFrame(
    {
        INTEGER_COLUMN: pd.Series([1, 2, 3, 4, 5], dtype="int64"),
        STRING_COLUMN: pd.Series(["a", "b", "c", "d", "e"], dtype="str"),
    }
)


try:
    from great_expectations.compatibility.pyspark import types as PYSPARK_TYPES

    SPARK_COLUMN_TYPES = {
        INTEGER_COLUMN: PYSPARK_TYPES.IntegerType,
        STRING_COLUMN: PYSPARK_TYPES.StringType,
        FLOAT_COLUMN: PYSPARK_TYPES.DoubleType,
    }
except ModuleNotFoundError:
    SPARK_COLUMN_TYPES = {}


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES,
    data=TYPED_DATA,
)
def test_success_pandas(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnTypeToBe(column=INTEGER_COLUMN, type_="int64")
    result = batch_for_datasource.validate(expectation)
    assert result.success
    assert set(result.result) == {"observed_value"}


@parameterize_batch_for_data_sources(
    data_source_configs=[
        PandasDataFrameDatasourceTestConfig(),
        PandasFilesystemCsvDatasourceTestConfig(),
    ],
    data=TYPED_DATA,
)
def test_success_for_type__int(batch_for_datasource: Batch) -> None:
    """Native python type name resolves via numpy dtype on pandas."""
    expectation = gxe.ExpectColumnTypeToBe(column=INTEGER_COLUMN, type_="int")
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES,
    data=DATA,
)
def test_success_object_dtype(batch_for_datasource: Batch) -> None:
    """Schema-level check: object dtype matches only an object type request."""
    expectation = gxe.ExpectColumnTypeToBe(column=INTEGER_COLUMN, type_="object")
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES,
    data=DATA,
)
def test_str_does_not_match_object_dtype(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnTypeToBe(column=STRING_COLUMN, type_="str")
    result = batch_for_datasource.validate(expectation)
    assert not result.success
    assert result.result["observed_value"] == "object_"


@parameterize_batch_for_data_sources(
    data_source_configs=[
        BigQueryDatasourceTestConfig(),
        SQLServerDatasourceTestConfig(),
        MySQLDatasourceTestConfig(),
        PostgreSQLDatasourceTestConfig(),
        RedshiftDatasourceTestConfig(),
        GenericSQLDatasourceTestConfig(),
        SqliteDatasourceTestConfig(),
    ],
    data=DATA,
)
def test_success_for_type__INTEGER(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnTypeToBe(column=INTEGER_COLUMN, type_="INTEGER")
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=[
        SqliteDatasourceTestConfig(),
    ],
    data=DATA,
)
def test_success_sql_integer(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnTypeToBe(column=INTEGER_COLUMN, type_="INTEGER")
    result = batch_for_datasource.validate(expectation)
    assert result.success
    assert result.result["observed_value"] == "INTEGER"


@parameterize_batch_for_data_sources(
    data_source_configs=[DatabricksDatasourceTestConfig()],
    data=DATA,
)
def test_success_for_type__Integer(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnTypeToBe(column=INTEGER_COLUMN, type_="INT")
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=[
        SparkFilesystemCsvDatasourceTestConfig(
            column_types=SPARK_COLUMN_TYPES,
        )
    ],
    data=DATA,
)
def test_success_for_type__IntegerType(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnTypeToBe(column=INTEGER_COLUMN, type_="IntegerType")
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=[SnowflakeDatasourceTestConfig()],
    data=DATA,
)
def test_success_for_type__Number(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnTypeToBe(column=INTEGER_COLUMN, type_="DECIMAL(38, 0)")
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=[
        DatabricksDatasourceTestConfig(),
        PostgreSQLDatasourceTestConfig(),
        SnowflakeDatasourceTestConfig(),
        SQLServerDatasourceTestConfig(),
    ],
    data=DATA,
)
def test_case_insensitive_dialects(batch_for_datasource: Batch) -> None:
    dialect_name = batch_for_datasource.data.execution_engine.engine.dialect.name.lower()

    expected_dialects = ["snowflake", "databricks", "postgresql", "mssql"]
    assert dialect_name in expected_dialects, f"Unexpected dialect: {dialect_name}"

    if dialect_name == "snowflake":
        base_type = "DECIMAL(38, 0)"
    elif dialect_name == "databricks":
        base_type = "INT"
    elif dialect_name in {"postgresql", "mssql"}:
        base_type = "INTEGER"
    else:
        raise AssertionError(f"Unexpected dialect: {dialect_name}")

    for type_str in [base_type.lower(), base_type.upper(), base_type.capitalize()]:
        expectation = gxe.ExpectColumnTypeToBe(column=INTEGER_COLUMN, type_=type_str)
        result = batch_for_datasource.validate(expectation)
        assert result.success, f"Expected success for type '{type_str}' on dialect '{dialect_name}'"


@parameterize_batch_for_data_sources(
    data_source_configs=[PostgreSQLDatasourceTestConfig()],
    data=DATA,
)
def test_double_precision_matches_float_not_int(batch_for_datasource: Batch) -> None:
    """Multi-word DDL type is known vocabulary: match on float, plain mismatch on int."""
    float_result = batch_for_datasource.validate(
        gxe.ExpectColumnTypeToBe(column=FLOAT_COLUMN, type_="DOUBLE PRECISION")
    )
    assert float_result.success

    int_result = batch_for_datasource.validate(
        gxe.ExpectColumnTypeToBe(column=INTEGER_COLUMN, type_="DOUBLE PRECISION")
    )
    assert not int_result.success
    assert int_result.exception_info["raised_exception"] is False


@parameterize_batch_for_data_sources(
    data_source_configs=[
        SqliteDatasourceTestConfig(),
    ],
    data=DATA,
)
def test_known_type_mismatch_sqlite(batch_for_datasource: Batch) -> None:
    result = batch_for_datasource.validate(
        gxe.ExpectColumnTypeToBe(column=STRING_COLUMN, type_="INTEGER")
    )
    assert not result.success
    assert result.exception_info["raised_exception"] is False


@pytest.mark.parametrize(
    "suite_param_value,expected_result",
    [
        pytest.param("int64", True, id="success"),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=TYPED_DATA)
def test_success_with_suite_param_type_(
    batch_for_datasource: Batch, suite_param_value: str, expected_result: bool
) -> None:
    suite_param_key = "test_expect_column_type_to_be"
    expectation = gxe.ExpectColumnTypeToBe(
        column=INTEGER_COLUMN,
        type_={"$PARAMETER": suite_param_key},
        result_format=ResultFormat.SUMMARY,
    )
    result = batch_for_datasource.validate(
        expectation, expectation_parameters={suite_param_key: suite_param_value}
    )
    assert result.success == expected_result


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES,
    data=DATA,
)
def test_failure(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnTypeToBe(column=INTEGER_COLUMN, type_="NUMBER")
    result = batch_for_datasource.validate(expectation)
    assert not result.success


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES,
    data=TYPED_DATA,
)
def test_known_type_mismatch_returns_false(batch_for_datasource: Batch) -> None:
    """Known pandas type on a non-matching column is a plain failure, not an error."""
    result = batch_for_datasource.validate(
        gxe.ExpectColumnTypeToBe(column=INTEGER_COLUMN, type_="float64")
    )
    assert not result.success
    assert result.exception_info["raised_exception"] is False


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES,
    data=TYPED_DATA,
)
def test_unknown_type_raises_exception_info(batch_for_datasource: Batch) -> None:
    """Unknown type_ surfaces as exception_info, not a plain type mismatch."""
    expectation = gxe.ExpectColumnTypeToBe(column=INTEGER_COLUMN, type_="NUMBER")
    result = batch_for_datasource.validate(expectation)
    assert not result.success
    assert result.exception_info["raised_exception"] is True


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES,
    data=DATA,
)
def test_missing_column_failure(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnTypeToBe(column="non_existent_column", type_="INTEGER")
    result = batch_for_datasource.validate(expectation)
    assert not result.success
