from typing import Sequence

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    BigQueryDatasourceTestConfig,
    DatabricksDatasourceTestConfig,
    MySQLDatasourceTestConfig,
    PandasDataFrameDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    RedshiftDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
    SqliteDatasourceTestConfig,
    SQLServerDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.base import DataSourceTestConfig

ALL_SUPPORTED_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    PandasDataFrameDatasourceTestConfig(),
    SparkFilesystemCsvDatasourceTestConfig(),
    SqliteDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    MySQLDatasourceTestConfig(),
    SQLServerDatasourceTestConfig(),
    BigQueryDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    DatabricksDatasourceTestConfig(),
    RedshiftDatasourceTestConfig(),
]

COLUMN = "amount"
CLEAN_DATA = pd.DataFrame({COLUMN: list(range(1, 21))})
DATA_WITH_OUTLIER = pd.DataFrame({COLUMN: [*range(1, 21), 100]})
DATA_WITH_OUTLIER_AND_NULL = pd.DataFrame(
    {
        "row_id": range(22),
        COLUMN: pd.Series([*range(1, 21), 100, None], dtype=object),
    }
)
DATA_WITH_VALUES_ON_IQR_BOUNDARY = pd.DataFrame({COLUMN: [0, 1, 2, 3, 4]})


@pytest.mark.parametrize(
    ("method", "multiplier"),
    [
        pytest.param("iqr", 1.5, id="iqr"),
        pytest.param("std", 3.0, id="standard_deviation"),
    ],
)
@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=CLEAN_DATA,
)
def test_clean_data_passes(
    batch_for_datasource: Batch,
    method: str,
    multiplier: float,
) -> None:
    expectation = gxe.ExpectColumnValuesToNotBeOutliers(
        column=COLUMN,
        method=method,
        multiplier=multiplier,
    )

    result = batch_for_datasource.validate(expectation)

    assert result.success
    assert result.result["unexpected_count"] == 0


@pytest.mark.parametrize(
    ("method", "multiplier"),
    [
        pytest.param("iqr", 1.5, id="iqr"),
        pytest.param("std", 3.0, id="standard_deviation"),
    ],
)
@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=DATA_WITH_OUTLIER,
)
def test_injected_outlier_fails_consistently_across_engines(
    batch_for_datasource: Batch,
    method: str,
    multiplier: float,
) -> None:
    expectation = gxe.ExpectColumnValuesToNotBeOutliers(
        column=COLUMN,
        method=method,
        multiplier=multiplier,
    )

    result = batch_for_datasource.validate(
        expectation,
        result_format=ResultFormat.COMPLETE,
    )

    assert not result.success
    assert result.result["unexpected_count"] == 1
    assert result.result["unexpected_list"] == [100]


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=DATA_WITH_OUTLIER_AND_NULL,
)
def test_nulls_are_excluded_from_statistics_and_evaluation(
    batch_for_datasource: Batch,
) -> None:
    expectation = gxe.ExpectColumnValuesToNotBeOutliers(
        column=COLUMN,
        method="iqr",
        multiplier=1.5,
    )

    result = batch_for_datasource.validate(
        expectation,
        result_format=ResultFormat.COMPLETE,
    )

    assert not result.success
    assert result.result["missing_count"] == 1
    assert result.result["unexpected_count"] == 1
    assert result.result["unexpected_list"] == [100]


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=DATA_WITH_VALUES_ON_IQR_BOUNDARY,
)
def test_values_equal_to_threshold_are_outliers(
    batch_for_datasource: Batch,
) -> None:
    expectation = gxe.ExpectColumnValuesToNotBeOutliers(
        column=COLUMN,
        method="iqr",
        multiplier=1.0,
    )

    result = batch_for_datasource.validate(
        expectation,
        result_format=ResultFormat.COMPLETE,
    )

    assert not result.success
    assert result.result["unexpected_count"] == 2
    assert sorted(result.result["unexpected_list"]) == [0, 4]
