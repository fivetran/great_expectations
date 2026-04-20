import uuid
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

import pytest
import responses
from pytest_mock import MockerFixture

from great_expectations.core.batch_definition import BatchDefinition
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.core.validation_definition import ValidationDefinition
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


# ---------------------------------------------------------------------------
# prepare_checkpoint_run: batch_definition_id query param (GX-3229)
# ---------------------------------------------------------------------------


CHECKPOINT_ID = str(uuid.uuid4())
BATCH_DEFINITION_ID = str(uuid.uuid4())
# urljoin() with an absolute URL path replaces the base URL's path, so the
# resulting request goes to the host root, not to ``{CLOUD_BASE_URL}``.
EXPECTATION_PARAMETERS_URL = (
    "https://api.greatexpectations.io"
    f"/api/v1/organizations/{ORG_ID}"
    f"/workspaces/{WORKSPACE_ID}/checkpoints/{CHECKPOINT_ID}/expectation-parameters"
)


def _build_cloud_context() -> CloudDataContext:
    """Construct a CloudDataContext whose /data-context-configuration call is mocked."""
    responses.add(
        responses.GET,
        CONTEXT_CONFIGURATION_URL,
        json=V1_CONFIG,
        status=200,
    )
    return CloudDataContext(
        cloud_base_url=CLOUD_BASE_URL,
        cloud_access_token=ACCESS_TOKEN,
        cloud_organization_id=ORG_ID,
        cloud_workspace_id=WORKSPACE_ID,
    )


def _build_checkpoint(mocker: MockerFixture, batch_definition_id: Optional[str]):
    """Build a minimal Checkpoint with a single ValidationDefinition whose
    BatchDefinition has the given id.
    """
    from great_expectations.checkpoint.checkpoint import Checkpoint

    batch_definition = mocker.Mock(spec=BatchDefinition)
    batch_definition.id = batch_definition_id

    validation_definition = ValidationDefinition.construct(
        name="my_validation_definition",
        data=batch_definition,
        suite=mocker.Mock(spec=ExpectationSuite),
        id=str(uuid.uuid4()),
    )

    return Checkpoint.construct(
        name="my_checkpoint",
        validation_definitions=[validation_definition],
        actions=[],
        id=CHECKPOINT_ID,
    )


@responses.activate
@pytest.mark.unit
def test_prepare_checkpoint_run_passes_batch_definition_id_when_available(
    mocker: MockerFixture,
) -> None:
    """SDK passes batch_definition_id as a query parameter when the checkpoint's
    validation definition has a batch_definition with an id.
    """
    responses.add(
        responses.GET,
        EXPECTATION_PARAMETERS_URL,
        json={"data": {"expectation_parameters": {}}},
        status=200,
    )

    ctx = _build_cloud_context()
    checkpoint = _build_checkpoint(mocker, batch_definition_id=BATCH_DEFINITION_ID)

    mocker.patch.object(
        type(ctx),
        "_checkpoint_has_windowed_expectations",
        return_value=True,
    )
    ctx.prepare_checkpoint_run(
        checkpoint=checkpoint,
        batch_parameters={},
        expectation_parameters={},
    )

    # The last call should be the expectation-parameters GET.
    expectation_params_call = responses.calls[-1]
    parsed = urlparse(expectation_params_call.request.url)
    query = parse_qs(parsed.query)
    assert query.get("batch_definition_id") == [BATCH_DEFINITION_ID]


@responses.activate
@pytest.mark.unit
def test_prepare_checkpoint_run_omits_batch_definition_id_when_unavailable(
    mocker: MockerFixture,
) -> None:
    """SDK does not pass batch_definition_id when it is not available. This
    preserves backward compatibility with older mercury versions that do not
    understand the query parameter.
    """
    responses.add(
        responses.GET,
        EXPECTATION_PARAMETERS_URL,
        json={"data": {"expectation_parameters": {}}},
        status=200,
    )

    ctx = _build_cloud_context()
    checkpoint = _build_checkpoint(mocker, batch_definition_id=None)

    mocker.patch.object(
        type(ctx),
        "_checkpoint_has_windowed_expectations",
        return_value=True,
    )
    ctx.prepare_checkpoint_run(
        checkpoint=checkpoint,
        batch_parameters={},
        expectation_parameters={},
    )

    expectation_params_call = responses.calls[-1]
    parsed = urlparse(expectation_params_call.request.url)
    query = parse_qs(parsed.query)
    assert "batch_definition_id" not in query
