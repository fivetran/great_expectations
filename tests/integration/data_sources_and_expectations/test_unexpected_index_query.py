import re

import pandas as pd

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    SQL_DATA_SOURCES,
)

DATA = pd.DataFrame(
    {
        "id": [1, 2, 3, 4, 5, 6],
        "val": [3, 4, 5, 6, 7, None],
    }
)


@parameterize_batch_for_data_sources(data_source_configs=SQL_DATA_SOURCES, data=DATA)
def test_unexpected_index_query_compiles_parameters(
    batch_for_datasource: Batch,
) -> None:
    """
    Test that unexpected_index_query has compiled SQL parameters, not placeholders like :param_1.

    For ExpectColumnValuesToBeBetween with min_value=3 and max_value=5:
    - Expected: WHERE val IS NOT NULL AND NOT (val >= 3 AND val <= 5)
    - Bug: WHERE val IS NOT NULL AND NOT (val >= :param_1 AND val <= :param_2)
    """
    min_value = 3
    max_value = 5
    expectation = gxe.ExpectColumnValuesToBeBetween(
        column="val",
        min_value=min_value,
        max_value=max_value,
    )

    result = batch_for_datasource.validate(
        expectation,
        result_format={
            "result_format": "COMPLETE",
            "unexpected_index_column_names": ["id"],
        },
    )

    # The expectation should fail because values 6 and 7 are outside the range [3, 5]
    assert not result.success
    result_dict = result["result"]

    # Check that unexpected_index_query exists
    assert "unexpected_index_query" in result_dict
    unexpected_index_query = result_dict["unexpected_index_query"]

    # These assertions exist strictly to protect against regressions
    assert not re.search(r":param_\d+", unexpected_index_query), (
        f"Parameter placeholder (:param_N) was not compiled. Query: {unexpected_index_query}"
    )
    assert not re.search(r"%\(param_\d+\)s", unexpected_index_query), (
        f"Parameter placeholder (%(param_N)s) was not compiled. Query: {unexpected_index_query}"
    )
    # Note: We don't check for positional parameter "?" since it could appear in legitimate SQL

    # Verify the query contains the actual values
    assert str(min_value) in unexpected_index_query, (
        f"Value {min_value} not found in query: {unexpected_index_query}"
    )
    assert str(max_value) in unexpected_index_query, (
        f"Value {max_value} not found in query: {unexpected_index_query}"
    )
