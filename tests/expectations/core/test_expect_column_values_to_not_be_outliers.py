import pandas as pd
import pytest

import great_expectations as gx
import great_expectations.expectations as gxe
from great_expectations.compatibility import pydantic
from great_expectations.expectations.expectation_configuration import (
    ExpectationConfiguration,
)
from great_expectations.expectations.metrics.column_aggregate_metrics.column_outlier_statistics import (  # noqa: E501
    validate_method,
)
from great_expectations.expectations.registry import get_renderer_impl


@pytest.mark.unit
@pytest.mark.parametrize(
    "method",
    ["unknown", "IQR", "stddev", "std_dev", "zscore"],
)
def test_unsupported_method_is_rejected_at_configuration_time(method: str) -> None:
    """An unsupported method must not survive into a stored suite to fail on every run."""
    with pytest.raises(pydantic.ValidationError, match="permitted: 'iqr', 'std'"):
        gxe.ExpectColumnValuesToNotBeOutliers(column="amount", method=method)


@pytest.mark.unit
def test_unsupported_method_from_a_suite_parameter_is_rejected() -> None:
    """A method resolved from a suite parameter is held to the same set of values."""
    context = gx.get_context(mode="ephemeral")
    batch = (
        context.data_sources.add_pandas(name="pandas")
        .add_dataframe_asset(name="amounts")
        .add_batch_definition_whole_dataframe("batch_definition")
        .get_batch(batch_parameters={"dataframe": pd.DataFrame({"amount": [1, 2, 3]})})
    )
    expectation = gxe.ExpectColumnValuesToNotBeOutliers(
        column="amount", method={"$PARAMETER": "chosen_method"}
    )

    with pytest.raises(pydantic.ValidationError, match="permitted: 'iqr', 'std'"):
        batch.validate(expectation, expectation_parameters={"chosen_method": "unknown"})


@pytest.mark.unit
def test_unsupported_method_raises_when_the_metric_is_resolved_directly() -> None:
    """The metric keeps its own guard for callers that bypass the Expectation."""
    with pytest.raises(NotImplementedError, match="method 'unknown' has not been implemented"):
        validate_method("unknown")


@pytest.mark.unit
def test_negative_multiplier_is_rejected_at_configuration_time() -> None:
    """A negative multiplier would silently report every row an outlier."""
    with pytest.raises(pydantic.ValidationError, match="greater than or equal to 0"):
        gxe.ExpectColumnValuesToNotBeOutliers(column="amount", multiplier=-1.5)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("mostly", "expected_template"),
    [
        pytest.param(
            1.0,
            "$column values must not be statistical outliers using the $method method "
            "with a multiplier of $multiplier.",
            id="all_values",
        ),
        pytest.param(
            0.9,
            "$column values must not be statistical outliers using the $method method "
            "with a multiplier of $multiplier, at least $mostly_pct % of the time.",
            id="mostly",
        ),
    ],
)
def test_prescriptive_renderer(mostly: float, expected_template: str) -> None:
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

    assert rendered_content["value"]["template"] == expected_template
