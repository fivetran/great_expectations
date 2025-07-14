import logging
import re
from typing import TYPE_CHECKING, Iterator, List, cast
from unittest import mock

import pytest

from great_expectations.compatibility import google
from great_expectations.core import IDDict
from great_expectations.core.batch import LegacyBatchDefinition
from great_expectations.core.partitioners import FileNamePartitionerPath
from great_expectations.core.util import GCSUrl
from great_expectations.datasource.fluent import BatchRequest
from great_expectations.datasource.fluent.data_connector import (
    GoogleCloudStorageDataConnector,
)
from great_expectations.datasource.fluent.data_connector.file_path_data_connector import (
    MissingFilePathTemplateMapFnError,
)

if TYPE_CHECKING:
    from great_expectations.datasource.fluent.data_connector import (
        DataConnector,
    )


logger = logging.getLogger(__name__)


if not google.storage:
    pytest.skip(
        'Could not import "storage" from google.cloud in configured_asset_gcs_data_connector.py',
        allow_module_level=True,
    )


class MockGCSClient:
    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def list_blobs(
        self,
        bucket_or_name,
        max_results=None,
        prefix=None,
        delimiter=None,
        **kwargs,
    ) -> Iterator:
        return iter([])


@pytest.mark.big
@mock.patch(
    "great_expectations.datasource.fluent.data_asset.data_connector.google_cloud_storage_data_connector.list_gcs_keys"
)
def test_basic_instantiation(mock_list_keys):
    mock_list_keys.return_value = [
        "alpha-1.csv",
        "alpha-2.csv",
        "alpha-3.csv",
    ]

    gcs_client: google.Client = cast("google.Client", MockGCSClient())
    my_data_connector: DataConnector = GoogleCloudStorageDataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_google_cloud_storage_data_asset",
        batching_regex=re.compile(r"alpha-(.*)\.csv"),
        gcs_client=gcs_client,
        bucket_or_name="my_bucket",
        prefix="",
        file_path_template_map_fn=GCSUrl.OBJECT_URL_TEMPLATE.format,
    )
    assert my_data_connector.get_data_reference_count() == 3
    assert my_data_connector.get_data_references()[:3] == [
        "alpha-1.csv",
        "alpha-2.csv",
        "alpha-3.csv",
    ]
    assert my_data_connector.get_matched_data_reference_count() == 3
    assert my_data_connector.get_matched_data_references()[:3] == [
        "alpha-1.csv",
        "alpha-2.csv",
        "alpha-3.csv",
    ]
    assert my_data_connector.get_unmatched_data_references()[:3] == []
    assert my_data_connector.get_unmatched_data_reference_count() == 0


@pytest.mark.big
@mock.patch(
    "great_expectations.datasource.fluent.data_asset.data_connector.google_cloud_storage_data_connector.list_gcs_keys"
)
def test_instantiation_batching_regex_does_not_match_paths(mock_list_keys):
    mock_list_keys.return_value = [
        "alpha-1.csv",
        "alpha-2.csv",
        "alpha-3.csv",
    ]

    gcs_client: google.Client = cast("google.Client", MockGCSClient())
    my_data_connector: DataConnector = GoogleCloudStorageDataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_google_cloud_storage_data_asset",
        batching_regex=re.compile(r"(?P<name>.+)_(?P<timestamp>.+)_(?P<price>.*)\.csv"),
        gcs_client=gcs_client,
        bucket_or_name="my_bucket",
        prefix="",
        file_path_template_map_fn=GCSUrl.OBJECT_URL_TEMPLATE.format,
    )
    assert my_data_connector.get_data_reference_count() == 3
    assert my_data_connector.get_data_references()[:3] == [
        "alpha-1.csv",
        "alpha-2.csv",
        "alpha-3.csv",
    ]
    assert my_data_connector.get_matched_data_reference_count() == 0
    assert my_data_connector.get_matched_data_references()[:3] == []
    assert my_data_connector.get_unmatched_data_references()[:3] == [
        "alpha-1.csv",
        "alpha-2.csv",
        "alpha-3.csv",
    ]
    assert my_data_connector.get_unmatched_data_reference_count() == 3


@pytest.mark.big
@mock.patch(
    "great_expectations.datasource.fluent.data_asset.data_connector.google_cloud_storage_data_connector.list_gcs_keys"
)
def test_return_all_batch_definitions_unsorted(mock_list_keys):
    mock_list_keys.return_value = [
        "abe_20200809_1040.csv",
        "alex_20200809_1000.csv",
        "alex_20200819_1300.csv",
        "eugene_20200809_1500.csv",
        "eugene_20201129_1900.csv",
        "james_20200713_1567.csv",
        "james_20200810_1003.csv",
        "james_20200811_1009.csv",
        "will_20200809_1002.csv",
        "will_20200810_1001.csv",
    ]

    gcs_client: google.Client = cast("google.Client", MockGCSClient())
    my_data_connector: DataConnector = GoogleCloudStorageDataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_google_cloud_storage_data_asset",
        batching_regex=re.compile(r"(?P<name>.+)_(?P<timestamp>.+)_(?P<price>.*)\.csv"),
        gcs_client=gcs_client,
        bucket_or_name="my_bucket",
        prefix="",
        file_path_template_map_fn=GCSUrl.OBJECT_URL_TEMPLATE.format,
    )
    # with missing BatchRequest arguments
    with pytest.raises(TypeError):
        # noinspection PyArgumentList
        my_data_connector.get_batch_definition_list()

    # with empty options
    unsorted_batch_definition_list: List[LegacyBatchDefinition] = (
        my_data_connector.get_batch_definition_list(
            BatchRequest(
                datasource_name="my_file_path_datasource",
                data_asset_name="my_google_cloud_storage_data_asset",
                options={},
            )
        )
    )
    expected: List[LegacyBatchDefinition] = [
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_google_cloud_storage_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "abe_20200809_1040.csv",
                    "name": "abe",
                    "timestamp": "20200809",
                    "price": "1040",
                }
            ),
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_google_cloud_storage_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "alex_20200809_1000.csv",
                    "name": "alex",
                    "timestamp": "20200809",
                    "price": "1000",
                }
            ),
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_google_cloud_storage_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "alex_20200819_1300.csv",
                    "name": "alex",
                    "timestamp": "20200819",
                    "price": "1300",
                }
            ),
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_google_cloud_storage_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "eugene_20200809_1500.csv",
                    "name": "eugene",
                    "timestamp": "20200809",
                    "price": "1500",
                }
            ),
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_google_cloud_storage_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "eugene_20201129_1900.csv",
                    "name": "eugene",
                    "timestamp": "20201129",
                    "price": "1900",
                }
            ),
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_google_cloud_storage_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "james_20200713_1567.csv",
                    "name": "james",
                    "timestamp": "20200713",
                    "price": "1567",
                }
            ),
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_google_cloud_storage_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "james_20200810_1003.csv",
                    "name": "james",
                    "timestamp": "20200810",
                    "price": "1003",
                }
            ),
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_google_cloud_storage_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "james_20200811_1009.csv",
                    "name": "james",
                    "timestamp": "20200811",
                    "price": "1009",
                }
            ),
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_google_cloud_storage_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "will_20200809_1002.csv",
                    "name": "will",
                    "timestamp": "20200809",
                    "price": "1002",
                }
            ),
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_google_cloud_storage_data_asset",
            batch_identifiers=IDDict(
                {
                    "path": "will_20200810_1001.csv",
                    "name": "will",
                    "timestamp": "20200810",
                    "price": "1001",
                }
            ),
        ),
    ]
    assert expected == unsorted_batch_definition_list

    # with specified Batch query options
    unsorted_batch_definition_list = my_data_connector.get_batch_definition_list(
        BatchRequest(
            datasource_name="my_file_path_datasource",
            data_asset_name="my_google_cloud_storage_data_asset",
            options={"name": "alex", "timestamp": "20200819", "price": "1300"},
        )
    )
    assert expected[2:3] == unsorted_batch_definition_list


@pytest.mark.big
@mock.patch(
    "great_expectations.datasource.fluent.data_asset.data_connector.google_cloud_storage_data_connector.list_gcs_keys"
)
def test_return_only_unique_batch_definitions(mock_list_keys):
    mock_list_keys.return_value = [
        "A/file_1.csv",
        "A/file_2.csv",
        "A/file_3.csv",
    ]

    gcs_client: google.Client = cast("google.Client", MockGCSClient())

    my_data_connector: DataConnector

    my_data_connector = GoogleCloudStorageDataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_google_cloud_storage_data_asset",
        batching_regex=re.compile(r"(?P<name>.+).*\.csv"),
        gcs_client=gcs_client,
        bucket_or_name="my_bucket",
        prefix="A",
        file_path_template_map_fn=GCSUrl.OBJECT_URL_TEMPLATE.format,
    )
    assert my_data_connector.get_data_reference_count() == 3
    assert my_data_connector.get_data_references()[:3] == [
        "A/file_1.csv",
        "A/file_2.csv",
        "A/file_3.csv",
    ]
    assert my_data_connector.get_matched_data_reference_count() == 3
    assert my_data_connector.get_matched_data_references()[:3] == [
        "A/file_1.csv",
        "A/file_2.csv",
        "A/file_3.csv",
    ]
    assert my_data_connector.get_unmatched_data_references()[:3] == []
    assert my_data_connector.get_unmatched_data_reference_count() == 0

    mock_list_keys.return_value = [
        "B/file_1.csv",
        "B/file_2.csv",
    ]

    expected: List[LegacyBatchDefinition] = [
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_google_cloud_storage_data_asset",
            batch_identifiers=IDDict({"path": "B/file_1.csv", "filename": "file_1"}),
        ),
        LegacyBatchDefinition(
            datasource_name="my_file_path_datasource",
            data_connector_name="fluent",
            data_asset_name="my_google_cloud_storage_data_asset",
            batch_identifiers=IDDict({"path": "B/file_2.csv", "filename": "file_2"}),
        ),
    ]

    my_data_connector = GoogleCloudStorageDataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_google_cloud_storage_data_asset",
        batching_regex=re.compile(r"(?P<filename>.+).*\.csv"),
        gcs_client=gcs_client,
        bucket_or_name="my_bucket",
        prefix="B",
        file_path_template_map_fn=GCSUrl.OBJECT_URL_TEMPLATE.format,
    )

    unsorted_batch_definition_list: List[LegacyBatchDefinition] = (
        my_data_connector.get_batch_definition_list(
            BatchRequest(
                datasource_name="my_file_path_datasource",
                data_asset_name="my_google_cloud_storage_data_asset",
                options={},
            )
        )
    )
    assert expected == unsorted_batch_definition_list


@pytest.mark.big
@mock.patch(
    "great_expectations.datasource.fluent.data_asset.data_connector.google_cloud_storage_data_connector.list_gcs_keys"
)
def test_alpha(mock_list_keys):
    mock_list_keys.return_value = [
        "test_dir_alpha/A.csv",
        "test_dir_alpha/B.csv",
        "test_dir_alpha/C.csv",
        "test_dir_alpha/D.csv",
    ]

    gcs_client: google.Client = cast("google.Client", MockGCSClient())
    my_data_connector: DataConnector = GoogleCloudStorageDataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_google_cloud_storage_data_asset",
        batching_regex=re.compile(r"(?P<part_1>.*)\.csv"),
        gcs_client=gcs_client,
        bucket_or_name="my_bucket",
        prefix="test_dir_alpha",
        file_path_template_map_fn=GCSUrl.OBJECT_URL_TEMPLATE.format,
    )
    assert my_data_connector.get_data_reference_count() == 4
    assert my_data_connector.get_data_references()[:3] == [
        "test_dir_alpha/A.csv",
        "test_dir_alpha/B.csv",
        "test_dir_alpha/C.csv",
    ]
    assert my_data_connector.get_matched_data_reference_count() == 4
    assert my_data_connector.get_matched_data_references()[:3] == [
        "test_dir_alpha/A.csv",
        "test_dir_alpha/B.csv",
        "test_dir_alpha/C.csv",
    ]
    assert my_data_connector.get_unmatched_data_references()[:3] == []
    assert my_data_connector.get_unmatched_data_reference_count() == 0

    my_batch_definition_list: List[LegacyBatchDefinition]
    my_batch_definition: LegacyBatchDefinition

    my_batch_request: BatchRequest

    # Try to fetch a batch from a nonexistent asset
    my_batch_request = BatchRequest(datasource_name="BASE", data_asset_name="A", options={})
    my_batch_definition_list = my_data_connector.get_batch_definition_list(
        batch_request=my_batch_request
    )
    assert len(my_batch_definition_list) == 0

    my_batch_request = BatchRequest(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_google_cloud_storage_data_asset",
        options={"part_1": "B"},
    )
    my_batch_definition_list = my_data_connector.get_batch_definition_list(
        batch_request=my_batch_request
    )
    assert len(my_batch_definition_list) == 1


@pytest.mark.big
@mock.patch(
    "great_expectations.datasource.fluent.data_asset.data_connector.google_cloud_storage_data_connector.list_gcs_keys"
)
def test_foxtrot(mock_list_keys):
    mock_list_keys.return_value = []

    gcs_client: google.Client = cast("google.Client", MockGCSClient())

    my_data_connector: DataConnector

    my_data_connector = GoogleCloudStorageDataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_google_cloud_storage_data_asset",
        batching_regex=re.compile(r"(?P<part_1>.+)-(?P<part_2>.*)\.csv"),
        gcs_client=gcs_client,
        bucket_or_name="my_bucket",
        prefix="",
        file_path_template_map_fn=GCSUrl.OBJECT_URL_TEMPLATE.format,
    )
    assert my_data_connector.get_data_reference_count() == 0
    assert my_data_connector.get_data_references()[:3] == []
    assert my_data_connector.get_matched_data_reference_count() == 0
    assert my_data_connector.get_matched_data_references()[:3] == []
    assert my_data_connector.get_unmatched_data_references()[:3] == []
    assert my_data_connector.get_unmatched_data_reference_count() == 0

    mock_list_keys.return_value = [
        "test_dir_foxtrot/A/A-1.csv",
        "test_dir_foxtrot/A/A-2.csv",
        "test_dir_foxtrot/A/A-3.csv",
    ]

    my_data_connector = GoogleCloudStorageDataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_google_cloud_storage_data_asset",
        batching_regex=re.compile(r"(?P<part_1>.+)-(?P<part_2>.*)\.csv"),
        gcs_client=gcs_client,
        bucket_or_name="my_bucket",
        prefix="test_dir_foxtrot/A",
        file_path_template_map_fn=GCSUrl.OBJECT_URL_TEMPLATE.format,
    )

    assert my_data_connector.get_data_reference_count() == 3
    assert my_data_connector.get_data_references()[:3] == [
        "test_dir_foxtrot/A/A-1.csv",
        "test_dir_foxtrot/A/A-2.csv",
        "test_dir_foxtrot/A/A-3.csv",
    ]
    assert my_data_connector.get_matched_data_reference_count() == 3
    assert my_data_connector.get_matched_data_references()[:3] == [
        "test_dir_foxtrot/A/A-1.csv",
        "test_dir_foxtrot/A/A-2.csv",
        "test_dir_foxtrot/A/A-3.csv",
    ]
    assert my_data_connector.get_unmatched_data_references()[:3] == []
    assert my_data_connector.get_unmatched_data_reference_count() == 0

    mock_list_keys.return_value = [
        "test_dir_foxtrot/B/B-1.txt",
        "test_dir_foxtrot/B/B-2.txt",
        "test_dir_foxtrot/B/B-3.txt",
    ]

    my_data_connector = GoogleCloudStorageDataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_google_cloud_storage_data_asset",
        batching_regex=re.compile(r"(?P<part_1>.+)-(?P<part_2>.*)\.txt"),
        gcs_client=gcs_client,
        bucket_or_name="my_bucket",
        prefix="test_dir_foxtrot/B",
        file_path_template_map_fn=GCSUrl.OBJECT_URL_TEMPLATE.format,
    )

    mock_list_keys.return_value = [
        "test_dir_foxtrot/B/B-1.txt",
        "test_dir_foxtrot/B/B-2.txt",
        "test_dir_foxtrot/B/B-3.txt",
    ]

    assert my_data_connector.get_data_reference_count() == 3
    assert my_data_connector.get_data_references()[:3] == [
        "test_dir_foxtrot/B/B-1.txt",
        "test_dir_foxtrot/B/B-2.txt",
        "test_dir_foxtrot/B/B-3.txt",
    ]
    assert my_data_connector.get_matched_data_reference_count() == 3
    assert my_data_connector.get_matched_data_references()[:3] == [
        "test_dir_foxtrot/B/B-1.txt",
        "test_dir_foxtrot/B/B-2.txt",
        "test_dir_foxtrot/B/B-3.txt",
    ]
    assert my_data_connector.get_unmatched_data_references()[:3] == []
    assert my_data_connector.get_unmatched_data_reference_count() == 0

    my_data_connector = GoogleCloudStorageDataConnector(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_google_cloud_storage_data_asset",
        batching_regex=re.compile(r"(?P<part_1>.+)-(?P<part_2>.*)\.csv"),
        gcs_client=gcs_client,
        bucket_or_name="my_bucket",
        prefix="test_dir_foxtrot/C",
        file_path_template_map_fn=GCSUrl.OBJECT_URL_TEMPLATE.format,
    )

    mock_list_keys.return_value = [
        "test_dir_foxtrot/C/C-2017.csv",
        "test_dir_foxtrot/C/C-2018.csv",
        "test_dir_foxtrot/C/C-2019.csv",
    ]

    assert my_data_connector.get_data_reference_count() == 3
    assert my_data_connector.get_data_references()[:3] == [
        "test_dir_foxtrot/C/C-2017.csv",
        "test_dir_foxtrot/C/C-2018.csv",
        "test_dir_foxtrot/C/C-2019.csv",
    ]
    assert my_data_connector.get_matched_data_reference_count() == 3
    assert my_data_connector.get_matched_data_references()[:3] == [
        "test_dir_foxtrot/C/C-2017.csv",
        "test_dir_foxtrot/C/C-2018.csv",
        "test_dir_foxtrot/C/C-2019.csv",
    ]
    assert my_data_connector.get_unmatched_data_references()[:3] == []
    assert my_data_connector.get_unmatched_data_reference_count() == 0

    my_batch_request = BatchRequest(
        datasource_name="my_file_path_datasource",
        data_asset_name="my_google_cloud_storage_data_asset",
        options={},
    )
    my_batch_definition_list: List[LegacyBatchDefinition] = (
        my_data_connector.get_batch_definition_list(batch_request=my_batch_request)
    )
    assert len(my_batch_definition_list) == 3


@pytest.mark.unit
@pytest.mark.parametrize(
    "whole_directory_override, expected_batch_count, expected_identifier_key",
    [
        pytest.param(
            True, 1, "path", id="with_whole_directory_override_returns_single_directory_batch"
        ),
        pytest.param(
            False,
            3,
            "filename",
            id="without_whole_directory_override_returns_individual_file_batches",
        ),
    ],
)
def test_gcs_data_connector_whole_directory_path_override(
    whole_directory_override, expected_batch_count, expected_identifier_key, mocker
):
    """Test GoogleCloudStorageDataConnector with whole_directory_path_override parameter."""
    # Setup
    bucket_name = "test-bucket"
    prefix = "test_directory/"
    whole_directory_path = f"gs://{bucket_name}/{prefix}"

    # Mock GCS client
    mock_gcs_client = mocker.Mock()
    mock_bucket = mocker.Mock()
    mock_gcs_client.bucket.return_value = mock_bucket

    # Create mock blobs for file mode testing
    mock_blobs = []
    test_files = [
        "test_directory/file1.csv",
        "test_directory/file2.csv",
        "test_directory/file3.csv",
    ]

    for file_path in test_files:
        mock_blob = mocker.Mock()
        mock_blob.name = file_path
        mock_blobs.append(mock_blob)

    mock_bucket.list_blobs.return_value = mock_blobs

    # Create data connector with conditional whole_directory_path_override
    data_connector = GoogleCloudStorageDataConnector(
        datasource_name="my_gcs_datasource",
        data_asset_name="my_data_asset",
        gcs_client=mock_gcs_client,
        bucket_or_name=bucket_name,
        prefix=prefix,
        file_path_template_map_fn=lambda bucket_or_name, path: f"gs://{bucket_or_name}/{path}",
        whole_directory_path_override=whole_directory_path if whole_directory_override else None,
    )

    # Create batch request with conditional partitioner
    batch_request = BatchRequest(
        datasource_name="my_gcs_datasource",
        data_asset_name="my_data_asset",
        options={},
        partitioner=None
        if whole_directory_override
        else FileNamePartitionerPath(regex=re.compile(r"(?P<filename>.+\.csv)")),
    )
    batch_definitions = data_connector.get_batch_definition_list(batch_request)

    # Verify expected batch count
    assert len(batch_definitions) == expected_batch_count

    # Verify batch definitions have correct structure
    for batch_definition in batch_definitions:
        assert batch_definition.datasource_name == "my_gcs_datasource"
        assert batch_definition.data_asset_name == "my_data_asset"
        assert expected_identifier_key in batch_definition.batch_identifiers

    if whole_directory_override:
        # For directory mode, verify single batch with directory path
        batch_definition = batch_definitions[0]
        assert batch_definition.batch_identifiers["path"] == whole_directory_path
    else:
        # For file mode, verify individual file batches
        file_names = [bd.batch_identifiers["filename"] for bd in batch_definitions]
        expected_files = ["file1.csv", "file2.csv", "file3.csv"]
        assert sorted(file_names) == sorted(expected_files)


@pytest.mark.unit
def test_gcs_data_connector_missing_file_path_template_map_fn_error():
    """Test GCS data connector raises error when file_path_template_map_fn is None."""
    gcs_client: google.Client = MockGCSClient()

    data_connector = GoogleCloudStorageDataConnector(
        datasource_name="my_gcs_datasource",
        data_asset_name="my_data_asset",
        gcs_client=gcs_client,
        bucket_or_name="test-bucket",
        prefix="test/",
        file_path_template_map_fn=None,
    )

    with pytest.raises(MissingFilePathTemplateMapFnError):
        data_connector._get_full_file_path("test.csv")
