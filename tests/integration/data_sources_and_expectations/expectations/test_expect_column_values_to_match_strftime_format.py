from typing import Sequence

import pandas as pd

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    PandasFilesystemCsvDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.base import DataSourceTestConfig

TIMESTAMPS = "timestamps"
MIXED_FORMAT_TIMESTAMPS = "mixed_format_timestamps"

try:
    from great_expectations.compatibility.pyspark import types as PYSPARK_TYPES

    SPARK_COLUMN_TYPES = {
        TIMESTAMPS: PYSPARK_TYPES.StringType,
        MIXED_FORMAT_TIMESTAMPS: PYSPARK_TYPES.StringType,
    }
except ModuleNotFoundError:
    SPARK_COLUMN_TYPES = {}

SUPPORTED_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    PandasFilesystemCsvDatasourceTestConfig(),
    SparkFilesystemCsvDatasourceTestConfig(column_types=SPARK_COLUMN_TYPES),
]

DATA = pd.DataFrame(
    {
        TIMESTAMPS: [
            "2026-01-15T10:30:00+0000",
            "2026-06-20T14:45:00+0000",
            "2026-12-31T23:59:59+0000",
        ],
        MIXED_FORMAT_TIMESTAMPS: [
            "2026-01-15T10:30:00+0000",
            "2026-06-20T14:45:00+0000",
            "not-a-timestamp",
        ],
    }
)


@parameterize_batch_for_data_sources(data_source_configs=SUPPORTED_DATA_SOURCES, data=DATA)
def test_timezone_aware_format_success(batch_for_datasource: Batch) -> None:
    """Regression test for #9203: %z in strftime_format must not raise.

    Previously, the Spark metric's inline validation used datetime.now()
    (naive), so %z rendered as empty and the strftime->strptime round-trip
    failed at metric execution time.
    """
    expectation = gxe.ExpectColumnValuesToMatchStrftimeFormat(
        column=TIMESTAMPS,
        strftime_format="%Y-%m-%dT%H:%M:%S%z",
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(data_source_configs=SUPPORTED_DATA_SOURCES, data=DATA)
def test_non_matching_format_failure(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToMatchStrftimeFormat(
        column=TIMESTAMPS,
        strftime_format="%Y-%m-%d",
    )
    result = batch_for_datasource.validate(expectation)
    assert not result.success


@parameterize_batch_for_data_sources(data_source_configs=SUPPORTED_DATA_SOURCES, data=DATA)
def test_mostly_threshold_met_success(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToMatchStrftimeFormat(
        column=MIXED_FORMAT_TIMESTAMPS,
        strftime_format="%Y-%m-%dT%H:%M:%S%z",
        mostly=0.5,
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(data_source_configs=SUPPORTED_DATA_SOURCES, data=DATA)
def test_mostly_threshold_not_met_failure(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToMatchStrftimeFormat(
        column=MIXED_FORMAT_TIMESTAMPS,
        strftime_format="%Y-%m-%dT%H:%M:%S%z",
        mostly=0.9,
    )
    result = batch_for_datasource.validate(expectation)
    assert not result.success
