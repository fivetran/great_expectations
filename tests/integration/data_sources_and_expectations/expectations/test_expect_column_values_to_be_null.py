from unittest.mock import ANY

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    JUST_PANDAS_DATA_SOURCES,
    SQL_DATA_SOURCES,
)
from tests.integration.test_utils.data_source_config import SparkFilesystemCsvDatasourceTestConfig

ALL_NULL_COLUMN = "all_nulls"
MOSTLY_NULL_COLUMN = "mostly_nulls"

DATA = pd.DataFrame(
    {
        MOSTLY_NULL_COLUMN: [1, None, None, None, None],  # 80% null
        ALL_NULL_COLUMN: [None, None, None, None, None],
    },
    dtype="object",
)

try:
    from great_expectations.compatibility.pyspark import types as PYSPARK_TYPES

    SPARK_COLUMN_TYPES = {
        MOSTLY_NULL_COLUMN: PYSPARK_TYPES.IntegerType,
        ALL_NULL_COLUMN: PYSPARK_TYPES.IntegerType,
    }
except ModuleNotFoundError:
    SPARK_COLUMN_TYPES = {}


@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success_complete_pandas(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToBeNull(column=ALL_NULL_COLUMN)
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=[
        SparkFilesystemCsvDatasourceTestConfig(column_types=SPARK_COLUMN_TYPES),
    ],
    data=DATA,
)
def test_success_complete_spark(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToBeNull(column=ALL_NULL_COLUMN)
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success


@parameterize_batch_for_data_sources(data_source_configs=SQL_DATA_SOURCES, data=DATA)
def test_success_complete_sql(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToBeNull(column=ALL_NULL_COLUMN)
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success
    assert result.to_json_dict()["result"] == {
        "element_count": 5,
        "unexpected_count": 0,
        "unexpected_percent": 0.0,
        "partial_unexpected_list": [],
        "unexpected_index_query": ANY,
        "partial_unexpected_counts": [],
        "unexpected_list": [],
    }


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValuesToBeNull(column=ALL_NULL_COLUMN),
            id="all_nulls",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeNull(column=MOSTLY_NULL_COLUMN, mostly=0.8),
            id="mostly_nulls_success",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnValuesToBeNull,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValuesToBeNull(column=MOSTLY_NULL_COLUMN),
            id="not_all_nulls",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeNull(column=MOSTLY_NULL_COLUMN, mostly=0.9),
            id="mostly_threshold_not_met",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnValuesToBeNull,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success
