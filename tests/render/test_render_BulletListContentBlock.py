import json
import pathlib

import pytest

from great_expectations.expectations.expectation_configuration import ExpectationConfiguration
from great_expectations.render.renderer.content_block.bullet_list_content_block import (
    ExpectationSuiteBulletListContentBlockRenderer,
)
from great_expectations.render.util import (
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
