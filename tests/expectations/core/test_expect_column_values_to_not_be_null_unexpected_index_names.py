import pandas as pd
import pytest

from great_expectations.self_check.util import build_pandas_validator_with_data


@pytest.mark.unit
@pytest.mark.pandas
def test_expect_column_values_to_not_be_null_includes_unexpected_index_column_names():
    # Data with one null email we can identify via customer_id
    df = pd.DataFrame(
        {
            "customer_id": [1001, 1002, 1003, 1004, 1005],
            "email": ["a@x.com", "b@x.com", "c@x.com", "d@x.com", None],
        }
    )

    validator = build_pandas_validator_with_data(
        df=df,
    )

    result = validator.expect_column_values_to_not_be_null(
        "email",
        result_format={
            "result_format": "COMPLETE",
            "unexpected_index_column_names": ["customer_id"],
        },
    )

    assert "unexpected_index_column_names" in result.result
    assert result.result["unexpected_index_column_names"] == ["customer_id"]
