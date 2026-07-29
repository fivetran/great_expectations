import pandas as pd
import pytest

import great_expectations as gx
import great_expectations.expectations  # register expectation renderers
from great_expectations.expectations.expectation_configuration import (
    ExpectationConfiguration,
)
from great_expectations.expectations.registry import get_renderer_impl
from great_expectations.self_check.util import get_test_validator_with_data


@pytest.mark.unit
def test_unknown_method_raises() -> None:
    context = gx.get_context(mode="ephemeral")
    validator = get_test_validator_with_data(
        execution_engine="pandas",
        data=pd.DataFrame({"amount": [1, 2, 3]}),
        context=context,
    )

    with pytest.raises(
        NotImplementedError,
        match="method 'unknown' has not been implemented",
    ):
        validator.expect_column_values_to_not_be_outliers(
            column="amount",
            method="unknown",
            catch_exceptions=False,
        )


@pytest.mark.unit
@pytest.mark.parametrize(
    ("mostly", "expected_suffix"),
    [
        pytest.param(1.0, ".", id="all_values"),
        pytest.param(
            0.9,
            ", at least $mostly_pct % of the time.",
            id="mostly",
        ),
    ],
)
def test_prescriptive_renderer(mostly: float, expected_suffix: str) -> None:
    configuration = ExpectationConfiguration(
        type="expect_column_values_to_not_be_outliers",
        kwargs={
            "column": "amount",
            "method": "iqr",
            "multiplier": 1.5,
            "mostly": mostly,
        },
    )
    renderer = get_renderer_impl(
        object_name="expect_column_values_to_not_be_outliers",
        renderer_type="atomic.prescriptive.summary",
    )[1]

    rendered_content = renderer(configuration=configuration).to_json_dict()

    template = rendered_content["value"]["template"]
    assert template.startswith(
        "$column values must not be statistical outliers using the $method method "
        "with a multiplier of $multiplier"
    )
    assert template.endswith(expected_suffix)
