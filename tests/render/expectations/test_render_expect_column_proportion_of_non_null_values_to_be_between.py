import pytest

from great_expectations import expectations as gxe
from great_expectations.render import (
    RenderedAtomicContent,
    RenderedAtomicValue,
)
from great_expectations.render.renderer.inline_renderer import InlineRenderer


@pytest.mark.parametrize(
    "expectation,expected_expectation_configuration_rendered_atomic_content",
    [
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
                column="test_column",
            ),
            [
                RenderedAtomicContent(
                    name="atomic.prescriptive.summary",
                    value=RenderedAtomicValue(
                        template="$column may have any proportion of non-null values.",
                        params={
                            "column": {
                                "schema": {"type": "string"},
                                "value": "test_column",
                            }
                        },
                        schema={"type": "com.superconductive.rendered.string"},
                    ),
                    value_type="StringValueType",
                ),
            ],
            id="no_min_max_values",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
                column="test_column",
                min_value=0.5,
                max_value=0.8,
            ),
            [
                RenderedAtomicContent(
                    name="atomic.prescriptive.summary",
                    value=RenderedAtomicValue(
                        template=(
                            "$column proportion of non-null values must be greater "
                            "than or equal to $min_value and less than or equal to $max_value."
                        ),
                        params={
                            "column": {
                                "schema": {"type": "string"},
                                "value": "test_column",
                            },
                            "min_value": {
                                "schema": {"type": "number"},
                                "value": 0.5,
                            },
                            "max_value": {
                                "schema": {"type": "number"},
                                "value": 0.8,
                            },
                        },
                        schema={"type": "com.superconductive.rendered.string"},
                    ),
                    value_type="StringValueType",
                ),
            ],
            id="min_and_max_values",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
                column="test_column",
                max_value=0.8,
            ),
            [
                RenderedAtomicContent(
                    name="atomic.prescriptive.summary",
                    value=RenderedAtomicValue(
                        template=(
                            "$column proportion of non-null values must be less than or equal to "
                            "$max_value."
                        ),
                        params={
                            "column": {
                                "schema": {"type": "string"},
                                "value": "test_column",
                            },
                            "max_value": {
                                "schema": {"type": "number"},
                                "value": 0.8,
                            },
                        },
                        schema={"type": "com.superconductive.rendered.string"},
                    ),
                    value_type="StringValueType",
                ),
            ],
            id="only_max_value",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
                column="test_column",
                min_value=0.5,
            ),
            [
                RenderedAtomicContent(
                    name="atomic.prescriptive.summary",
                    value=RenderedAtomicValue(
                        template=(
                            "$column proportion of non-null values must be greater "
                            "than or equal to $min_value."
                        ),
                        params={
                            "column": {
                                "schema": {"type": "string"},
                                "value": "test_column",
                            },
                            "min_value": {
                                "schema": {"type": "number"},
                                "value": 0.5,
                            },
                        },
                        schema={"type": "com.superconductive.rendered.string"},
                    ),
                    value_type="StringValueType",
                ),
            ],
            id="only_min_value",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
                column="test_column",
                min_value=0.7,
                max_value=0.7,
            ),
            [
                RenderedAtomicContent(
                    name="atomic.prescriptive.summary",
                    value=RenderedAtomicValue(
                        template="$column proportion of non-null values "
                        "must be exactly $min_value.",
                        params={
                            "column": {
                                "schema": {"type": "string"},
                                "value": "test_column",
                            },
                            "min_value": {
                                "schema": {"type": "number"},
                                "value": 0.7,
                            },
                            "max_value": {
                                "schema": {"type": "number"},
                                "value": 0.7,
                            },
                        },
                        schema={"type": "com.superconductive.rendered.string"},
                    ),
                    value_type="StringValueType",
                ),
            ],
            id="equal_min_max_values",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
                column="test_column",
                min_value=0.5,
                max_value=0.8,
                strict_min=True,
            ),
            [
                RenderedAtomicContent(
                    name="atomic.prescriptive.summary",
                    value=RenderedAtomicValue(
                        template=(
                            "$column proportion of non-null values must be greater than $min_value "
                            "and less than or equal to $max_value."
                        ),
                        params={
                            "column": {
                                "schema": {"type": "string"},
                                "value": "test_column",
                            },
                            "min_value": {
                                "schema": {"type": "number"},
                                "value": 0.5,
                            },
                            "max_value": {
                                "schema": {"type": "number"},
                                "value": 0.8,
                            },
                            "strict_min": {
                                "schema": {"type": "boolean"},
                                "value": True,
                            },
                        },
                        schema={"type": "com.superconductive.rendered.string"},
                    ),
                    value_type="StringValueType",
                ),
            ],
            id="strict_min_condition",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
                column="test_column",
                min_value=0.5,
                max_value=0.8,
                strict_max=True,
            ),
            [
                RenderedAtomicContent(
                    name="atomic.prescriptive.summary",
                    value=RenderedAtomicValue(
                        template=(
                            "$column proportion of non-null values must be greater "
                            "than or equal to $min_value and less than $max_value."
                        ),
                        params={
                            "column": {
                                "schema": {"type": "string"},
                                "value": "test_column",
                            },
                            "min_value": {
                                "schema": {"type": "number"},
                                "value": 0.5,
                            },
                            "max_value": {
                                "schema": {"type": "number"},
                                "value": 0.8,
                            },
                            "strict_max": {
                                "schema": {"type": "boolean"},
                                "value": True,
                            },
                        },
                        schema={"type": "com.superconductive.rendered.string"},
                    ),
                    value_type="StringValueType",
                ),
            ],
            id="strict_max_condition",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
                column="test_column",
                min_value=0.5,
                max_value=0.8,
                strict_min=True,
                strict_max=True,
            ),
            [
                RenderedAtomicContent(
                    name="atomic.prescriptive.summary",
                    value=RenderedAtomicValue(
                        template=(
                            "$column proportion of non-null values must be greater than $min_value "
                            "and less than $max_value."
                        ),
                        params={
                            "column": {
                                "schema": {"type": "string"},
                                "value": "test_column",
                            },
                            "min_value": {
                                "schema": {"type": "number"},
                                "value": 0.5,
                            },
                            "max_value": {
                                "schema": {"type": "number"},
                                "value": 0.8,
                            },
                            "strict_min": {
                                "schema": {"type": "boolean"},
                                "value": True,
                            },
                            "strict_max": {
                                "schema": {"type": "boolean"},
                                "value": True,
                            },
                        },
                        schema={"type": "com.superconductive.rendered.string"},
                    ),
                    value_type="StringValueType",
                ),
            ],
            id="both_strict_conditions",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
                column="test_column",
                min_value=0.5,
                strict_min=True,
            ),
            [
                RenderedAtomicContent(
                    name="atomic.prescriptive.summary",
                    value=RenderedAtomicValue(
                        template=(
                            "$column proportion of non-null values must be greater than $min_value."
                        ),
                        params={
                            "column": {
                                "schema": {"type": "string"},
                                "value": "test_column",
                            },
                            "min_value": {
                                "schema": {"type": "number"},
                                "value": 0.5,
                            },
                            "strict_min": {
                                "schema": {"type": "boolean"},
                                "value": True,
                            },
                        },
                        schema={"type": "com.superconductive.rendered.string"},
                    ),
                    value_type="StringValueType",
                ),
            ],
            id="only_min_value_strict",
        ),
        pytest.param(
            gxe.ExpectColumnProportionOfNonNullValuesToBeBetween(
                column="test_column",
                max_value=0.8,
                strict_max=True,
            ),
            [
                RenderedAtomicContent(
                    name="atomic.prescriptive.summary",
                    value=RenderedAtomicValue(
                        template=(
                            "$column proportion of non-null values must be less than $max_value."
                        ),
                        params={
                            "column": {
                                "schema": {"type": "string"},
                                "value": "test_column",
                            },
                            "max_value": {
                                "schema": {"type": "number"},
                                "value": 0.8,
                            },
                            "strict_max": {
                                "schema": {"type": "boolean"},
                                "value": True,
                            },
                        },
                        schema={"type": "com.superconductive.rendered.string"},
                    ),
                    value_type="StringValueType",
                ),
            ],
            id="only_max_value_strict",
        ),
    ],
)
@pytest.mark.unit
def test_expectation_configuration_rendered_atomic_content(
    expectation: gxe.ExpectColumnProportionOfNonNullValuesToBeBetween,
    expected_expectation_configuration_rendered_atomic_content: list[RenderedAtomicContent],
):
    inline_renderer: InlineRenderer = InlineRenderer(render_object=expectation.configuration)

    actual_expectation_configuration_rendered_atomic_content: list[RenderedAtomicContent] = (
        inline_renderer.get_rendered_content()
    )

    assert len(actual_expectation_configuration_rendered_atomic_content) == 1

    assert (
        expected_expectation_configuration_rendered_atomic_content
        == actual_expectation_configuration_rendered_atomic_content
    )
