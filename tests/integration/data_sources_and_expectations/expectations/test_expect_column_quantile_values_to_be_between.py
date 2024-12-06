import pandas as pd

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
from tests.integration.test_utils.data_source_config.big_query import BigQueryDatasourceTestConfig

COL_NAME = "my_col"

DATA = pd.DataFrame({COL_NAME: [1, 2, 2, 3, 3, 3, 4]})

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
