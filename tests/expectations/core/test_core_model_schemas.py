import json
from pathlib import Path

import jsonschema
import pytest
from jsonschema import Draft7Validator
from tasks import _emit_expectation_catalog_index

from great_expectations.expectations import core
from great_expectations.expectations.core import schemas
from great_expectations.expectations.expectation import MetaExpectation
from great_expectations.expectations.registry import _registered_expectations, get_expectation_impl

expectation_dictionary = dict(core.__dict__)

_INDEX_PATH = Path(schemas.__file__).parent / "index.json"


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
    # `index.json` is a generated catalog derived from these per-class schemas, not a
    # schema for a class itself, so it has no corresponding entry in `all_models`.
    schema_file_paths = (
        path for path in Path(schemas.__file__).parent.glob("*.json") if path.stem != "index"
    )
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
    # `index.json` is a generated catalog, not itself a JSON Schema document, so it's
    # exempt from JSON Schema spec validation.
    schema_file_paths = (
        path for path in Path(schemas.__file__).parent.glob("*.json") if path.stem != "index"
    )
    for file_path in schema_file_paths:
        with open(file_path) as schema_file:
            try:
                safer_draft_7_validator.check_schema(json.load(schema_file))
            except jsonschema.exceptions.SchemaError as e:
                raise AssertionError(
                    f"Invalid json schema for `{file_path.name}`: {e.message}"
                ) from e


@pytest.mark.unit
def test_expectation_catalog_index_matches_generator():
    """The checked-in expectation catalog index must equal what regenerating it produces.

    The index is derived data, not hand-maintained - anything that changes its inputs
    (an expectation's curated metadata, or the set of expectations it covers) without
    also regenerating it will drift silently for any consumer that trusts the checked-in
    file. Regenerate with `invoke schemas --sync`.
    """
    regenerated = _emit_expectation_catalog_index(indent=4)
    checked_in = _INDEX_PATH.read_text()
    # Both sides are ~30KB of generated JSON text, so an `assert regenerated == checked_in`
    # here would let pytest's assertion rewriter emit a multi-thousand-line character diff
    # that buries the one line a contributor actually needs. Byte equality is still the
    # detection mechanism - only the reporting path changes.
    if regenerated != checked_in:
        pytest.fail(
            "expectations/core/schemas/index.json is out of date, run `invoke schemas --sync`",
            pytrace=False,
        )


@pytest.mark.unit
def test_registered_expectations_are_indexed_or_documented_absent():
    """Every registered expectation must be either cataloged or explicitly recorded as absent.

    An expectation that is neither would be invisible to anything that enumerates GX's
    capabilities from the catalog - it would appear to not exist at all, rather than
    being a documented gap.

    `_registered_expectations` is process-global mutable state: any `Expectation`
    subclass anywhere - including ones defined in other test modules purely as fixtures
    or probes - registers itself via `MetaExpectation` the instant its module is
    imported, and pytest imports every collected test module during collection, before
    any test (and any marker-based deselection) runs. Comparing the catalog against the
    raw registry therefore makes this test's outcome depend on which other test modules
    happened to be collected in the same process, rather than on whether GX's own
    catalog is complete. Restrict the comparison to expectations whose implementation
    actually lives under the `great_expectations` package - that's what the catalog is
    describing - so a test-only expectation registered incidentally during collection
    can never trip this assertion. Do not remove this filter as a "simplification"; doing
    so reintroduces collection-order-dependent failures.

    The trailing dot in the prefix is load-bearing: sibling distributions install under
    names like `great_expectations_experimental`, which a dotless prefix would admit.
    """
    catalog = json.loads(_INDEX_PATH.read_text())
    indexed = set(catalog["expectations"])
    documented_absent = set(catalog["documented_absent"])
    shipped = {
        name
        for name in _registered_expectations
        if get_expectation_impl(name).__module__.startswith("great_expectations.")
    }

    missing = shipped - (indexed | documented_absent)
    assert not missing, (
        "The following registered expectations are neither cataloged in index.json nor "
        f"recorded as documented-absent: {sorted(missing)}. Run `invoke schemas --sync`, "
        "or add them to the documented-absence list if the omission is deliberate."
    )


@pytest.mark.unit
def test_expectation_catalog_index_and_documented_absent_are_disjoint():
    """An expectation must not be both cataloged and recorded as documented-absent.

    If it were both, a stale absence entry could sit alongside a real catalog entry
    indefinitely - the completeness check alone can't tell that case apart from a correct
    one, since the union of the two sets would still cover every registered expectation.
    """
    catalog = json.loads(_INDEX_PATH.read_text())
    indexed = set(catalog["expectations"])
    documented_absent = set(catalog["documented_absent"])

    overlap = indexed & documented_absent
    assert not overlap, (
        "The following expectations appear both in the catalog and in the "
        f"documented-absence list: {sorted(overlap)}. An expectation with real catalog "
        "metadata is not absent - drop it from the documented-absence list."
    )
