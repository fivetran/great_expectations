from typing import Literal, Sequence

import pandas as pd
import pytest
from sqlalchemy import types as sqlatypes

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

COLUMN = "amount"

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

try:
    from great_expectations.compatibility.pyspark import types as PYSPARK_TYPES

    SPARK_DECIMAL_COLUMN_TYPES = {COLUMN: PYSPARK_TYPES.DecimalType}
except ModuleNotFoundError:
    SPARK_DECIMAL_COLUMN_TYPES = {}

# The statistics come back from the engine in the column's own type - Decimal for a SQL
# NUMERIC column and for Spark's DecimalType - and have to survive the float arithmetic
# the threshold is built from.
DECIMAL_COLUMN_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    PostgreSQLDatasourceTestConfig(column_types={COLUMN: sqlatypes.NUMERIC}),
    SparkFilesystemCsvDatasourceTestConfig(column_types=SPARK_DECIMAL_COLUMN_TYPES),
]

CLEAN_DATA = pd.DataFrame({COLUMN: list(range(1, 21))})
DATA_WITH_OUTLIER = pd.DataFrame({COLUMN: [*range(1, 21), 100]})
DATA_WITH_OUTLIER_AND_NULL = pd.DataFrame(
    {
        "row_id": range(22),
        COLUMN: pd.Series([*range(1, 21), 100, None], dtype=object),
    }
)
DATA_WITH_VALUES_ON_IQR_BOUNDARY = pd.DataFrame({COLUMN: [0, 1, 2, 3, 4]})
# Q1, the median, and Q3 are all 7, so the interquartile range - and the threshold built
# from it - is zero.
DATA_WITHOUT_SPREAD = pd.DataFrame({COLUMN: [1, *([7] * 8), 100]})
SINGLE_ROW_DATA = pd.DataFrame({COLUMN: [5]})
# Sized so the sample and population standard deviations straddle the threshold: the
# sample figure is sqrt(80/4) = 4.472 and the population figure sqrt(80/5) = 4.0, so at a
# multiplier of 1.9 the distance of 8 from the mean of 2 clears the first and not the
# second.
DATA_SENSITIVE_TO_SAMPLE_STANDARD_DEVIATION = pd.DataFrame({COLUMN: [0, 0, 0, 0, 10]})


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
    method: Literal["iqr", "std"],
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
    method: Literal["iqr", "std"],
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
    data=CLEAN_DATA,
)
def test_quartiles_are_interpolated_consistently_across_engines(
    batch_for_datasource: Batch,
) -> None:
    """Pin the quartiles to continuous, linearly interpolated percentiles.

    Twenty rows put every quartile between two values: Q1 is 5.75, the median 10.5 and Q3
    15.25, so the interquartile range is 9.5 and 1 and 20 sit exactly on the threshold.
    An engine that reports the quartiles as dataset elements instead - the discrete
    definition - would see a range of 10 around a median of 10 and clear the value 1.
    """
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
    assert sorted(result.result["unexpected_list"]) == [1, 20]


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


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=DATA_WITHOUT_SPREAD,
)
def test_a_zero_spread_leaves_the_center_alone(
    batch_for_datasource: Batch,
) -> None:
    """A threshold of zero must not report every row - including the center - an outlier."""
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
    assert result.result["unexpected_count"] == 2
    assert sorted(result.result["unexpected_list"]) == [1, 100]


@pytest.mark.parametrize(
    "method",
    [
        pytest.param("iqr", id="iqr"),
        pytest.param("std", id="standard_deviation"),
    ],
)
@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=CLEAN_DATA,
)
def test_a_zero_multiplier_admits_only_the_center(
    batch_for_datasource: Batch,
    method: Literal["iqr", "std"],
) -> None:
    """A zero multiplier collapses a genuinely non-zero spread.

    `CLEAN_DATA` has a real spread under both methods, so this exercises the multiplier
    itself rather than retreading the zero-spread column. Twenty rows put the center
    between two values under either method, so no row sits on it and every row is an
    outlier.
    """
    expectation = gxe.ExpectColumnValuesToNotBeOutliers(
        column=COLUMN,
        method=method,
        multiplier=0.0,
    )

    result = batch_for_datasource.validate(expectation)

    assert not result.success
    assert result.result["unexpected_count"] == 20


@pytest.mark.parametrize(
    ("method", "multiplier"),
    [
        pytest.param("iqr", 1.5, id="iqr"),
        pytest.param("std", 3.0, id="standard_deviation"),
    ],
)
@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=SINGLE_ROW_DATA,
)
def test_a_single_row_is_not_an_outlier_against_itself(
    batch_for_datasource: Batch,
    method: Literal["iqr", "std"],
    multiplier: float,
) -> None:
    """One value reaches the two methods differently.

    A sample standard deviation is undefined for one value, so there is no statistic at
    all; the interquartile range is defined but zero, so the threshold collapses and the
    lone value is its own center. Neither may report it an outlier.
    """
    expectation = gxe.ExpectColumnValuesToNotBeOutliers(
        column=COLUMN,
        method=method,
        multiplier=multiplier,
    )

    result = batch_for_datasource.validate(
        expectation,
        result_format=ResultFormat.COMPLETE,
    )

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
    data_source_configs=DECIMAL_COLUMN_DATA_SOURCES,
    data=DATA_WITH_OUTLIER,
)
def test_decimal_columns_are_evaluated(
    batch_for_datasource: Batch,
    method: Literal["iqr", "std"],
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
    assert [float(value) for value in result.result["unexpected_list"]] == [100.0]


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=DATA_SENSITIVE_TO_SAMPLE_STANDARD_DEVIATION,
)
def test_the_standard_deviation_is_the_sample_statistic_on_every_engine(
    batch_for_datasource: Batch,
) -> None:
    """Pin the divisor to n-1 across engines.

    Engines reach this differently - pandas' default ddof, STDDEV_SAMP, SQL Server's
    STDEV, and a hand-rolled two-pass on SQLite - and nothing else in this file would
    notice one of them computing the population figure instead. On this data that
    substitution flips the verdict.
    """
    expectation = gxe.ExpectColumnValuesToNotBeOutliers(
        column=COLUMN,
        method="std",
        multiplier=1.9,
    )

    result = batch_for_datasource.validate(expectation)

    assert result.success
    assert result.result["unexpected_count"] == 0
