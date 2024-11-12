import json
from pathlib import Path

import jsonschema
import pytest
from jsonschema import Draft7Validator

from great_expectations.expectations import core
from great_expectations.expectations.core import schemas
from great_expectations.expectations.expectation import MetaExpectation

expectation_dictionary = dict(core.__dict__)


@pytest.fixture
def safer_draft_7_validator() -> type[Draft7Validator]:
    validator = Draft7Validator
    validator.META_SCHEMA = {
        **Draft7Validator.META_SCHEMA,
        # this ensures that only specified properties are used (e.g. multipleOf, not multiple_of)
        # otherwise, the spec says unspecified properties should be ignored
        "additionalProperties": False,
    }
    return validator


@pytest.mark.unit
def test_all_core_model_schemas_are_serializable():
    all_models = [
        expectation
        for expectation in expectation_dictionary.values()
        if isinstance(expectation, MetaExpectation)
    ]
    # are they still there?
    assert len(all_models) > 50
    for model in all_models:
        model.schema_json()


@pytest.mark.filesystem  # ~4s
def test_schemas_updated():
    all_models = {
        cls_name: expectation
        for cls_name, expectation in expectation_dictionary.items()
        if isinstance(expectation, MetaExpectation)
    }
    schema_file_paths = Path(schemas.__file__).parent.glob("*.json")
    all_schemas = {file_path.stem: file_path.read_text() for file_path in schema_file_paths}
    for cls_name, schema in all_schemas.items():
        # converting to dicts for easier comparision on failure
        new_schema = json.loads(all_models[cls_name].schema_json())
        old_schema = json.loads(schema)
        assert new_schema == old_schema, "json schemas not updated, run `invoke schemas --sync`"


@pytest.mark.unit
def test_schemas_valid_spec(safer_draft_7_validator: type[Draft7Validator]):
    # https://json-schema.org/draft-07
    # https://jsonforms.io/api/core/interfaces/jsonschema7
    schema_file_paths = Path(schemas.__file__).parent.glob("*.json")
    for file_path in schema_file_paths:
        with open(file_path) as schema_file:
            try:
                safer_draft_7_validator.check_schema(json.load(schema_file))
            except jsonschema.exceptions.SchemaError as e:
                raise AssertionError(
                    f"Invalid json schema for `{file_path.name}`: {e.message}"
                ) from e
