import pytest

from great_expectations.core.expectation_validation_result import (
    ExpectationValidationResult,
)
from great_expectations.expectations.expectation_configuration import (
    ExpectationConfiguration,
)
from great_expectations.render.renderer.renderer import Renderer


@pytest.mark.unit
def test__find_evr_by_type(titanic_profiled_evrs_1):
    # TODO: _find_all_evrs_by_type should accept an ValidationResultSuite, not ValidationResultSuite.results  # noqa: E501 # FIXME CoP
    found_evr = Renderer()._find_evr_by_type(
        titanic_profiled_evrs_1.results, "expect_column_to_exist"
    )
    print(found_evr)
    assert found_evr is None

    # TODO: _find_all_evrs_by_type should accept an ValidationResultSuite, not ValidationResultSuite.results  # noqa: E501 # FIXME CoP
    found_evr = Renderer()._find_evr_by_type(
        titanic_profiled_evrs_1.results, "expect_column_distinct_values_to_be_in_set"
    )
    print(found_evr)
    assert found_evr == ExpectationValidationResult(
        success=True,
        result={
            "observed_value": ["*", "1st", "2nd", "3rd"],
            "element_count": 1313,
            "missing_count": 0,
            "missing_percent": 0.0,
            "details": {
                "value_counts": [
                    {"value": "*", "count": 1},
                    {"value": "1st", "count": 322},
                    {"value": "2nd", "count": 279},
                    {"value": "3rd", "count": 711},
                ]
            },
        },
        exception_info={
            "raised_exception": False,
            "exception_message": None,
            "exception_traceback": None,
        },
        expectation_config=ExpectationConfiguration(
            type="expect_column_distinct_values_to_be_in_set",
            kwargs={"column": "PClass", "value_set": ["a", "b", "c"], "result_format": "SUMMARY"},
        ),
    )


@pytest.mark.unit
def test__find_all_evrs_by_type(titanic_profiled_evrs_1):
    # TODO: _find_all_evrs_by_type should accept an ValidationResultSuite, not ValidationResultSuite.results  # noqa: E501 # FIXME CoP
    found_evrs = Renderer()._find_all_evrs_by_type(
        titanic_profiled_evrs_1.results, "expect_column_to_exist", column_=None
    )
    print(found_evrs)
    assert found_evrs == []

    # TODO: _find_all_evrs_by_type should accept an ValidationResultSuite, not ValidationResultSuite.results  # noqa: E501 # FIXME CoP
    found_evrs = Renderer()._find_all_evrs_by_type(
        titanic_profiled_evrs_1.results, "expect_column_to_exist", column_="SexCode"
    )
    print(found_evrs)
    assert found_evrs == []

    # TODO: _find_all_evrs_by_type should accept an ValidationResultSuite, not ValidationResultSuite.results  # noqa: E501 # FIXME CoP
    found_evrs = Renderer()._find_all_evrs_by_type(
        titanic_profiled_evrs_1.results,
        "expect_column_distinct_values_to_be_in_set",
        column_=None,
    )
    print(found_evrs)
    assert len(found_evrs) == 4

    # TODO: _find_all_evrs_by_type should accept an ValidationResultSuite, not ValidationResultSuite.results  # noqa: E501 # FIXME CoP
    found_evrs = Renderer()._find_all_evrs_by_type(
        titanic_profiled_evrs_1.results,
        "expect_column_distinct_values_to_be_in_set",
        column_="SexCode",
    )
    print(found_evrs)
    assert len(found_evrs) == 1


@pytest.mark.unit
def test__get_column_list_from_evrs(titanic_profiled_evrs_1):
    column_list = Renderer()._get_column_list_from_evrs(titanic_profiled_evrs_1)
    print(column_list)
    assert column_list == [
        "Unnamed: 0",
        "Name",
        "PClass",
        "Age",
        "Sex",
        "Survived",
        "SexCode",
    ]


@pytest.mark.unit
def test_renderer_hash_consistency_with_equality():
    renderer1 = Renderer()
    renderer2 = Renderer()

    assert renderer1 == renderer2
    assert hash(renderer1) == hash(renderer2)


@pytest.mark.unit
def test_renderer_hash_different_for_different_types():
    class TestRenderer(Renderer):
        pass

    renderer1 = Renderer()
    renderer2 = TestRenderer()

    assert renderer1 != renderer2
    assert hash(renderer1) != hash(renderer2)


@pytest.mark.unit
def test_renderer_hash_stable_across_runs():
    renderer = Renderer()

    hash1 = hash(renderer)
    hash2 = hash(renderer)
    hash3 = hash(renderer)

    assert hash1 == hash2 == hash3
