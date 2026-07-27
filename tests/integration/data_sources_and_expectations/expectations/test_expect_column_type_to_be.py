import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
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

# Natural dtypes: pandas infers `integers` -> int64 and `strings` -> object.
# (Unlike the ExpectColumnValuesToBeOfType test we do NOT force dtype="object",
# because ExpectColumnTypeToBe validates the declared schema dtype, not each row.)
DATA = pd.DataFrame(
    {
        INTEGER_COLUMN: [1, 2, 3, 4, 5],
        STRING_COLUMN: ["a", "b", "c", "d", "e"],
    }
)

# Object-dtype data, used to prove the schema-level behavior for pandas.
OBJECT_DATA = pd.DataFrame(
    {INTEGER_COLUMN: [1, 2, 3, 4, 5]},
    dtype="object",
)

# Row-level result fields that must NEVER appear for this schema-level expectation.
ROW_LEVEL_RESULT_KEYS = {
    "element_count",
    "unexpected_count",
    "unexpected_percent",
    "partial_unexpected_list",
    "missing_count",
}


try:
    from great_expectations.compatibility.pyspark import types as PYSPARK_TYPES

    SPARK_COLUMN_TYPES = {
        INTEGER_COLUMN: PYSPARK_TYPES.IntegerType,
        STRING_COLUMN: PYSPARK_TYPES.StringType,
    }
except ModuleNotFoundError:
    SPARK_COLUMN_TYPES = {}


@parameterize_batch_for_data_sources(
    data_source_configs=[
        PandasDataFrameDatasourceTestConfig(),
        PandasFilesystemCsvDatasourceTestConfig(),
    ],
    data=DATA,
)
def test_success_for_type__int64(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnTypeToBe(column=INTEGER_COLUMN, type_="int64")
    result = batch_for_datasource.validate(expectation)
    assert result.success
    assert result.result == {"observed_value": "int64"}


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
    data_source_configs=[DatabricksDatasourceTestConfig()],
    data=DATA,
)
def test_success_for_type__INT(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnTypeToBe(column=INTEGER_COLUMN, type_="INT")
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=[SnowflakeDatasourceTestConfig()],
    data=DATA,
)
def test_success_for_type__DECIMAL(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnTypeToBe(column=INTEGER_COLUMN, type_="DECIMAL(38, 0)")
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
    assert result.result == {"observed_value": "IntegerType"}


@parameterize_batch_for_data_sources(
    data_source_configs=[
        PandasDataFrameDatasourceTestConfig(),
        SqliteDatasourceTestConfig(),
    ],
    data=DATA,
)
def test_failure(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnTypeToBe(column=STRING_COLUMN, type_="int")
    result = batch_for_datasource.validate(expectation)
    assert not result.success
    # Schema-level result shape is preserved even on failure.
    assert "observed_value" in result.result


@parameterize_batch_for_data_sources(
    data_source_configs=[PandasDataFrameDatasourceTestConfig()],
    data=OBJECT_DATA,
)
def test_pandas_object_column_is_schema_level(batch_for_datasource: Batch) -> None:
    """The core fix: unlike ExpectColumnValuesToBeOfType, a pandas 'object' column is
    validated at the schema level (no per-row check, no row-level result fields)."""
    expectation = gxe.ExpectColumnTypeToBe(column=INTEGER_COLUMN, type_="int")
    result = batch_for_datasource.validate(expectation)
    assert not result.success
    assert result.result == {"observed_value": "object_"}
    # None of the row-level fields ExpectColumnValuesToBeOfType would emit are present.
    assert not (ROW_LEVEL_RESULT_KEYS & set(result.result.keys()))


@parameterize_batch_for_data_sources(
    data_source_configs=[PandasDataFrameDatasourceTestConfig()],
    data=OBJECT_DATA,
)
def test_pandas_object_column_success_with_object_type(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnTypeToBe(column=INTEGER_COLUMN, type_="object")
    result = batch_for_datasource.validate(expectation)
    assert result.success
    assert result.result == {"observed_value": "object_"}


# Group datasources with case-insensitive type handling
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


@pytest.mark.parametrize(
    "suite_param_value,expected_result",
    [
        pytest.param("int64", True, id="success"),
    ],
)
@parameterize_batch_for_data_sources(
    data_source_configs=[PandasDataFrameDatasourceTestConfig()],
    data=DATA,
)
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
