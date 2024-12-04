"""
The tests here ensure that quoted identifiers work as expected.

Quoted identifiers needed are the mechanism used by DBs to allow specific casing and abnormal
characters in entity names. NOTE: The tests here indirectly test that quoted identifiers
work under the hood without us specifying them explicitly when instantiating expectations.
"""

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    SQL_DATA_SOURCES,
)
from tests.integration.test_utils.data_source_config import BigQueryDatasourceTestConfig

UPPER_CASE = "UNQUOTED_UPPER"
LOWER_CASE = "unquoted_lower"
MIXED_CASE = "UnquotedMixed"
WITH_DOTS = "unquoted.with.dots"


DATA = pd.DataFrame(
    {
        LOWER_CASE: [1, 2, 3],
        UPPER_CASE: [1, 2, 3],
        MIXED_CASE: [1, 2, 3],
        WITH_DOTS: [1, 2, 3],
    }
)

SUPPORTED_DATASOURCES = [
    ds for ds in SQL_DATA_SOURCES if not isinstance(ds, BigQueryDatasourceTestConfig)
]


@pytest.mark.parametrize(
    "col_name",
    [
        UPPER_CASE,
        LOWER_CASE,
        MIXED_CASE,
        WITH_DOTS,
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=SUPPORTED_DATASOURCES, data=DATA)
def test_specific_column_name_formats_work(batch_for_datasource: Batch, col_name: str) -> None:
    expectation = gxe.ExpectColumnValuesToBeBetween(column=col_name, min_value=0, max_value=10)
    result = batch_for_datasource.validate(expectation)
    assert result.success
