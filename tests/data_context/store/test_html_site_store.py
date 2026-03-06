import datetime

import pytest
from freezegun import freeze_time
from marshmallow import ValidationError

from great_expectations.data_context.store import HtmlSiteStore
from great_expectations.data_context.types.resource_identifiers import (
    SiteSectionIdentifier,
    ValidationResultIdentifier,
    validationResultIdentifierSchema,
)
from great_expectations.util import gen_directory_tree_str


@pytest.mark.filesystem
@freeze_time("09/26/2019 13:42:41")
def test_HtmlSiteStore_filesystem_backend(tmp_path_factory):
    full_test_dir = tmp_path_factory.mktemp(
        "test_HtmlSiteStore_with_TupleFileSystemStoreBackend__dir"
    )
    test_dir = full_test_dir.parts[-1]
    path = str(full_test_dir)

    my_store = HtmlSiteStore(
        store_backend={
            "class_name": "TupleFilesystemStoreBackend",
            "base_directory": "my_store",
        },
        runtime_environment={"root_directory": path},
    )

    with pytest.raises(TypeError):
        my_store.get("not_a_ValidationResultIdentifier")

    with pytest.raises(ValidationError):
        my_store.get(validationResultIdentifierSchema.load({}))

    ns_1 = SiteSectionIdentifier(
        site_section_name="validations",
        resource_identifier=ValidationResultIdentifier.from_tuple(
            (
                "a",
                "b",
                "c",
                "quarantine",
                datetime.datetime.now(datetime.timezone.utc),
                "prod-100",
            )
        ),
    )
    my_store.set(ns_1, "aaa")

    ns_2 = SiteSectionIdentifier(
        site_section_name="validations",
        resource_identifier=ValidationResultIdentifier.from_tuple(
            (
                "a",
                "b",
                "c",
                "quarantine",
                datetime.datetime.now(datetime.timezone.utc),
                "prod-20",
            )
        ),
    )
    my_store.set(ns_2, "bbb")

    # WARNING: OBSERVE THAT SITE_SECTION_NAME IS LOST IN THE CALL TO LIST_KEYS
    assert set(my_store.list_keys()) == {
        ns_1.resource_identifier,
        ns_2.resource_identifier,
    }

    assert (
        gen_directory_tree_str(path)
        == f"""\
{test_dir}/
    my_store/
        validations/
            a/
                b/
                    c/
                        quarantine/
                            20190926T134241.000000Z/
                                prod-100.html
                                prod-20.html
"""
    )
