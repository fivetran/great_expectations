import json
import pathlib

import pytest

import great_expectations.expectations as gxe
from great_expectations.expectations.conditions import AndCondition, Column, OrCondition
from great_expectations.expectations.expectation_configuration import ExpectationConfiguration
from great_expectations.render.renderer.content_block.bullet_list_content_block import (
    ExpectationSuiteBulletListContentBlockRenderer,
)
from great_expectations.render.util import (
    parse_row_condition_string,
    parse_row_condition_string_pandas_engine,
    substitute_none_for_missing,
)


@pytest.mark.unit
def test_substitute_none_for_missing():
    assert substitute_none_for_missing(kwargs={"a": 1, "b": 2}, kwarg_list=["c", "d"]) == {
        "a": 1,
        "b": 2,
        "c": None,
        "d": None,
    }

    my_kwargs = {"a": 1, "b": 2}
    assert substitute_none_for_missing(kwargs=my_kwargs, kwarg_list=["c", "d"]) == {
        "a": 1,
        "b": 2,
        "c": None,
        "d": None,
    }
    assert my_kwargs == {
        "a": 1,
        "b": 2,
    }, "substitute_none_for_missing should not change input kwargs in place."


@pytest.mark.unit
def test_parse_row_condition_string_pandas_engine():
    test_condition_string = ""
    assert parse_row_condition_string_pandas_engine(test_condition_string) == (
        "if $row_condition__0",
        {"row_condition__0": "True"},
    )

    test_condition_string = "Age in [0, 42]"
    assert parse_row_condition_string_pandas_engine(test_condition_string) == (
        "if $row_condition__0",
        {"row_condition__0": "Age in [0, 42]"},
    )

    test_condition_string = (
        "Survived == 1 and (SexCode not in (0, 7, x) | ~(Age > 50)) & not (PClass != '1st')"
    )
    assert parse_row_condition_string_pandas_engine(test_condition_string) == (
        "if $row_condition__0 and ($row_condition__1 or not ($row_condition__2)) and not ($row_condition__3)",  # noqa: E501 # FIXME CoP
        {
            "row_condition__0": "Survived == 1",
            "row_condition__1": "SexCode not in [0, 7, x]",
            "row_condition__2": "Age > 50",
            "row_condition__3": "PClass != '1st'",
        },
    )


@pytest.mark.filesystem
def test_expectations_using_expectation_definitions():
    dir_path = pathlib.Path(__file__).parent
    data_path = dir_path / "BulletListContentBlock.json"
    with open(data_path) as f:
        test_data = json.load(f)

    for expectation_dict in test_data:
        fake_expectation = ExpectationConfiguration(**expectation_dict)
        render_result = ExpectationSuiteBulletListContentBlockRenderer.render([fake_expectation])
        assert render_result is not None
        render_result = render_result.to_json_dict()
        assert isinstance(render_result, dict)
        assert "content_block_type" in render_result
        assert render_result["content_block_type"] in render_result
        assert isinstance(render_result[render_result["content_block_type"]], list)


# A row condition restricts which rows were checked, so Data Docs must show it as the author wrote
# it. Each case pairs a condition with the text the reader should see.
_ROW_CONDITION_DISPLAY_CASES = [
    pytest.param(
        lambda: Column("end_date") > Column("start_date"),
        "end_date > start_date",
        id="column_comparison_standalone",
    ),
    pytest.param(
        lambda: AndCondition(
            conditions=[Column("end_date") > Column("start_date"), Column("status") == "open"]
        ),
        "(end_date > start_date AND status == open)",
        id="column_comparison_in_and_group",
    ),
    pytest.param(
        lambda: OrCondition(
            conditions=[Column("end_date") > Column("start_date"), Column("status") == "open"]
        ),
        "(end_date > start_date OR status == open)",
        id="column_comparison_in_or_group",
    ),
    pytest.param(
        lambda: Column("end_date") >= Column("start_date"),
        "end_date >= start_date",
        id="column_comparison_inclusive_operator",
    ),
    pytest.param(
        lambda: Column("status") == "open",
        "status == open",
        id="literal_comparison_standalone",
    ),
    pytest.param(
        lambda: AndCondition(
            conditions=[Column("status") == "open", Column("amount") > 0],
        ),
        "(status == open AND amount > 0)",
        id="literal_comparison_in_and_group",
    ),
]


@pytest.mark.unit
@pytest.mark.parametrize(("build_condition", "expected_text"), _ROW_CONDITION_DISPLAY_CASES)
def test_parse_row_condition_string_shows_condition_as_written(build_condition, expected_text):
    condition = build_condition()

    assert parse_row_condition_string(condition) == expected_text
    # A saved suite stores the condition as a dict, which is the form Data Docs receive.
    assert parse_row_condition_string(condition.dict()) == expected_text


@pytest.mark.unit
@pytest.mark.parametrize(("build_condition", "expected_text"), _ROW_CONDITION_DISPLAY_CASES)
def test_prescriptive_content_block_badge_shows_condition_as_written(
    build_condition, expected_text
):
    expectation = gxe.ExpectColumnValuesToBeBetween(
        column="amount", min_value=0, row_condition=build_condition()
    )

    render_result = ExpectationSuiteBulletListContentBlockRenderer.render(
        [expectation.configuration]
    ).to_json_dict()

    string_template = render_result["bullet_list"][0]["string_template"]
    assert string_template["template"] == (
        "If $condition_content, then $column values must be greater than or equal to $min_value."
    )
    assert string_template["params"]["condition_content"] == expected_text
    assert "badge" in string_template["styling"]["params"]["condition_content"]["classes"]
