import copy
from typing import Dict, Final, Optional

import pytest

from great_expectations.data_context.data_context.serializable_data_context import (
    SerializableDataContext,
)
from great_expectations.data_context.types.base import (
    BaseStoreBackendDefaults,
    DataContextConfig,
    DataContextConfigDefaults,
    DataContextConfigSchema,
    FilesystemStoreBackendDefaults,
    InMemoryStoreBackendDefaults,
)
from great_expectations.util import filter_properties_dict

"""
What does this test and why?

This file will hold various tests to ensure that the UI functions as expected when creating a DataContextConfig object. It will ensure that the appropriate defaults are used, including when the store_backend_defaults parameter is set.
"""  # noqa: E501 # FIXME CoP

_DEFAULT_CONFIG_VERSION: Final[float] = float(
    DataContextConfigDefaults.DEFAULT_CONFIG_VERSION.value
)


@pytest.fixture(scope="function")
def construct_data_context_config():
    """
    Construct a DataContextConfig fixture given the modifications in the input parameters
    Returns:
        Dictionary representation of a DataContextConfig to compare in tests
    """

    def _construct_data_context_config(
        data_context_id: str,
        config_version: float = _DEFAULT_CONFIG_VERSION,
        expectations_store_name: str = DataContextConfigDefaults.DEFAULT_EXPECTATIONS_STORE_NAME.value,  # noqa: E501 # FIXME CoP
        validation_results_store_name: str = DataContextConfigDefaults.DEFAULT_VALIDATIONS_STORE_NAME.value,  # noqa: E501 # FIXME CoP
        checkpoint_store_name: str = DataContextConfigDefaults.DEFAULT_CHECKPOINT_STORE_NAME.value,
        fluent_datasources: Optional[Dict] = None,
        plugins_directory: Optional[str] = None,
        stores: Optional[Dict] = None,
        data_docs_sites: Optional[Dict] = None,
    ):
        if stores is None:
            stores = copy.deepcopy(DataContextConfigDefaults.DEFAULT_STORES.value)
        if data_docs_sites is None:
            data_docs_sites = copy.deepcopy(DataContextConfigDefaults.DEFAULT_DATA_DOCS_SITES.value)

        return {
            "config_version": config_version,
            "expectations_store_name": expectations_store_name,
            "fluent_datasources": fluent_datasources,
            "validation_results_store_name": validation_results_store_name,
            "checkpoint_store_name": checkpoint_store_name,
            "plugins_directory": plugins_directory,
            "stores": stores,
            "data_docs_sites": data_docs_sites,
            "config_variables_file_path": None,
            "data_context_id": data_context_id,
        }

    return _construct_data_context_config


@pytest.mark.unit
def test_DataContextConfig_with_BaseStoreBackendDefaults_and_simple_defaults(
    construct_data_context_config,
):
    """
    What does this test and why?
    Ensure that a very simple DataContextConfig setup with many defaults is created accurately
    and produces a valid DataContextConfig
    """

    store_backend_defaults = BaseStoreBackendDefaults()
    data_context_config = DataContextConfig(
        store_backend_defaults=store_backend_defaults,
        checkpoint_store_name=store_backend_defaults.checkpoint_store_name,
    )

    desired_config = construct_data_context_config(
        data_context_id=data_context_config.data_context_id,
    )

    data_context_config_schema = DataContextConfigSchema()
    assert filter_properties_dict(
        properties=data_context_config_schema.dump(data_context_config),
        clean_falsy=True,
    ) == filter_properties_dict(
        properties=desired_config,
        clean_falsy=True,
    )
    assert isinstance(
        SerializableDataContext.get_or_create_data_context_config(
            project_config=data_context_config
        ),
        DataContextConfig,
    )


@pytest.mark.unit
def test_DataContextConfig_with_FilesystemStoreBackendDefaults_and_simple_defaults(
    construct_data_context_config,
):
    """
    What does this test and why?
    Ensure that a very simple DataContextConfig setup using FilesystemStoreBackendDefaults is created accurately
    This test sets the root_dir parameter
    """  # noqa: E501 # FIXME CoP

    test_root_directory = "test_root_dir"

    store_backend_defaults = FilesystemStoreBackendDefaults(root_directory=test_root_directory)
    data_context_config = DataContextConfig(
        store_backend_defaults=store_backend_defaults,
    )

    # Create desired config
    data_context_id = data_context_config.data_context_id
    desired_config = construct_data_context_config(data_context_id=data_context_id)
    # Add root_directory to stores and data_docs
    desired_config["stores"][desired_config["expectations_store_name"]]["store_backend"][
        "root_directory"
    ] = test_root_directory
    desired_config["stores"][desired_config["validation_results_store_name"]]["store_backend"][
        "root_directory"
    ] = test_root_directory
    desired_config["stores"][desired_config["checkpoint_store_name"]]["store_backend"][
        "root_directory"
    ] = test_root_directory
    desired_config["data_docs_sites"]["local_site"]["store_backend"]["root_directory"] = (
        test_root_directory
    )

    desired_config["stores"]["validation_definition_store"]["store_backend"]["root_directory"] = (
        test_root_directory
    )

    data_context_config_schema = DataContextConfigSchema()
    assert filter_properties_dict(
        properties=data_context_config_schema.dump(data_context_config),
        clean_falsy=True,
    ) == filter_properties_dict(
        properties=desired_config,
        clean_falsy=True,
    )
    assert isinstance(
        SerializableDataContext.get_or_create_data_context_config(
            project_config=data_context_config
        ),
        DataContextConfig,
    )


@pytest.mark.unit
def test_DataContextConfig_with_FilesystemStoreBackendDefaults_and_simple_defaults_no_root_directory(  # noqa: E501 # FIXME CoP
    construct_data_context_config,
):
    """
    What does this test and why?
    Ensure that a very simple DataContextConfig setup using FilesystemStoreBackendDefaults is created accurately
    This test does not set the optional root_directory parameter
    """  # noqa: E501 # FIXME CoP

    store_backend_defaults = FilesystemStoreBackendDefaults()
    data_context_config = DataContextConfig(
        store_backend_defaults=store_backend_defaults,
        checkpoint_store_name=store_backend_defaults.checkpoint_store_name,
    )

    # Create desired config
    data_context_id = data_context_config.data_context_id
    desired_config = construct_data_context_config(data_context_id=data_context_id)

    data_context_config_schema = DataContextConfigSchema()
    assert filter_properties_dict(
        properties=data_context_config_schema.dump(data_context_config),
        clean_falsy=True,
    ) == filter_properties_dict(
        properties=desired_config,
        clean_falsy=True,
    )
    assert isinstance(
        SerializableDataContext.get_or_create_data_context_config(
            project_config=data_context_config
        ),
        DataContextConfig,
    )


@pytest.mark.unit
def test_DataContextConfig_with_InMemoryStoreBackendDefaults(
    construct_data_context_config,
):
    store_backend_defaults = InMemoryStoreBackendDefaults()
    data_context_config = DataContextConfig(
        store_backend_defaults=store_backend_defaults,
    )

    desired_config = {
        "data_context_id": data_context_config.data_context_id,
        "checkpoint_store_name": "checkpoint_store",
        "config_version": 4.0,
        "expectations_store_name": "expectations_store",
        "stores": {
            "checkpoint_store": {
                "class_name": "CheckpointStore",
                "store_backend": {"class_name": "InMemoryStoreBackend"},
            },
            "expectations_store": {
                "class_name": "ExpectationsStore",
                "store_backend": {"class_name": "InMemoryStoreBackend"},
            },
            "validation_results_store": {
                "class_name": "ValidationResultsStore",
                "store_backend": {"class_name": "InMemoryStoreBackend"},
            },
            "validation_definition_store": {
                "class_name": "ValidationDefinitionStore",
                "store_backend": {"class_name": "InMemoryStoreBackend"},
            },
        },
        "validation_results_store_name": "validation_results_store",
    }

    data_context_config_schema = DataContextConfigSchema()
    assert filter_properties_dict(
        properties=data_context_config_schema.dump(data_context_config),
        clean_falsy=True,
    ) == filter_properties_dict(
        properties=desired_config,
        clean_falsy=True,
    )
    assert isinstance(
        SerializableDataContext.get_or_create_data_context_config(
            project_config=data_context_config
        ),
        DataContextConfig,
    )


@pytest.mark.unit
def test_data_context_config_defaults():
    config = DataContextConfig()
    assert config.to_json_dict() == {
        "analytics_enabled": None,
        "data_context_id": None,
        "checkpoint_store_name": None,
        "config_variables_file_path": None,
        "config_version": 4,
        "data_docs_sites": None,
        "expectations_store_name": None,
        "fluent_datasources": {},
        "plugins_directory": None,
        "progress_bars": None,
        "stores": DataContextConfigDefaults.DEFAULT_STORES.value,
        "validation_results_store_name": None,
    }
