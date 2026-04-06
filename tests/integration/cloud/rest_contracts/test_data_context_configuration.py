from __future__ import annotations

from typing import TYPE_CHECKING, Final

import pytest
from pact import Pact, match

import great_expectations as gx
from tests.integration.cloud.rest_contracts.conftest import (
    EXISTING_ORGANIZATION_ID,
    EXISTING_WORKSPACE_ID,
)

if TYPE_CHECKING:
    import requests


GET_DATA_CONTEXT_CONFIGURATION_MIN_RESPONSE_BODY: Final[dict] = {
    "anonymous_usage_statistics": match.like(
        {
            "data_context_id": match.uuid(),
            "enabled": False,
        }
    ),
    "datasources": match.like({}),
}


@pytest.mark.cloud
def test_data_context_configuration(
    gx_cloud_session: requests.Session,
    cloud_access_token: str,
    pact_test: Pact,
) -> None:
    # Arrange: set up the data context configuration endpoint interaction
    provider_state = "the Data Context exists"
    scenario = "a request for a Data Context"
    method = "GET"
    path = (
        f"/api/v1/organizations/{EXISTING_ORGANIZATION_ID}/"
        f"workspaces/{EXISTING_WORKSPACE_ID}/data-context-configuration"
    )
    status = 200
    response_body = GET_DATA_CONTEXT_CONFIGURATION_MIN_RESPONSE_BODY

    (
        pact_test.upon_receiving(scenario)
        .given(provider_state)
        .with_request(method, path)
        .with_headers({k: str(v) for k, v in gx_cloud_session.headers.items()})
        .will_respond_with(status)
        .with_body(response_body, content_type="application/json")
    )

    # Act
    with pact_test.serve() as srv:
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=cloud_access_token,
        )

    # Assert
    assert ctx.data_sources.all() is not None
