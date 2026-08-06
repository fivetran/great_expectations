import pandas as pd
import pytest
from sqlalchemy import types as sqlatypes

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.expectations.core.expect_column_quantile_values_to_be_between import (
    QuantileRange,
)
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    ALL_DATA_SOURCES,
    JUST_PANDAS_DATA_SOURCES,
)
from tests.integration.test_utils.data_source_config import (
    GenericSQLDatasourceTestConfig,
    RedshiftDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.big_query import BigQueryDatasourceTestConfig
from tests.integration.test_utils.data_source_config.databricks import (
    DatabricksDatasourceTestConfig,
)
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
from tests.integration.test_utils.data_source_config.sql_server import SQLServerDatasourceTestConfig
from tests.integration.test_utils.data_source_config.sqlite import SqliteDatasourceTestConfig

COL_NAME = "my_col"

DATA = pd.DataFrame({COL_NAME: [1, 2, 2, 3, 3, 3, 4]})

ALL_NULLS = pd.DataFrame({COL_NAME: [None, None, None]}, dtype="object")

# An all-null column carries no type of its own, so each backend is told what to make it.
ALL_NULLS_COLUMN_TYPES = {COL_NAME: sqlatypes.INTEGER}
try:
    from great_expectations.compatibility.pyspark import types as PYSPARK_TYPES

    ALL_NULLS_SPARK_COLUMN_TYPES = {COL_NAME: PYSPARK_TYPES.IntegerType}
except ModuleNotFoundError:
    ALL_NULLS_SPARK_COLUMN_TYPES = {}

ALL_NULLS_DATA_SOURCES = [
    BigQueryDatasourceTestConfig(column_types=ALL_NULLS_COLUMN_TYPES),
    DatabricksDatasourceTestConfig(column_types=ALL_NULLS_COLUMN_TYPES),
    SQLServerDatasourceTestConfig(column_types=ALL_NULLS_COLUMN_TYPES),
    MySQLDatasourceTestConfig(column_types=ALL_NULLS_COLUMN_TYPES),
    PandasDataFrameDatasourceTestConfig(),
    PandasFilesystemCsvDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(column_types=ALL_NULLS_COLUMN_TYPES),
    RedshiftDatasourceTestConfig(column_types=ALL_NULLS_COLUMN_TYPES),
    GenericSQLDatasourceTestConfig(column_types=ALL_NULLS_COLUMN_TYPES),
    SnowflakeDatasourceTestConfig(column_types=ALL_NULLS_COLUMN_TYPES),
    SparkFilesystemCsvDatasourceTestConfig(column_types=ALL_NULLS_SPARK_COLUMN_TYPES),
    SqliteDatasourceTestConfig(column_types=ALL_NULLS_COLUMN_TYPES),
]

ALL_DATA_SOURCES_EXCEPT_BIGQUERY = [
    ds for ds in ALL_DATA_SOURCES if not isinstance(ds, BigQueryDatasourceTestConfig)
]

# TODO: Consider more test cases before removing expect_column_quantile_values_to_be_between.json


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES_EXCEPT_BIGQUERY, data=DATA
)
def test_success_complete_results(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnQuantileValuesToBeBetween(
        column=COL_NAME,
        quantile_ranges=QuantileRange(
            quantiles=[0, 0.333, 0.667, 1],
            value_ranges=[[0, 1], [2, 3], [3, 4], [4, 5]],
        ),
    )
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success
    assert result.to_json_dict()["result"] == {
        "observed_value": {
            "quantiles": [0.0, 0.333, 0.667, 1.0],
            "values": [1, 2, 3, 4],
        },
        "details": {
            "success_details": [True, True, True, True],
        },
    }


# Every backend, including BigQuery: this asserts only that no quantile was observed, so unlike
# the cases above it does not depend on the type or shape of a returned value.
@parameterize_batch_for_data_sources(data_source_configs=ALL_NULLS_DATA_SOURCES, data=ALL_NULLS)
def test_all_null_column_reports_unmet_expectation(batch_for_datasource: Batch) -> None:
    """A column with no quantiles fails the expectation instead of raising.

    The backends report the absent quantile differently -- SQL engines return NULL, pandas
    returns NaN, and Spark returns no values at all -- and every one of them must report it as
    an unmet expectation.
    """
    expectation = gxe.ExpectColumnQuantileValuesToBeBetween(
        column=COL_NAME,
        quantile_ranges=QuantileRange(quantiles=[0.25, 0.5], value_ranges=[[0, 99], [0, 99]]),
    )
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert not result.success
    assert result.to_json_dict()["result"] == {
        "observed_value": {
            "quantiles": [0.25, 0.5],
            "values": [None, None],
        },
        "details": {
            "success_details": [False, False],
        },
    }


@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_allows_unspecified_extremes(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnQuantileValuesToBeBetween(
        column=COL_NAME,
        quantile_ranges=QuantileRange(
            quantiles=[0, 0.333, 0.667, 1],
            value_ranges=[[None, 1], [2, 3], [3, 4], [4, None]],
        ),
    )
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success


@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnQuantileValuesToBeBetween(
        column=COL_NAME,
        quantile_ranges=QuantileRange(
            quantiles=[0, 0.333, 0.667, 1],
            value_ranges=[[0, 1], [1, 2], [1, 2], [2, 3]],
        ),
    )
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert not result.success


@pytest.mark.parametrize(
    "suite_param_value,expected_result",
    [
        pytest.param(
            {
                "quantiles": [0, 0.333, 0.667, 1],
                "value_ranges": [[0, 1], [2, 3], [3, 4], [4, 5]],
            },
            True,
            id="success",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success_with_suite_param_quantile_ranges_(
    batch_for_datasource: Batch, suite_param_value: dict, expected_result: bool
) -> None:
    suite_param_key = "test_expect_column_quantile_values_to_be_between"
    expectation = gxe.ExpectColumnQuantileValuesToBeBetween(
        column=COL_NAME,
        quantile_ranges={"$PARAMETER": suite_param_key},
        result_format=ResultFormat.SUMMARY,
    )
    result = batch_for_datasource.validate(
        expectation, expectation_parameters={suite_param_key: suite_param_value}
    )
    assert result.success == expected_result


@pytest.mark.parametrize(
    "suite_param_value,expected_result",
    [
        pytest.param(False, True, id="success"),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success_with_suite_param_allow_relative_error_(
    batch_for_datasource: Batch, suite_param_value: bool, expected_result: bool
) -> None:
    suite_param_key = "test_expect_column_quantile_values_to_be_between"
    expectation = gxe.ExpectColumnQuantileValuesToBeBetween(
        column=COL_NAME,
        quantile_ranges=QuantileRange(
            quantiles=[0, 0.333, 0.667, 1],
            value_ranges=[[0, 1], [2, 3], [3, 4], [4, 5]],
        ),
        allow_relative_error={"$PARAMETER": suite_param_key},
        result_format=ResultFormat.SUMMARY,
    )
    result = batch_for_datasource.validate(
        expectation, expectation_parameters={suite_param_key: suite_param_value}
    )
    assert result.success == expected_result
