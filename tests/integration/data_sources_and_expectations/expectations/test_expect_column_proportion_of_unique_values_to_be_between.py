from collections.abc import Sequence

import pandas as pd
import pytest
from sqlalchemy import types as sqlatypes

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    JUST_PANDAS_DATA_SOURCES,
)
from tests.integration.test_utils.data_source_config import RedshiftDatasourceTestConfig
from tests.integration.test_utils.data_source_config.base import DataSourceTestConfig
from tests.integration.test_utils.data_source_config.big_query import BigQueryDatasourceTestConfig
from tests.integration.test_utils.data_source_config.databricks import (
    DatabricksDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.mssql import MSSQLDatasourceTestConfig
from tests.integration.test_utils.data_source_config.mysql import MySQLDatasourceTestConfig
from tests.integration.test_utils.data_source_config.pandas_data_frame import (
    PandasDataFrameDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.pandas_filesystem_csv import (
    PandasFilesystemCsvDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.postgres import PostgreSQLDatasourceTestConfig
from tests.integration.test_utils.data_source_config.snowflake import SnowflakeDatasourceTestConfig
from tests.integration.test_utils.data_source_config.spark_filesystem_csv import (
    SparkFilesystemCsvDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.sqlite import SqliteDatasourceTestConfig

ALL_UNIQUE_COL = "all_unique"
NO_UNIQUE_COL = "one_unique"
SOME_UNIQUE_COL = "some_unique"
STRING_COL = "my_strings"


A_LOT_OF_NONES = [None] * 10
DATA = pd.DataFrame(
    {
        ALL_UNIQUE_COL: [0, 1, 2, 3, *A_LOT_OF_NONES],
        NO_UNIQUE_COL: [None, None, None, None, *A_LOT_OF_NONES],
        SOME_UNIQUE_COL: [1, 2, 3, 3, *A_LOT_OF_NONES],
        STRING_COL: ["foo", "foo", "bar", "baz", *A_LOT_OF_NONES],
    },
    dtype="object",
)

COLUMN_TYPES = {NO_UNIQUE_COL: sqlatypes.INTEGER}
try:
    from great_expectations.compatibility.pyspark import types as PYSPARK_TYPES

    SPARK_COLUMN_TYPES = {
        ALL_UNIQUE_COL: PYSPARK_TYPES.IntegerType,
        NO_UNIQUE_COL: PYSPARK_TYPES.IntegerType,
        SOME_UNIQUE_COL: PYSPARK_TYPES.IntegerType,
        STRING_COL: PYSPARK_TYPES.StringType,
    }
except ModuleNotFoundError:
    SPARK_COLUMN_TYPES = {}

ALL_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    BigQueryDatasourceTestConfig(column_types=COLUMN_TYPES),
    DatabricksDatasourceTestConfig(column_types=COLUMN_TYPES),
    MSSQLDatasourceTestConfig(column_types=COLUMN_TYPES),
    MySQLDatasourceTestConfig(column_types=COLUMN_TYPES),
    PandasDataFrameDatasourceTestConfig(),
    PandasFilesystemCsvDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(column_types=COLUMN_TYPES),
    RedshiftDatasourceTestConfig(column_types=COLUMN_TYPES),
    SnowflakeDatasourceTestConfig(column_types=COLUMN_TYPES),
    SparkFilesystemCsvDatasourceTestConfig(column_types=SPARK_COLUMN_TYPES),
    SqliteDatasourceTestConfig(column_types=COLUMN_TYPES),
]


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=DATA)
def test_success_complete_results(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnProportionOfUniqueValuesToBeBetween(
        column=SOME_UNIQUE_COL, min_value=0.75, max_value=0.75
    )
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success
    assert result.to_json_dict()["result"] == {"observed_value": 0.75}


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=DATA)
def test_strings(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnProportionOfUniqueValuesToBeBetween(
        column=STRING_COL, min_value=0.75, max_value=0.75
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnProportionOfUniqueValuesToBeBetween(column=SOME_UNIQUE_COL),
            id="vacuously_true",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfUniqueValuesToBeBetween(
                column=SOME_UNIQUE_COL, min_value=0.75, max_value=0.75
            ),
            id="some_unique",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfUniqueValuesToBeBetween(
                column=ALL_UNIQUE_COL, min_value=1, max_value=1
            ),
            id="all_unique",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfUniqueValuesToBeBetween(
                column=NO_UNIQUE_COL, min_value=0, max_value=0
            ),
            id="no_unique",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfUniqueValuesToBeBetween(
                column=SOME_UNIQUE_COL, min_value=0.75
            ),
            id="only_min",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfUniqueValuesToBeBetween(
                column=SOME_UNIQUE_COL, min_value=0.75
            ),
            id="only_max",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfUniqueValuesToBeBetween(
                column=SOME_UNIQUE_COL,
                min_value=0.74,
                max_value=0.76,
                strict_min=True,
                strict_max=True,
            ),
            id="strict_bounds",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(
    batch_for_datasource: Batch, expectation: gxe.ExpectColumnProportionOfUniqueValuesToBeBetween
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnProportionOfUniqueValuesToBeBetween(
                column=SOME_UNIQUE_COL, min_value=0.75, strict_min=True
            ),
            id="strict_min",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfUniqueValuesToBeBetween(
                column=SOME_UNIQUE_COL, max_value=0.75, strict_max=True
            ),
            id="strict_max",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfUniqueValuesToBeBetween(
                column=SOME_UNIQUE_COL, min_value=0.8, max_value=0.9
            ),
            id="wrong_bounds",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(
    batch_for_datasource: Batch, expectation: gxe.ExpectColumnProportionOfUniqueValuesToBeBetween
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success
