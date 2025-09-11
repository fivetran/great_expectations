from __future__ import annotations

from typing import TYPE_CHECKING, Final

import pact
import pytest

import great_expectations as gx
from tests.integration.cloud.rest_contracts.conftest import (
    EXISTING_ORGANIZATION_ID,
    EXISTING_WORKSPACE_ID,
    PACT_MOCK_SERVICE_URL,
)

if TYPE_CHECKING:
    import requests


GET_DATA_CONTEXT_CONFIGURATION_MIN_RESPONSE_BODY: Final[dict] = {
    "anonymous_usage_statistics": pact.Like(
        {
            "data_context_id": pact.Format().uuid,
            "enabled": False,
        }
    ),
    "datasources": pact.Like({}),
}


@pytest.mark.cloud
def test_data_context_configuration(
    gx_cloud_session: requests.Session,
    cloud_access_token: str,
    pact_test: pact.Pact,
) -> None:
    # arrange
    (
        pact_test.given("the Data Context exists")
        .upon_receiving("a request for a Data Context")
        .with_request(
            headers=dict(gx_cloud_session.headers),
            method="GET",
            path=f"/api/v1/organizations/{EXISTING_ORGANIZATION_ID}/workspaces/{EXISTING_WORKSPACE_ID}/data-context-configuration",
        )
        .will_respond_with(
            status=200,
            body=GET_DATA_CONTEXT_CONFIGURATION_MIN_RESPONSE_BODY,
        )
    )

    with pact_test:
        # act
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=PACT_MOCK_SERVICE_URL,
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=cloud_access_token,
        )

    # assert
    assert ctx.data_sources.all() is not None
