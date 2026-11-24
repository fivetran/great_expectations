"""Legacy descriptive renderers must show a real zero, not '--'."""

import pytest

from great_expectations.core.expectation_validation_result import ExpectationValidationResult
from great_expectations.expectations.core.expect_column_proportion_of_non_null_values_to_be_between import (
    ExpectColumnProportionOfNonNullValuesToBeBetween,
)
from great_expectations.expectations.core.expect_column_proportion_of_unique_values_to_be_between import (
    ExpectColumnProportionOfUniqueValuesToBeBetween,
)
from great_expectations.expectations.core.expect_column_unique_value_count_to_be_between import (
    ExpectColumnUniqueValueCountToBeBetween,
)


def _render(expectation_cls, observed_value):
    result = ExpectationValidationResult(
        success=True,
        result={"observed_value": observed_value},
        exception_info={
            "raised_exception": False,
            "exception_message": None,
            "exception_traceback": None,
        },
    )
    renderer = getattr(
        expectation_cls,
        "_descriptive_column_properties_table_distinct_count_row_renderer",
        None,
    ) or getattr(
        expectation_cls,
        "_descriptive_column_properties_table_distinct_percent_row_renderer",
    )
    blocks = renderer(configuration=None, result=result)
    return [getattr(block, "value", block) for block in blocks][-1]


@pytest.mark.unit
@pytest.mark.parametrize(
    "expectation_cls,observed_value,expected",
    [
        (ExpectColumnProportionOfNonNullValuesToBeBetween, 0.0, "0.0%"),
        (ExpectColumnProportionOfUniqueValuesToBeBetween, 0, "0.0%"),
        (ExpectColumnUniqueValueCountToBeBetween, 0, 0),
    ],
)
def test_descriptive_renderer__observed_zero__shows_zero(
    expectation_cls, observed_value, expected
):
    assert _render(expectation_cls, observed_value) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "expectation_cls",
    [
        ExpectColumnProportionOfNonNullValuesToBeBetween,
        ExpectColumnProportionOfUniqueValuesToBeBetween,
        ExpectColumnUniqueValueCountToBeBetween,
    ],
)
def test_descriptive_renderer__observed_none__shows_placeholder(expectation_cls):
    assert _render(expectation_cls, None) == "--"
