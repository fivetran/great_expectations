"""Test that unexpected_index_query compiles SQL parameters correctly for all SQL dialects."""

import pandas as pd

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    SQL_DATA_SOURCES,
)

# Test data with a simple table that has an id column (for unexpected_index_column_names)
# and a val column that we'll test expectations against
DATA = pd.DataFrame(
    {
        "id": [1, 2, 3, 4, 5, 6],
        "val": [1, 2, 3, 6, 7, None],
    }
)


@parameterize_batch_for_data_sources(data_source_configs=SQL_DATA_SOURCES, data=DATA)
def test_unexpected_index_query_compiles_parameters_for_expect_column_values_to_be_between(
    batch_for_datasource: Batch,
) -> None:
    """
    Test that unexpected_index_query has compiled SQL parameters, not placeholders like :param_1.

    For ExpectColumnValuesToBeBetween with min_value=1 and max_value=5:
    - Expected: WHERE val IS NOT NULL AND NOT (val >= 1 AND val <= 5)
    - Bug: WHERE val IS NOT NULL AND NOT (val >= :param_1 AND val <= :param_2)
    """
    expectation = gxe.ExpectColumnValuesToBeBetween(
        column="val",
        min_value=1,
        max_value=5,
    )

    result = batch_for_datasource.validate(
        expectation,
        result_format={
            "result_format": "COMPLETE",
            "unexpected_index_column_names": ["id"],
        },
    )

    # The expectation should fail because values 6 and 7 are outside the range [1, 5]
    assert not result.success
    result_dict = result["result"]

    # Check that unexpected_index_query exists
    assert "unexpected_index_query" in result_dict
    unexpected_index_query = result_dict["unexpected_index_query"]

    assert ":param_1" not in unexpected_index_query, (
        f"SQL parameter :param_1 was not compiled. Query: {unexpected_index_query}"
    )
    assert ":param_2" not in unexpected_index_query, (
        f"SQL parameter :param_2 was not compiled. Query: {unexpected_index_query}"
    )

    # Verify the query contains the actual values 1 and 5
    assert "1" in unexpected_index_query, f"Value 1 not found in query: {unexpected_index_query}"
    assert "5" in unexpected_index_query, f"Value 5 not found in query: {unexpected_index_query}"
