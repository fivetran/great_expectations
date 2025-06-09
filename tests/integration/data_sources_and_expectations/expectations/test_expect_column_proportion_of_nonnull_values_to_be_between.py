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

ALL_NONNULL_COL = "all_nonnull"
HALF_NONNULL_COL = "half_nonnull"
MOSTLY_NONNULL_COL = "mostly_nonnull"
NO_NONNULL_COL = "no_nonnull"
STRING_COL = "my_strings"


# Create a sample dataframe with different proportions of nonnull values
DATA = pd.DataFrame(
    {
        ALL_NONNULL_COL: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        HALF_NONNULL_COL: [0, 1, 2, 3, 4, None, None, None, None, None],
        MOSTLY_NONNULL_COL: [0, 1, 2, 3, 4, 5, 6, 7, None, None],
        NO_NONNULL_COL: [None, None, None, None, None, None, None, None, None, None],
        STRING_COL: ["foo", "bar", "baz", None, None, "qux", "quux", None, "corge", None],
    },
    dtype="object",
)

COLUMN_TYPES = {NO_NONNULL_COL: sqlatypes.INTEGER}
try:
    from great_expectations.compatibility.pyspark import types as PYSPARK_TYPES

    SPARK_COLUMN_TYPES = {
        ALL_NONNULL_COL: PYSPARK_TYPES.IntegerType,
        HALF_NONNULL_COL: PYSPARK_TYPES.IntegerType,
        MOSTLY_NONNULL_COL: PYSPARK_TYPES.IntegerType,
        NO_NONNULL_COL: PYSPARK_TYPES.IntegerType,
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
    expectation = gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
        column=HALF_NONNULL_COL, min_value=0.5, max_value=0.5
    )
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success
    assert result.to_json_dict()["result"] == {"observed_value": 0.5}


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=DATA)
def test_strings(batch_for_datasource: Batch) -> None:
    # String column has 6 non-null values out of 10 (60%)
    expectation = gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
        column=STRING_COL, min_value=0.6, max_value=0.6
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(column=HALF_NONNULL_COL),
            id="vacuously_true",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
                column=HALF_NONNULL_COL, min_value=0.5, max_value=0.5
            ),
            id="half_nonnull",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
                column=ALL_NONNULL_COL, min_value=1.0, max_value=1.0
            ),
            id="all_nonnull",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
                column=NO_NONNULL_COL, min_value=0.0, max_value=0.0
            ),
            id="no_nonnull",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
                column=MOSTLY_NONNULL_COL, min_value=0.8
            ),
            id="only_min",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
                column=MOSTLY_NONNULL_COL, max_value=0.8
            ),
            id="only_max",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
                column=MOSTLY_NONNULL_COL,
                min_value=0.79,
                max_value=0.81,
                strict_min=True,
                strict_max=True,
            ),
            id="strict_bounds",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(
    batch_for_datasource: Batch, expectation: gxe.ExpectColumnProportionOfNonNullValuesToBeBetween
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
                column=HALF_NONNULL_COL, min_value=0.5, strict_min=True
            ),
            id="strict_min",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
                column=HALF_NONNULL_COL, max_value=0.5, strict_max=True
            ),
            id="strict_max",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
                column=HALF_NONNULL_COL, min_value=0.6, max_value=0.7
            ),
            id="wrong_bounds",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(
    batch_for_datasource: Batch, expectation: gxe.ExpectColumnProportionOfNonNullValuesToBeBetween
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success
