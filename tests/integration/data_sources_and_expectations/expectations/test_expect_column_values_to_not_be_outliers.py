from typing import List, Literal, Sequence

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
# Q1 is 1 and Q3 is 3 on these five rows, so the interquartile range is 2 and a
# multiplier of 0.5 puts the fences exactly on the smallest and largest values.
DATA_WITH_VALUES_ON_IQR_FENCES = pd.DataFrame({COLUMN: [0, 1, 2, 3, 4]})
# Nine rows put every quartile exactly on an element - Q1 is 1, the median 2 and Q3 15 -
# so the interquartile range is 14 and the column is skewed hard to the right. That skew
# is where fences drawn from the quartiles and a window centred on the median part ways.
RIGHT_SKEWED_DATA = pd.DataFrame({COLUMN: [0, 1, 1, 2, 2, 3, 15, 16, 34]})
# The same column with its largest value pushed past the upper fence of 36. It stays the
# maximum, so the quartiles - and therefore the fences - are unmoved.
RIGHT_SKEWED_DATA_ABOVE_THE_UPPER_FENCE = pd.DataFrame(
    {COLUMN: [*RIGHT_SKEWED_DATA[COLUMN].iloc[:-1], 40]}
)
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

    Twenty rows put both quartiles between two values: Q1 is 5.75 and Q3 15.25, so the
    interquartile range is 9.5 and a multiplier of 0.45 draws the fences at 1.475 and
    19.525 - just inside 1 and 20, which are therefore outliers. An engine that averages
    the two straddling values instead would see quartiles of 5.5 and 15.5 around a range
    of 10, putting the fences exactly on 1 and 20 and reporting no outliers at all.
    """
    expectation = gxe.ExpectColumnValuesToNotBeOutliers(
        column=COLUMN,
        method="iqr",
        multiplier=0.45,
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


@pytest.mark.parametrize(
    ("multiplier", "expected_outliers"),
    [
        pytest.param(0.5, [], id="on_the_fences"),
        pytest.param(0.25, [0, 4], id="outside_the_fences"),
    ],
)
@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=DATA_WITH_VALUES_ON_IQR_FENCES,
)
def test_values_on_the_fences_are_not_outliers(
    batch_for_datasource: Batch,
    multiplier: float,
    expected_outliers: List[int],
) -> None:
    """Pin the fences as closed, following the convention a boxplot whisker draws.

    Q1 is 1 and Q3 is 3, so a multiplier of 0.5 lands the fences exactly on 0 and 4 and
    neither is an outlier. Pulling the multiplier back to 0.25 moves the fences inside
    those two values, and both become outliers - so the pair distinguishes an inclusive
    boundary from an exclusive one rather than merely from a misplaced fence.
    """
    expectation = gxe.ExpectColumnValuesToNotBeOutliers(
        column=COLUMN,
        method="iqr",
        multiplier=multiplier,
    )

    result = batch_for_datasource.validate(
        expectation,
        result_format=ResultFormat.COMPLETE,
    )

    assert result.success is (not expected_outliers)
    assert result.result["unexpected_count"] == len(expected_outliers)
    assert sorted(result.result["unexpected_list"]) == expected_outliers


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=DATA_WITHOUT_SPREAD,
)
def test_a_zero_spread_leaves_the_center_alone(
    batch_for_datasource: Batch,
) -> None:
    """A zero interquartile range must not report every row - the quartile included."""
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


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=DATA_WITH_VALUES_ON_IQR_FENCES,
)
def test_a_zero_multiplier_admits_the_quartile_range(
    batch_for_datasource: Batch,
) -> None:
    """A zero multiplier collapses the fences onto the quartiles, not onto the middle.

    What is left is the closed range from Q1 to Q3 - here 1 to 3 - so the three rows
    inside it pass and only the two outside are outliers. This column has a genuinely
    non-zero interquartile range, so it exercises the multiplier itself rather than
    retreading the column with no spread.
    """
    expectation = gxe.ExpectColumnValuesToNotBeOutliers(
        column=COLUMN,
        method="iqr",
        multiplier=0.0,
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
    data=CLEAN_DATA,
)
def test_a_zero_multiplier_admits_only_the_mean(
    batch_for_datasource: Batch,
) -> None:
    """A zero multiplier collapses a genuinely non-zero standard deviation.

    `CLEAN_DATA` has a real spread, so this exercises the multiplier itself rather than
    retreading a column that has none. Twenty rows put the mean between two values, so no
    row sits on it and every row is an outlier.
    """
    expectation = gxe.ExpectColumnValuesToNotBeOutliers(
        column=COLUMN,
        method="std",
        multiplier=0.0,
    )

    result = batch_for_datasource.validate(expectation)

    assert not result.success
    assert result.result["unexpected_count"] == 20


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=RIGHT_SKEWED_DATA,
)
def test_each_fence_is_measured_from_its_own_quartile(
    batch_for_datasource: Batch,
) -> None:
    """Pin the rule to fences drawn from the quartiles, not a window around the median.

    Q1 is 1 and Q3 15, so the interquartile range is 14 and at a multiplier of 1.5 the
    fences reach out to -20 and 36: every value in the column clears them. A window of the
    same half-width measured from the median of 2 instead would span -19 to 23 and report
    34 an outlier. The difference is the whole point of measuring each side from its own
    quartile - on a right-skewed column the median sits far below Q3, and a window
    centred on it falls short on the long tail.
    """
    expectation = gxe.ExpectColumnValuesToNotBeOutliers(
        column=COLUMN,
        method="iqr",
        multiplier=1.5,
    )

    result = batch_for_datasource.validate(
        expectation,
        result_format=ResultFormat.COMPLETE,
    )

    assert result.success
    assert result.result["unexpected_count"] == 0


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=RIGHT_SKEWED_DATA_ABOVE_THE_UPPER_FENCE,
)
def test_a_value_past_the_upper_fence_is_an_outlier(
    batch_for_datasource: Batch,
) -> None:
    """The wider window still has an edge, and it sits between 34 and 40.

    This is the previous column with its largest value moved from 34 to 40. The value
    stays the maximum, so the quartiles and the fences are unchanged at -20 and 36 - but
    40 now clears the upper one. Reading the two tests together pins the fence to a
    location rather than merely somewhere beyond the data.
    """
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
    assert result.result["unexpected_count"] == 1
    assert result.result["unexpected_list"] == [40]


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
