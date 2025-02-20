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
from tests.integration.test_utils.data_source_config import (
    PandasDataFrameDatasourceTestConfig,
    PandasFilesystemCsvDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
)

NON_NULL_COLUMN = "none_nulls"
ALL_NULL_COLUMN = "oops_all_nulls"
MOSTLY_NULL_COLUMN = "mostly_nulls"

DATA = pd.DataFrame(
    {
        NON_NULL_COLUMN: [1, 2, 3, 4, 5],
        MOSTLY_NULL_COLUMN: pd.Series([1, None, None, None, None], dtype="object"),
        ALL_NULL_COLUMN: pd.Series([None, None, None, None, None], dtype="object"),
    },
)

try:
    from great_expectations.compatibility.pyspark import types as PYSPARK_TYPES

    SPARK_COLUMN_TYPES = {
        NON_NULL_COLUMN: PYSPARK_TYPES.IntegerType,
        MOSTLY_NULL_COLUMN: PYSPARK_TYPES.IntegerType,
        ALL_NULL_COLUMN: PYSPARK_TYPES.IntegerType,
    }
except ModuleNotFoundError:
    SPARK_COLUMN_TYPES = {}


@parameterize_batch_for_data_sources(
    data_source_configs=[PandasDataFrameDatasourceTestConfig()], data=DATA
)
def test_failure_pandas_dataframe(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToNotBeNull(column=MOSTLY_NULL_COLUMN)
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert not result.success
    assert result.to_json_dict()["result"] == {
        "element_count": 5,
        "unexpected_count": 4,
        "unexpected_percent": 80.0,
        "partial_unexpected_list": [None, None, None, None],
        "partial_unexpected_index_list": [1, 2, 3, 4],
        "partial_unexpected_counts": [
            {"count": 4, "value": None},
        ],
        "unexpected_list": [None, None, None, None],
        "unexpected_index_list": [1, 2, 3, 4],
        "unexpected_index_query": "df.filter(items=[1, 2, 3, 4], axis=0)",
    }


@parameterize_batch_for_data_sources(
    data_source_configs=[PandasFilesystemCsvDatasourceTestConfig()], data=DATA
)
def test_failure_pandas_csv(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToNotBeNull(column=MOSTLY_NULL_COLUMN)
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert not result.success
    assert result.to_json_dict()["result"] == {
        "element_count": 5,
        "unexpected_count": 4,
        "unexpected_percent": 80.0,
        "partial_unexpected_list": [None, None, None, None],
        "partial_unexpected_index_list": [1, 2, 3, 4],
        "partial_unexpected_counts": [
            # TODO: NOT THIS
            {"count": 1, "value": None},
            {"count": 1, "value": None},
            {"count": 1, "value": None},
            {"count": 1, "value": None},
        ],
        "unexpected_list": [None, None, None, None],
        "unexpected_index_list": [1, 2, 3, 4],
        "unexpected_index_query": "df.filter(items=[1, 2, 3, 4], axis=0)",
    }


@parameterize_batch_for_data_sources(
    data_source_configs=[
        SparkFilesystemCsvDatasourceTestConfig(
            column_types=SPARK_COLUMN_TYPES,
        )
    ],
    data=DATA,
)
def test_failure_spark(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToNotBeNull(column=MOSTLY_NULL_COLUMN)
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert not result.success
    assert result.to_json_dict()["result"] == {
        "element_count": 5,
        "unexpected_count": 4,
        "unexpected_percent": 80.0,
        "partial_unexpected_list": [None, None, None, None],
        "partial_unexpected_counts": [
            {"count": 4, "value": None},
        ],
        "unexpected_list": [None, None, None, None],
        "unexpected_index_query": ANY,
    }


@parameterize_batch_for_data_sources(data_source_configs=SQL_DATA_SOURCES, data=DATA)
def test_failure_complete_sql(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToNotBeNull(column=MOSTLY_NULL_COLUMN)
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert not result.success
    assert result.to_json_dict()["result"] == {
        "element_count": 5,
        "unexpected_count": 4,
        "unexpected_percent": 80.0,
        "partial_unexpected_list": [None, None, None, None],
        "partial_unexpected_counts": [
            {"count": 4, "value": None},
        ],
        "unexpected_list": [None, None, None, None],
        "unexpected_index_query": ANY,
    }


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValuesToNotBeNull(column=NON_NULL_COLUMN),
            id="no_nulls",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToNotBeNull(column=MOSTLY_NULL_COLUMN, mostly=0.2),
            id="mostly",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnValuesToNotBeNull,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValuesToNotBeNull(column=ALL_NULL_COLUMN),
            id="no_nulls",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToNotBeNull(column=MOSTLY_NULL_COLUMN, mostly=0.3),
            id="mostly_not_met",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnValuesToNotBeNull,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success
