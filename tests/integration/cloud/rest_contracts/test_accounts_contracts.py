"""Client-driven Pact contract tests for the accounts/me endpoint.

Each test:
1. Registers the GET /data-context-configuration interaction via
   ``setup_data_context_config_interaction()``.
2. Registers the accounts/me interaction.
3. Constructs a ``CloudDataContext`` and exercises ``cloud_user_info()``
   inside the ``with pact_test.serve() as srv:`` block.
4. Asserts the client correctly parses the response.

URL pattern (V0 — no /api/v1 prefix, no workspace segment):
    GET /organizations/{org_id}/accounts/me
"""

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
    setup_data_context_config_interaction,
)

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

# V0 endpoint path — no /api/v1 prefix and no workspace segment.
ACCOUNTS_ME_PATH: Final[str] = f"/organizations/{EXISTING_ORGANIZATION_ID}/accounts/me"

# ---------------------------------------------------------------------------
# Response body matcher
# ---------------------------------------------------------------------------

ACCOUNTS_ME_RESPONSE_BODY: Final[dict] = {
    "id": match.uuid(),
    "organization_id": match.uuid(),
    "workspaces": match.each_like(
        {
            "id": match.uuid(),
            "name": match.like("pact-test-workspace"),
            "role": match.like("admin"),
        },
        min=1,
    ),
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.cloud
def test_get_accounts_me(pact_test: Pact) -> None:
    """GET /organizations/{org_id}/accounts/me returns the current user's info.

    ``CloudDataContext.cloud_user_info()`` issues a GET to the V0
    accounts/me endpoint (no /api/v1 prefix, no workspace segment) and
    parses ``id`` and ``workspaces`` from the response.

    Two interactions are registered:
      1. GET /data-context-configuration  (context init)
      2. GET /accounts/me                 (primary contract under test)
    """
    headers = pact_session_headers()

    # 1. GET /data-context-configuration (required for context init)
    setup_data_context_config_interaction(
        pact_test, access_token=PACT_DUMMY_ACCESS_TOKEN, description_suffix="accounts-me"
    )

    # 2. GET /organizations/{org_id}/accounts/me
    (
        pact_test.upon_receiving("a request to get the current user account (client-driven)")
        .given("the user account exists")
        .with_request("GET", ACCOUNTS_ME_PATH)
        .with_headers(headers)
        .will_respond_with(200)
        .with_body(ACCOUNTS_ME_RESPONSE_BODY, content_type="application/json")
    )

    with pact_test.serve() as srv:
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )
        # cloud_user_info() is a public method on CloudDataContext; it delegates
        # to _get_cloud_user_info() internally.
        user_info = ctx.cloud_user_info()

    assert user_info is not None
    assert user_info.user_id is not None
    assert len(user_info.workspaces) >= 1
