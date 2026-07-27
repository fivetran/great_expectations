import numpy as np

import great_expectations.expectations as gxe
from great_expectations.expectations.expectation_configuration import (
    ExpectationConfiguration,
)


def test_expectation_is_registered_and_constructible():
    expectation = gxe.ExpectColumnTypeToBe(column="col", type_="int64")
    assert expectation.column == "col"
    assert expectation.type_ == "int64"


def test_validate_pandas_success():
    expectation = gxe.ExpectColumnTypeToBe(column="col", type_="int64")
    result = expectation._validate_pandas(
        actual_column_type=np.dtype("int64"), expected_type="int64"
    )
    assert result == {"success": True, "result": {"observed_value": "int64"}}


def test_validate_pandas_failure_returns_schema_level_result():
    expectation = gxe.ExpectColumnTypeToBe(column="col", type_="int64")
    result = expectation._validate_pandas(
        actual_column_type=np.dtype("object"), expected_type="int64"
    )
    # Schema-level result shape (observed_value only) is preserved on failure,
    # with no row-level fields.
    assert result == {"success": False, "result": {"observed_value": "object_"}}


def test_validate_pandas_object_column_is_schema_level():
    # The core behavior: a pandas 'object' column reports its declared dtype and
    # is not checked row-by-row (unlike ExpectColumnValuesToBeOfType).
    expectation = gxe.ExpectColumnTypeToBe(column="col", type_="object")
    result = expectation._validate_pandas(
        actual_column_type=np.dtype("object"), expected_type="object"
    )
    assert result == {"success": True, "result": {"observed_value": "object_"}}


def test_prescriptive_renderer_template():
    configuration = ExpectationConfiguration(
        type="expect_column_type_to_be",
        kwargs={"column": "col", "type_": "int64"},
    )
    rendered = gxe.ExpectColumnTypeToBe._prescriptive_renderer(configuration=configuration)
    string_template = rendered[0].string_template
    assert string_template["template"] == "$column type must be $type_."
    assert string_template["params"]["column"] == "col"
    assert string_template["params"]["type_"] == "int64"
