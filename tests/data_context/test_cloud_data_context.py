import uuid
from typing import Any, Dict

import pytest
import responses

from great_expectations.data_context.data_context.cloud_data_context import CloudDataContext

CLOUD_BASE_URL = "https://api.greatexpectations.io/fake"
ACCESS_TOKEN = "my-secret-access-token"
ORG_ID = str(uuid.uuid4())
WORKSPACE_ID = str(uuid.uuid4())
CONTEXT_CONFIGURATION_URL = (
    f"{CLOUD_BASE_URL}/api/v1/organizations/{ORG_ID}"
    f"/workspaces/{WORKSPACE_ID}/data-context-configuration"
)


def _create_cloud_config_response(
    expectation_suite_store_name_key: str,
    validation_results_store_name_key: str,
    validation_results_store_class_name: str,
) -> Dict[str, Any]:
    return {
        "anonymous_usage_statistics": {
            "data_context_id": "6a52bdfa-e182-455b-a825-e69f076e67d6",
            "enabled": True,
        },
        "checkpoint_store_name": "default_checkpoint_store",
        "config_variables_file_path": "uncommitted/config_variables.yml",
        "config_version": 3.0,
        "data_docs_sites": {},
        expectation_suite_store_name_key: "suite_parameter_store",
        "expectations_store_name": "default_expectations_store",
        "plugins_directory": "plugins/",
        "progress_bars": {
            "globally": False,
            "metric_calculations": False,
            "profilers": False,
        },
        "stores": {
            "default_checkpoint_store": {
                "class_name": "CheckpointStore",
                "store_backend": {
                    "class_name": "GXCloudStoreBackend",
                    "ge_cloud_base_url": CLOUD_BASE_URL,
                    "ge_cloud_credentials": {
                        "access_token": ACCESS_TOKEN,
                        "organization_id": ORG_ID,
                    },
                    "ge_cloud_resource_type": "checkpoint",
                    "suppress_store_backend_id": True,
                },
            },
            "default_expectations_store": {
                "class_name": "ExpectationsStore",
                "store_backend": {
                    "class_name": "GXCloudStoreBackend",
                    "ge_cloud_base_url": CLOUD_BASE_URL,
                    "ge_cloud_credentials": {
                        "access_token": ORG_ID,
                        "organization_id": ORG_ID,
                    },
                    "ge_cloud_resource_type": "expectation_suite",
                    "suppress_store_backend_id": True,
                },
            },
            "default_validation_results_store": {
                "class_name": validation_results_store_class_name,
                "store_backend": {
                    "class_name": "GXCloudStoreBackend",
                    "ge_cloud_base_url": CLOUD_BASE_URL,
                    "ge_cloud_credentials": {
                        "access_token": ACCESS_TOKEN,
                        "organization_id": ORG_ID,
                    },
                    "ge_cloud_resource_type": "validation_result",
                    "suppress_store_backend_id": True,
                },
            },
            "expectations_store": {
                "class_name": "ExpectationsStore",
                "store_backend": {
                    "base_directory": "expectations/",
                    "class_name": "TupleFilesystemStoreBackend",
                },
            },
        },
        validation_results_store_name_key: "default_validation_results_store",
    }


V0_CONFIG = _create_cloud_config_response(
    expectation_suite_store_name_key="evaluation_parameter_store_name",
    validation_results_store_name_key="validations_store_name",
    validation_results_store_class_name="ValidationsStore",
)

V1_CONFIG = _create_cloud_config_response(
    expectation_suite_store_name_key="suite_parameter_store_name",
    validation_results_store_name_key="validation_results_store_name",
    validation_results_store_class_name="ValidationResultsStore",
)


@pytest.mark.parametrize(
    ("config",),
    [
        (V0_CONFIG,),
        (V1_CONFIG,),
    ],
)
@responses.activate
@pytest.mark.unit
def test_parses_v0_config_from_cloud(config: dict):
    """
    Tests to ensure we can build a cloud data context from both v0 and v1 configurations.

    NOTE: This includes some assertions, but we are also just checking that no exceptions
    are raised when instantiating the CloudDataContext, as would happen if we didn't
    properly map keys from the v0 configuration to the v1 configuration.
    """

    responses.add(
        responses.GET,
        CONTEXT_CONFIGURATION_URL,
        json=config,
        status=200,
    )

    CloudDataContext(
        cloud_base_url=CLOUD_BASE_URL,
        cloud_access_token=ACCESS_TOKEN,
        cloud_organization_id=ORG_ID,
        cloud_workspace_id=WORKSPACE_ID,
    )

    # if we didn't raise when instantiating the context, we are good!


@responses.activate
@pytest.mark.unit
def test_warns_when_workspace_id_env_var_unset(unset_gx_env_variables: None):
    """
    Test that CloudDataContext warns when GX_CLOUD_WORKSPACE_ID environment variable is unset.

    This test verifies that the warning message starting with
    "Workspace id is not set when instantiating a CloudDataContext." is emitted
    when the workspace ID is not provided via environment variable or constructor parameter.
    """
    # Mock the accounts/me endpoint to return a user with exactly one workspace
    # This allows the context to be instantiated successfully after the warning
    accounts_me_response = {
        "user_id": str(uuid.uuid4()),
        "workspaces": [{"id": WORKSPACE_ID, "role": "admin"}],
    }

    responses.add(
        responses.GET,
        f"{CLOUD_BASE_URL}/organizations/{ORG_ID}/accounts/me",
        json=accounts_me_response,
        status=200,
    )

    # Mock the data context configuration endpoint
    responses.add(
        responses.GET,
        CONTEXT_CONFIGURATION_URL,
        json=V1_CONFIG,
        status=200,
    )

    # Capture warnings and instantiate CloudDataContext
    with pytest.warns(UserWarning) as warning_info:
        CloudDataContext(
            cloud_base_url=CLOUD_BASE_URL,
            cloud_access_token=ACCESS_TOKEN,
            cloud_organization_id=ORG_ID,
            # Note: cloud_workspace_id is intentionally NOT provided
        )

    # Verify the warning message
    assert len(warning_info) == 1
    warning_message = str(warning_info[0].message)
    assert warning_message.startswith(
        "Workspace id is not set when instantiating a CloudDataContext."
    )
    assert "GX_CLOUD_WORKSPACE_ID" in warning_message
