import pandas as pd
import pytest

from great_expectations.data_context.data_context.abstract_data_context import AbstractDataContext
from great_expectations.expectations.core.expect_column_values_to_not_be_null import (
    ExpectColumnValuesToNotBeNull,
)


@pytest.mark.unit
def test_expect_column_values_to_not_be_null_includes_unexpected_index_column_names(
    empty_data_context: AbstractDataContext,
):
    """
    Validate that when `unexpected_index_column_names` is provided in result_format,
    the ExpectColumnValuesToNotBeNull result includes it in the final output.
    """

    # Create sample dataframe with one null email
    df = pd.DataFrame(
        {
            "customer_id": [1001, 1002, 1003, 1004, 1005],
            "email": ["a@x.com", "b@x.com", "c@x.com", "d@x.com", None],
        }
    )

    data_asset = empty_data_context.data_sources.pandas_default.add_dataframe_asset("my_dataframe")
    batch = data_asset.add_batch_definition_whole_dataframe("whole_df").get_batch(
        batch_parameters={"dataframe": df}
    )

    result = batch.validate(
        ExpectColumnValuesToNotBeNull(column="email"),
        result_format={
            "result_format": "COMPLETE",
            "unexpected_index_column_names": ["customer_id"],
        },
    )

    assert not result.success

    assert "unexpected_index_column_names" in result.result
    assert result.result["unexpected_index_column_names"] == ["customer_id"]
