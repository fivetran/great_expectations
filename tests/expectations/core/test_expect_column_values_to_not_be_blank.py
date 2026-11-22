import great_expectations as gx
import pandas as pd
import pytest


pytestmark = pytest.mark.unit


def validate_dataframe(dataframe, **expectation_kwargs):
    context = gx.get_context(mode="ephemeral")

    data_source = context.data_sources.add_pandas("test_source")
    asset = data_source.add_dataframe_asset("test_asset")

    batch = (
        asset.add_batch_definition_whole_dataframe("test_batch")
        .get_batch(batch_parameters={"dataframe": dataframe})
    )

    expectation = gx.expectations.ExpectColumnValuesToNotBeBlank(
        **expectation_kwargs
    )

    return batch.validate(expectation)


def test_passes_for_non_blank_and_non_string_values():
    dataframe = pd.DataFrame(
        {
            "value": ["Alice", " Bob ", 0, False, 3.14],
        }
    )

    result = validate_dataframe(dataframe, column="value")

    assert result.success
    assert result.result["unexpected_count"] == 0


def test_fails_for_null_empty_and_whitespace_values():
    dataframe = pd.DataFrame(
        {
            "value": ["Alice", None, "", "   ", "\t"],
        }
    )

    result = validate_dataframe(dataframe, column="value")

    assert not result.success
    assert result.result["unexpected_count"] == 4


def test_mostly_allows_some_blank_values():
    dataframe = pd.DataFrame(
        {
            "value": ["Alice", "", "Bob"],
        }
    )

    result = validate_dataframe(
        dataframe,
        column="value",
        mostly=0.66,
    )

    assert result.success
    assert result.result["unexpected_count"] == 1
