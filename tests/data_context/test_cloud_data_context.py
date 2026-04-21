import json
import uuid
from typing import Any, Dict, List, Tuple
from urllib.parse import parse_qs, urlparse

import pytest
import responses
from pytest_mock import MockerFixture

from great_expectations.checkpoint.checkpoint import Checkpoint
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


CHECKPOINT_ID = str(uuid.uuid4())
BATCH_DEFINITION_ID = str(uuid.uuid4())
# urljoin() with an absolute URL path replaces the base URL's path, so the
# resulting request goes to the host root, not to ``{CLOUD_BASE_URL}``.
EXPECTATION_PARAMETERS_URL = (
    "https://api.greatexpectations.io"
    f"/api/v1/organizations/{ORG_ID}"
    f"/workspaces/{WORKSPACE_ID}/checkpoints/{CHECKPOINT_ID}/expectation-parameters"
)


class TestPrepareCheckpointRun:
    """Tests for ``CloudDataContext.prepare_checkpoint_run`` grouped-call
    behavior against ``GET /expectation-parameters``.

    Mercury's forecast store is keyed by ``(expectation_id, batch_definition_id)``,
    so an expectation's dynamic parameters are only correct when the server
    resolves them using that expectation's own ``batch_definition_id``. When
    a checkpoint spans multiple batch definitions, the client issues one call
    per distinct id and merges responses by ``parameter_name``, keeping each
    parameter only from the call whose ``batch_definition_id`` matches the
    expectation that owns it.
    """

    @staticmethod
    def _build_cloud_context() -> CloudDataContext:
        """CloudDataContext whose /data-context-configuration call is mocked.

        This is a static helper (not a ``@pytest.fixture``) because
        ``responses.add`` has to execute inside the test's ``@responses.activate``
        wrapper — fixtures resolve before the wrapper takes effect, so mocks
        registered in a fixture don't intercept the ``__init__`` HTTP call.
        """
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

    @pytest.fixture
    def make_checkpoint(self, mocker: MockerFixture):
        """Factory fixture: build a Checkpoint from a list of tuples of the form
        ``(batch_definition_id, [parameter_names])`` — one tuple per
        ValidationDefinition. Each parameter_name becomes a single windowed
        expectation under that validation definition's suite.
        """

        def _build(
            validation_defs: List[Tuple[str, List[str]]],
        ) -> Checkpoint:
            vds = []
            for batch_definition_id, parameter_names in validation_defs:
                batch_definition = mocker.Mock(spec=BatchDefinition)
                batch_definition.id = batch_definition_id

                expectations = []
                for parameter_name in parameter_names:
                    window = mocker.Mock()
                    window.parameter_name = parameter_name
                    expectation = mocker.Mock()
                    expectation.windows = [window]
                    expectations.append(expectation)

                suite = mocker.Mock(spec=ExpectationSuite)
                suite.expectations = expectations

                vd = ValidationDefinition.construct(
                    name=f"vd_{batch_definition_id}",
                    data=batch_definition,
                    suite=suite,
                    id=str(uuid.uuid4()),
                )
                vds.append(vd)

            return Checkpoint.construct(
                name="my_checkpoint",
                validation_definitions=vds,
                actions=[],
                id=CHECKPOINT_ID,
            )

        return _build

    @staticmethod
    def _expectation_parameter_calls() -> List[responses.Call]:
        return [
            call
            for call in responses.calls
            if call.request.url and "expectation-parameters" in call.request.url
        ]

    @staticmethod
    def _batch_definition_id_on_call(call: responses.Call) -> str | None:
        url = call.request.url
        if url is None:
            return None
        values = parse_qs(urlparse(url).query).get("batch_definition_id")
        return values[0] if values else None

    @responses.activate
    @pytest.mark.unit
    def test_passes_batch_definition_id_when_available(self, make_checkpoint) -> None:
        responses.add(
            responses.GET,
            EXPECTATION_PARAMETERS_URL,
            json={"data": {"expectation_parameters": {"p_max": 42}}},
            status=200,
        )
        checkpoint = make_checkpoint([(BATCH_DEFINITION_ID, ["p_max"])])

        self._build_cloud_context().prepare_checkpoint_run(
            checkpoint=checkpoint,
            batch_parameters={},
            expectation_parameters={},
        )

        ep_calls = self._expectation_parameter_calls()
        assert len(ep_calls) == 1
        assert self._batch_definition_id_on_call(ep_calls[0]) == BATCH_DEFINITION_ID

    @responses.activate
    @pytest.mark.unit
    def test_groups_calls_by_distinct_batch_definition_id(self, make_checkpoint) -> None:
        """Checkpoint spans two batch definitions → two grouped calls, one per
        distinct id. Mercury returns entries only for expectations whose owning
        validation definition uses the passed batch_definition_id, so the
        responses carry disjoint keys and merge cleanly.
        """
        batch_definition_id_a = str(uuid.uuid4())
        batch_definition_id_b = str(uuid.uuid4())

        def callback(request):
            bd_id = parse_qs(urlparse(request.url).query).get("batch_definition_id", [None])[0]
            if bd_id == batch_definition_id_a:
                body = {"data": {"expectation_parameters": {"p_a_max": 111}}}
            elif bd_id == batch_definition_id_b:
                body = {"data": {"expectation_parameters": {"p_b_max": 222}}}
            else:
                body = {"data": {"expectation_parameters": {}}}
            return (200, {}, json.dumps(body))

        responses.add_callback(
            responses.GET,
            EXPECTATION_PARAMETERS_URL,
            callback=callback,
            content_type="application/json",
        )

        checkpoint = make_checkpoint(
            [
                (batch_definition_id_a, ["p_a_max"]),
                (batch_definition_id_b, ["p_b_max"]),
            ]
        )
        expectation_parameters: dict = {}

        self._build_cloud_context().prepare_checkpoint_run(
            checkpoint=checkpoint,
            batch_parameters={},
            expectation_parameters=expectation_parameters,
        )

        ep_calls = self._expectation_parameter_calls()
        assert len(ep_calls) == 2
        bd_ids_used = sorted(
            bd_id
            for bd_id in (self._batch_definition_id_on_call(c) for c in ep_calls)
            if bd_id is not None
        )
        assert bd_ids_used == sorted([batch_definition_id_a, batch_definition_id_b])

        # Responses from each call carry disjoint keys; the merge is a union.
        assert expectation_parameters == {"p_a_max": 111, "p_b_max": 222}
