import pytest

from great_expectations.render.renderer.observed_value_renderer import (
    ObservedValueRenderState,
    get_list_comparison_obs_val,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "description, expected, actual, expected_result",
    [
        (
            "happy",
            ["a", "b", "c"],
            ["a", "b", "c"],
            [
                ("a", ObservedValueRenderState.expected),
                ("b", ObservedValueRenderState.expected),
                ("c", ObservedValueRenderState.expected),
            ],
        ),
        (
            "transposed chars",
            ["a", "b", "c", "d"],
            ["a", "c", "b", "d"],
            [
                ("a", ObservedValueRenderState.expected),
                ("c", ObservedValueRenderState.unexpected),
                ("b", ObservedValueRenderState.unexpected),
                ("d", ObservedValueRenderState.expected),
            ],
        ),
        (
            "renamed",
            ["a", "b", "c"],
            ["a", "c", "b2"],
            [
                ("a", ObservedValueRenderState.expected),
                ("b", ObservedValueRenderState.missing),
                ("c", ObservedValueRenderState.expected),
                ("b2", ObservedValueRenderState.unexpected),
            ],
        ),
        (
            "pair transposed",
            ["a", "b"],
            ["b", "a"],
            [
                ("b", ObservedValueRenderState.unexpected),
                ("a", ObservedValueRenderState.unexpected),
            ],
        ),
        (
            "pair first index missing",
            ["a", "b"],
            ["x", "a"],
            [
                ("x", ObservedValueRenderState.unexpected),
                ("b", ObservedValueRenderState.missing),
                ("a", ObservedValueRenderState.expected),
            ],
        ),
        (
            "pair second index missing",
            ["a", "b"],
            ["a", "x"],
            [
                ("a", ObservedValueRenderState.expected),
                ("b", ObservedValueRenderState.missing),
                ("x", ObservedValueRenderState.unexpected),
            ],
        ),
        (
            "empty actual",
            ["a", "b"],
            [],
            [("a", ObservedValueRenderState.missing), ("b", ObservedValueRenderState.missing)],
        ),
        (
            "one column deleted",
            ["a", "b", "c"],
            ["a", "c"],
            [
                ("a", ObservedValueRenderState.expected),
                ("b", ObservedValueRenderState.missing),
                ("c", ObservedValueRenderState.expected),
            ],
        ),
        (
            "last column deleted",
            ["a", "b", "c", "d"],
            ["a", "b", "c"],
            [
                ("a", ObservedValueRenderState.expected),
                ("b", ObservedValueRenderState.expected),
                ("c", ObservedValueRenderState.expected),
                ("d", ObservedValueRenderState.missing),
            ],
        ),
        (
            "empty expected",
            [],
            ["a", "b"],
            [
                ("a", ObservedValueRenderState.unexpected),
                ("b", ObservedValueRenderState.unexpected),
            ],
        ),
        (
            "one column added",
            ["a", "b"],
            ["a", "b", "c"],
            [
                ("a", ObservedValueRenderState.expected),
                ("b", ObservedValueRenderState.expected),
                ("c", ObservedValueRenderState.unexpected),
            ],
        ),
        (
            "mix 1",
            ["f", "a", "b", "c", "d"],
            ["a", "b", "c"],
            [
                ("f", ObservedValueRenderState.missing),
                ("a", ObservedValueRenderState.expected),
                ("b", ObservedValueRenderState.expected),
                ("c", ObservedValueRenderState.expected),
                ("d", ObservedValueRenderState.missing),
            ],
        ),
        (
            "mix 2",
            ["a", "b", "c", "d"],
            ["a", "c", "d", "b", "e"],
            [
                ("a", ObservedValueRenderState.expected),
                ("c", ObservedValueRenderState.unexpected),
                ("d", ObservedValueRenderState.unexpected),
                ("b", ObservedValueRenderState.unexpected),
                ("e", ObservedValueRenderState.unexpected),
            ],
        ),
    ],
)
def test_get_list_comparison_obs_val(description, expected, actual, expected_result):
    # arrange
    ...

    # act
    res = get_list_comparison_obs_val(expected, actual)

    # assert
    assert res == expected_result
