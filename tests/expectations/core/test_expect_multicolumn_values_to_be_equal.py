from typing import List

import pytest

import great_expectations.expectations as gxe
from great_expectations.expectations.expectation_configuration import ExpectationConfiguration
from great_expectations.render import RenderedStringTemplateContent

COLUMN_LIST = ["source", "copy"]


def _render_content(
    runtime_configuration: dict | None = None, **kwargs
) -> List[RenderedStringTemplateContent]:
    configuration = ExpectationConfiguration(
        type="expect_multicolumn_values_to_be_equal",
        kwargs={"column_list": COLUMN_LIST, **kwargs},
    )
    return gxe.ExpectMulticolumnValuesToBeEqual._prescriptive_renderer(
        configuration=configuration, runtime_configuration=runtime_configuration
    )


def _render(**kwargs) -> str:
    return _render_content(**kwargs)[0].string_template["template"]


@pytest.mark.unit
def test_prescriptive_renderer_renders_column_list():
    assert _render() == "Values across columns $column_list_0, $column_list_1 must be equal."


@pytest.mark.unit
def test_prescriptive_renderer_renders_mostly_below_one():
    assert _render(mostly=0.6) == (
        "Values across columns $column_list_0, $column_list_1 must be equal, "
        "at least $mostly_pct % of the time."
    )


@pytest.mark.unit
def test_prescriptive_renderer_omits_mostly_at_full_threshold():
    """A `mostly` of 1 adds nothing, and "at least 100 % of the time" would contradict the
    modern renderer, which drops the clause at that threshold."""
    assert _render(mostly=1.0) == (
        "Values across columns $column_list_0, $column_list_1 must be equal."
    )


@pytest.mark.unit
def test_prescriptive_renderer_renders_a_suite_parameter_for_mostly():
    """`mostly` may arrive as an unresolved suite parameter. It has no percentage to
    render, and the reader still needs to see which parameter supplied the threshold and
    what it resolved to."""
    content = _render_content(
        mostly={"$PARAMETER": "acceptable_match_rate"},
        runtime_configuration={"suite_parameters": {"acceptable_match_rate": 0.6}},
    )

    assert content[0].string_template["template"] == (
        "Values across columns $column_list_0, $column_list_1 must be equal."
    )
    assert content[1].string_template["params"] == {
        "eval_param": "acceptable_match_rate",
        "eval_param_value": 0.6,
    }


@pytest.mark.unit
def test_prescriptive_renderer_prefixes_row_condition():
    """A row condition restricts which rows were checked, so a rendered description that
    omits it overstates what the Expectation covered."""
    content = _render_content(row_condition='col_region=="EU"', condition_parser="pandas")

    assert content[0].string_template["template"] == (
        "If $condition_content, then values across columns "
        "$column_list_0, $column_list_1 must be equal."
    )
    # `parse_row_condition_string` quotes the condition for display.
    assert content[0].string_template["params"]["condition_content"] == "'col_region==\"EU\"'"
