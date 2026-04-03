from __future__ import annotations

import os
import pathlib
import subprocess
import uuid
from typing import TYPE_CHECKING, Any, Dict, Final, List, Union

import pact
import pytest

from great_expectations.core.http import create_session
from great_expectations.data_context import CloudDataContext
from great_expectations.data_context.data_context.context_factory import project_manager

if TYPE_CHECKING:
    from requests import Session
    from typing_extensions import TypeAlias


CONSUMER_NAME: Final[str] = "great_expectations"
PROVIDER_NAME: Final[str] = "mercury"

# Dummy token used by pact_cloud_context — the Pact mock server does not validate credentials.
PACT_DUMMY_ACCESS_TOKEN: Final[str] = "dummy-pact-access-token"


PACT_MOCK_HOST: Final[str] = "localhost"
PACT_MOCK_PORT: Final[int] = 9292
PACT_DIR: Final[pathlib.Path] = pathlib.Path(pathlib.Path(__file__, ".."), "pacts").resolve()
PACT_MOCK_SERVICE_URL: Final[str] = f"http://{PACT_MOCK_HOST}:{PACT_MOCK_PORT}"


JsonData: TypeAlias = Union[None, int, str, bool, List[Any], Dict[str, Any]]

PactBody: TypeAlias = Union[
    Dict[str, Union[JsonData, pact.matchers.Matcher]], pact.matchers.Matcher, None
]


EXISTING_ORGANIZATION_ID: Final[str] = (
    os.environ.get("GX_CLOUD_ORGANIZATION_ID", "") or "0ccac18e-7631-4bdd-8a42-3c35cce574c6"
)
EXISTING_WORKSPACE_ID: Final[str] = (
    os.environ.get("GX_CLOUD_WORKSPACE_ID", "") or "44444444-4444-4bdd-8a42-3c35cce574c6"
)

# Full data-context-configuration response body used as the Pact mock response when
# constructing a CloudDataContext in tests.  Store backend URLs use the environment-variable
# placeholder so they resolve correctly at runtime regardless of mock host/port.
DATA_CONTEXT_CONFIG_RESPONSE_BODY: Final[dict] = {
    "anonymous_usage_statistics": pact.Like(
        {
            "data_context_id": pact.Format().uuid,
            "enabled": False,
        }
    ),
    "datasources": pact.Like({}),
    "checkpoint_store_name": "default_checkpoint_store",
    "expectations_store_name": "default_expectations_store",
    "validation_results_store_name": "default_validation_results_store",
    "stores": {
        "default_expectations_store": {
            "class_name": "ExpectationsStore",
            "store_backend": {
                "class_name": "GXCloudStoreBackend",
                "ge_cloud_base_url": r"${GX_CLOUD_BASE_URL}",
                "ge_cloud_credentials": {
                    "access_token": r"${GX_CLOUD_ACCESS_TOKEN}",
                    "organization_id": r"${GX_CLOUD_ORGANIZATION_ID}",
                },
                "ge_cloud_resource_type": "expectation_suite",
                "suppress_store_backend_id": True,
            },
        },
        "default_checkpoint_store": {
            "class_name": "CheckpointStore",
            "store_backend": {
                "class_name": "GXCloudStoreBackend",
                "ge_cloud_base_url": r"${GX_CLOUD_BASE_URL}",
                "ge_cloud_credentials": {
                    "access_token": r"${GX_CLOUD_ACCESS_TOKEN}",
                    "organization_id": r"${GX_CLOUD_ORGANIZATION_ID}",
                },
                "ge_cloud_resource_type": "checkpoint",
                "suppress_store_backend_id": True,
            },
        },
        "default_validation_results_store": {
            "class_name": "ValidationResultsStore",
            "store_backend": {
                "class_name": "GXCloudStoreBackend",
                "ge_cloud_base_url": r"${GX_CLOUD_BASE_URL}",
                "ge_cloud_credentials": {
                    "access_token": r"${GX_CLOUD_ACCESS_TOKEN}",
                    "organization_id": r"${GX_CLOUD_ORGANIZATION_ID}",
                },
                "ge_cloud_resource_type": "validation_result",
                "suppress_store_backend_id": True,
            },
        },
    },
}


@pytest.fixture
def cloud_base_url() -> str:
    try:
        return os.environ["GX_CLOUD_BASE_URL"]
    except KeyError as e:
        raise OSError("GX_CLOUD_BASE_URL is not set in this environment.") from e


@pytest.fixture
def cloud_access_token() -> str:
    try:
        return os.environ["GX_CLOUD_ACCESS_TOKEN"]
    except KeyError as e:
        raise OSError("GX_CLOUD_ACCESS_TOKEN is not set in this environment.") from e


@pytest.fixture(scope="module")
def gx_cloud_session() -> Session:
    try:
        access_token = os.environ["GX_CLOUD_ACCESS_TOKEN"]
    except KeyError as e:
        raise OSError("GX_CLOUD_ACCESS_TOKEN is not set in this environment.") from e
    return create_session(access_token=access_token)


@pytest.fixture
def cloud_data_context(
    cloud_base_url: str,
    cloud_access_token: str,
    pact_test: pact.Pact,
) -> CloudDataContext:
    """This is a real Cloud Data Context that points to the pact mock service instead of the Mercury API."""  # noqa: E501 # FIXME CoP
    cloud_data_context = CloudDataContext(
        cloud_base_url=cloud_base_url,
        cloud_organization_id=EXISTING_ORGANIZATION_ID,
        cloud_workspace_id=EXISTING_WORKSPACE_ID,
        cloud_access_token=cloud_access_token,
    )
    # we can't override the base url to use the mock service due to
    # reliance on env vars, so instead we override with a real project config
    project_config = cloud_data_context.config

    with pact_test:
        context = CloudDataContext(
            cloud_base_url=PACT_MOCK_SERVICE_URL,
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=cloud_access_token,
            project_config=project_config,
        )

    project_manager.set_project(cloud_data_context)
    return context


def setup_data_context_config_interaction(
    pact_test: pact.Pact,
    access_token: str,
) -> None:
    """Register the GET /data-context-configuration Pact interaction.

    Nearly every client-driven contract test needs this because
    ``CloudDataContext.__init__`` always fetches the data-context-configuration
    endpoint.  Call this helper before entering the ``with pact_test:`` block in
    any fixture or test that constructs a ``CloudDataContext`` against the Pact
    mock server.

    Args:
        pact_test: The active ``pact.Pact`` instance (from the ``pact_test`` fixture).
        access_token: The access token to use in the ``Authorization: Bearer`` header
            that will be matched against the recorded interaction.  Pass
            ``PACT_DUMMY_ACCESS_TOKEN`` when no real credentials are needed (e.g.
            in the ``pact_cloud_context`` fixture), or a real token when testing
            against a live provider.
    """
    session = create_session(access_token=access_token)
    path = (
        f"/api/v1/organizations/{EXISTING_ORGANIZATION_ID}/"
        f"workspaces/{EXISTING_WORKSPACE_ID}/data-context-configuration"
    )
    (
        pact_test.given(provider_state="the Data Context exists")
        .upon_receiving(scenario="a request for Data Context configuration (client-driven setup)")
        .with_request(
            method="GET",
            path=path,
            headers=dict(session.headers),
        )
        .will_respond_with(
            status=200,
            body=DATA_CONTEXT_CONFIG_RESPONSE_BODY,
        )
    )


@pytest.fixture
def pact_cloud_context(
    pact_test: pact.Pact,
) -> CloudDataContext:
    """A ``CloudDataContext`` backed by the Pact mock server.

    Unlike ``cloud_data_context``, this fixture does **not** require real cloud
    credentials (``GX_CLOUD_BASE_URL`` / ``GX_CLOUD_ACCESS_TOKEN`` environment
    variables).  All configuration is supplied through
    ``DATA_CONTEXT_CONFIG_RESPONSE_BODY`` so the Pact mock server can respond
    correctly without contacting Mercury.  Both the registered Pact interaction
    headers and the ``CloudDataContext`` itself use ``PACT_DUMMY_ACCESS_TOKEN``
    so that the token is consistent end-to-end.

    Use this fixture in new client-driven contract tests instead of
    ``cloud_data_context``.
    """
    setup_data_context_config_interaction(pact_test, access_token=PACT_DUMMY_ACCESS_TOKEN)

    with pact_test:
        context = CloudDataContext(
            cloud_base_url=PACT_MOCK_SERVICE_URL,
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )

    return context


def get_git_commit_hash() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("ascii").strip()


@pytest.fixture(scope="package")
def pact_test(request) -> pact.Pact:
    """
    pact_test can be used as a context manager and will:
    1. write a new contract to the pact dir
    2. verify the contract against the mock service
    """
    pact_broker_base_url = "https://greatexpectations.pactflow.io"

    broker_token: str
    publish_to_broker: bool
    if os.environ.get("PACT_BROKER_READ_WRITE_TOKEN"):
        broker_token = os.environ.get("PACT_BROKER_READ_WRITE_TOKEN", "")
        publish_to_broker = True
    elif os.environ.get("PACT_BROKER_READ_ONLY_TOKEN"):
        broker_token = os.environ.get("PACT_BROKER_READ_ONLY_TOKEN", "")
        publish_to_broker = False
    else:
        pytest.skip(
            "no pact credentials: set PACT_BROKER_READ_ONLY_TOKEN from greatexpectations.pactflow.io"  # noqa: E501 # FIXME CoP
        )

    # Adding random id to the commit hash allows us to run the build
    # and publish the contract more than once for a given commit.
    # We need this because we have the ability to trigger re-run of tests
    # in GH, and we run the release build process on the tagged commit.
    version = f"{get_git_commit_hash()}_{str(uuid.uuid4())[:5]}"

    _pact: pact.Pact = pact.Consumer(
        name=CONSUMER_NAME,
        version=version,
        tag_with_git_branch=True,
        auto_detect_version_properties=True,
    ).has_pact_with(
        pact.Provider(name=PROVIDER_NAME),
        broker_base_url=pact_broker_base_url,
        broker_token=broker_token,
        host_name=PACT_MOCK_HOST,
        port=PACT_MOCK_PORT,
        pact_dir=str(PACT_DIR),
        publish_to_broker=publish_to_broker,
    )

    _pact.start_service()
    yield _pact
    _pact.stop_service()
