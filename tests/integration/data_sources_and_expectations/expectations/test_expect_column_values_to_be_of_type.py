import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    JUST_PANDAS_DATA_SOURCES,
)
from tests.integration.test_utils.data_source_config import (
    BigQueryDatasourceTestConfig,
    DatabricksDatasourceTestConfig,
    MSSQLDatasourceTestConfig,
    MySQLDatasourceTestConfig,
    PandasDataFrameDatasourceTestConfig,
    PandasFilesystemCsvDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    RedshiftDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
    SqliteDatasourceTestConfig,
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


try:
    from great_expectations.compatibility.pyspark import types as PYSPARK_TYPES

    SPARK_COLUMN_TYPES = {
        INTEGER_COLUMN: PYSPARK_TYPES.IntegerType,
        INTEGER_AND_NULL_COLUMN: PYSPARK_TYPES.IntegerType,
        STRING_COLUMN: PYSPARK_TYPES.StringType,
        NULL_COLUMN: PYSPARK_TYPES.IntegerType,
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
def test_success_for_type__int(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToBeOfType(column=INTEGER_COLUMN, type_="int")
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=[
        BigQueryDatasourceTestConfig(),
        MSSQLDatasourceTestConfig(),
        MySQLDatasourceTestConfig(),
        PostgreSQLDatasourceTestConfig(),
        RedshiftDatasourceTestConfig(),
        SqliteDatasourceTestConfig(),
    ],
    data=DATA,
)
def test_success_for_type__INTEGER(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToBeOfType(column=INTEGER_COLUMN, type_="INTEGER")
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=[DatabricksDatasourceTestConfig()],
    data=DATA,
)
def test_success_for_type__Integer(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToBeOfType(column=INTEGER_COLUMN, type_="INT")
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
    expectation = gxe.ExpectColumnValuesToBeOfType(column=INTEGER_COLUMN, type_="IntegerType")
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=[SnowflakeDatasourceTestConfig()],
    data=DATA,
)
def test_success_for_type__Number(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToBeOfType(column=INTEGER_COLUMN, type_="DECIMAL(38, 0)")
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        gxe.ExpectColumnValuesToBeOfType(column=INTEGER_COLUMN, type_="int"),
        gxe.ExpectColumnValuesToBeOfType(column=INTEGER_AND_NULL_COLUMN, type_="int"),
        gxe.ExpectColumnValuesToBeOfType(column=STRING_COLUMN, type_="str"),
        gxe.ExpectColumnValuesToBeOfType(column=NULL_COLUMN, type_="float64"),
    ],
)
@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES,
    data=DATA,
)
def test_success_types(
    batch_for_datasource: Batch, expectation: gxe.ExpectColumnValuesToBeOfType
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES,
    data=DATA,
)
def test_failure(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToBeOfType(column=INTEGER_COLUMN, type_="NUMBER")
    result = batch_for_datasource.validate(expectation)
    assert not result.success
