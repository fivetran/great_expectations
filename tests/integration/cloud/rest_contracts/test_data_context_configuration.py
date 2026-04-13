from __future__ import annotations

from typing import Final

import pytest
from pact import Pact, match

import great_expectations as gx
from tests.integration.cloud.rest_contracts.conftest import (
    EXISTING_ORGANIZATION_ID,
    EXISTING_WORKSPACE_ID,
    PACT_DUMMY_ACCESS_TOKEN,
    pact_session_headers,
)

GET_DATA_CONTEXT_CONFIGURATION_MIN_RESPONSE_BODY: Final[dict] = {
    "analytics_enabled": match.like(True),
}


@pytest.mark.cloud
def test_data_context_configuration(
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
    headers = pact_session_headers()

    (
        pact_test.upon_receiving(scenario)
        .given(provider_state)
        .with_request(method, path)
        .with_headers(headers)
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
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )

    # Assert
    assert ctx.data_sources.all() is not None
