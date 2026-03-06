import datetime
import uuid

import pytest
from freezegun import freeze_time

from great_expectations.core import ExpectationSuiteValidationResult
from great_expectations.data_context.store import ValidationResultsStore
from great_expectations.data_context.types.resource_identifiers import (
    ExpectationSuiteIdentifier,
    ValidationResultIdentifier,
)
from great_expectations.util import gen_directory_tree_str


@freeze_time("09/26/2019 13:42:41")
@pytest.mark.big
def test_ValidationResultsStore_with_InMemoryStoreBackend():
    my_store = ValidationResultsStore(
        store_backend={
            "module_name": "great_expectations.data_context.store",
            "class_name": "InMemoryStoreBackend",
        }
    )

    with pytest.raises(TypeError):
        my_store.get("not_a_ValidationResultIdentifier")

    ns_1 = ValidationResultIdentifier.from_tuple(
        (
            "a",
            "b",
            "c",
            "quarantine",
            datetime.datetime.now(datetime.timezone.utc),
            "prod-100",
        )
    )
    my_store.set(
        ns_1,
        ExpectationSuiteValidationResult(success=True, results=[], suite_name="a.b.c.quarantine"),
    )
    assert my_store.get(ns_1) == ExpectationSuiteValidationResult(
        success=True, statistics={}, results=[], suite_name="a.b.c.quarantine"
    )

    ns_2 = ValidationResultIdentifier.from_tuple(
        (
            "a",
            "b",
            "c",
            "quarantine",
            datetime.datetime.now(datetime.timezone.utc),
            "prod-200",
        )
    )
    my_store.set(
        ns_2,
        ExpectationSuiteValidationResult(success=False, results=[], suite_name="a.b.c.quarantine"),
    )
    assert my_store.get(ns_2) == ExpectationSuiteValidationResult(
        success=False, statistics={}, results=[], suite_name="a.b.c.quarantine"
    )
    assert set(my_store.list_keys()) == {
        ns_1,
        ns_2,
    }
    """
    What does this test and why?
    A Store should be able to report it's store_backend_id
    which is set when the StoreBackend is instantiated.
    """
    # Check that store_backend_id exists can be read
    assert my_store.store_backend_id is not None
    # Check that store_backend_id is a valid UUID
    assert isinstance(my_store.store_backend_id, uuid.UUID)


@pytest.mark.big
@freeze_time("09/26/2019 13:42:41")
@pytest.mark.filterwarnings(
    "ignore:String run_ids are deprecated*:DeprecationWarning:great_expectations.data_context.types.resource_identifiers"  # noqa: E501 # FIXME CoP
)
def test_ValidationResultsStore_with_TupleFileSystemStoreBackend(tmp_path_factory):
    full_test_dir = tmp_path_factory.mktemp(
        "test_ValidationResultStore_with_TupleFileSystemStoreBackend__dir"
    )
    test_dir = full_test_dir.parts[-1]
    path = str(full_test_dir)

    my_store = ValidationResultsStore(
        store_backend={
            "module_name": "great_expectations.data_context.store",
            "class_name": "TupleFilesystemStoreBackend",
            "base_directory": "my_store/",
        },
        runtime_environment={"root_directory": path},
    )

    with pytest.raises(TypeError):
        my_store.get("not_a_ValidationResultIdentifier")

    ns_1 = ValidationResultIdentifier(
        expectation_suite_identifier=ExpectationSuiteIdentifier("asset.quarantine"),
        run_id="prod-100",
        batch_identifier="batch_id",
    )
    my_store.set(
        ns_1,
        ExpectationSuiteValidationResult(success=True, results=[], suite_name="asset.quarantine"),
    )
    assert my_store.get(ns_1) == ExpectationSuiteValidationResult(
        success=True, statistics={}, results=[], suite_name="asset.quarantine"
    )

    ns_2 = ValidationResultIdentifier.from_tuple(
        (
            "asset",
            "quarantine",
            "prod-20",
            datetime.datetime.now(datetime.timezone.utc),
            "batch_id",
        )
    )
    my_store.set(
        ns_2,
        ExpectationSuiteValidationResult(success=False, results=[], suite_name="asset.quarantine"),
    )
    assert my_store.get(ns_2) == ExpectationSuiteValidationResult(
        success=False, statistics={}, results=[], suite_name="asset.quarantine"
    )

    assert set(my_store.list_keys()) == {
        ns_1,
        ns_2,
    }

    assert (
        gen_directory_tree_str(path)
        == f"""\
{test_dir}/
    my_store/
        .ge_store_backend_id
        asset/
            quarantine/
                prod-100/
                    20190926T134241.000000Z/
                        batch_id.json
                prod-20/
                    20190926T134241.000000Z/
                        batch_id.json
"""
    )

    """
    What does this test and why?
    A Store should be able to report it's store_backend_id
    which is set when the StoreBackend is instantiated.
    """
    # Check that store_backend_id exists can be read
    assert my_store.store_backend_id is not None
    # Check that store_backend_id is a valid UUID
    assert isinstance(my_store.store_backend_id, uuid.UUID)

    # Check that another store with the same configuration shares the same store_backend_id
    my_store_duplicate = ValidationResultsStore(
        store_backend={
            "module_name": "great_expectations.data_context.store",
            "class_name": "TupleFilesystemStoreBackend",
            "base_directory": "my_store/",
        },
        runtime_environment={"root_directory": path},
    )
    assert my_store.store_backend_id == my_store_duplicate.store_backend_id


@pytest.mark.cloud
def test_gx_cloud_response_json_to_object_dict() -> None:
    validation_id = "c1e8f964-ba44-4a13-a9b6-7331a358f12d"
    validation_definition = {
        "results": [],
        "success": True,
        "statistics": {
            "evaluated_expectations": 0,
            "successful_expectations": 0,
            "unsuccessful_expectations": 0,
            "success_percent": None,
        },
    }
    response_json = {
        "data": {
            "id": validation_id,
            "attributes": {
                "result": validation_definition,
            },
        }
    }

    expected = validation_definition
    expected["id"] = validation_id

    actual = ValidationResultsStore.gx_cloud_response_json_to_object_dict(response_json)

    assert actual == expected
