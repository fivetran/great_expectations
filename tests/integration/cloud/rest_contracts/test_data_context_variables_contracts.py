"""Client-driven Pact contract tests for data-context-variables GET and PUT.

The data-context-variables endpoint is a singleton per org/workspace.  GET
returns the current configuration variables; PUT upserts (creates or updates)
them.  The GX Python client interacts with this endpoint via
``CloudDataContextVariables.save()`` (which always issues PUT).

URL pattern (V1 endpoint):
    /api/v1/organizations/{org_id}/workspaces/{workspace_id}/data-context-variables
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import pytest
from pact import Pact, match

from tests.integration.cloud.rest_contracts.conftest import (
    EXISTING_ORGANIZATION_ID,
    EXISTING_WORKSPACE_ID,
    GX_VERSION_REGEX,
)

if TYPE_CHECKING:
    import requests

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

DATA_CONTEXT_VARIABLES_PATH: Final[str] = (
    f"/api/v1/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/data-context-variables"
)

# ---------------------------------------------------------------------------
# Response body matchers
# ---------------------------------------------------------------------------

# The GET and PUT responses share the same schema:
# {
#   "data": {
#     "id": <uuid|null>,
#     "type": "data_context_variables",
#     "attributes": {
#       "organization_id": <uuid>,
#       "created_by_id": <uuid|null>,
#       "data_context_variables": { ... config fields ... }
#     }
#   }
# }
DATA_CONTEXT_VARIABLES_RESPONSE_BODY: Final[dict] = {
    "data": match.like(
        {
            "id": match.uuid(),
            "type": "data_context_variables",
            "attributes": match.like(
                {
                    "organization_id": match.uuid(),
                    "created_by_id": match.uuid(),
                    "data_context_variables": match.like(
                        {
                            "config_version": match.like(4.0),
                            "stores": match.like(
                                {
                                    "validation_definition_store": match.like({}),
                                }
                            ),
                            "data_context_id": match.uuid(),
                            "analytics_enabled": match.like(True),
                        }
                    ),
                }
            ),
        }
    )
}

# ---------------------------------------------------------------------------
# PUT request body matchers
# ---------------------------------------------------------------------------

# The PUT request body wraps the data-context-variables config under {"data": ...}.
# The GX client builds this via _construct_json_payload_v1 which produces
# {"data": {<serialized DataContextConfig fields>}}.
PUT_DATA_CONTEXT_VARIABLES_REQUEST_BODY: Final[dict] = {
    "data": match.like(
        {
            "config_version": match.like(4.0),
            "stores": match.like(
                {
                    "validation_definition_store": match.like(
                        {
                            "class_name": match.like("ValidationDefinitionStore"),
                            "store_backend": match.like(
                                {
                                    "class_name": match.like("GXCloudStoreBackend"),
                                    "ge_cloud_base_url": match.like("${GX_CLOUD_BASE_URL}"),
                                    "ge_cloud_credentials": match.like(
                                        {
                                            "access_token": match.like("${GX_CLOUD_ACCESS_TOKEN}"),
                                            "organization_id": match.like(
                                                "${GX_CLOUD_ORGANIZATION_ID}"
                                            ),
                                        }
                                    ),
                                    "ge_cloud_resource_type": match.like("validation_definition"),
                                    "suppress_store_backend_id": match.like(True),
                                }
                            ),
                        }
                    ),
                }
            ),
            "data_context_id": match.uuid(EXISTING_ORGANIZATION_ID),
            "analytics_enabled": match.like(True),
        }
    )
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.cloud
def test_get_data_context_variables(
    gx_cloud_session: requests.Session,
    cloud_access_token: str,
    pact_test: Pact,
) -> None:
    """GET /data-context-variables returns the current configuration variables.

    The GX client fetches these via GXCloudStoreBackend._get_all() when
    CloudDataContext needs the data context variables.
    """
    headers: dict = {
        k: (match.regex(str(v), regex=GX_VERSION_REGEX) if k == "Gx-Version" else str(v))
        for k, v in gx_cloud_session.headers.items()
    }

    (
        pact_test.upon_receiving("a request to get data context variables")
        .given("data context variables exist")
        .with_request("GET", DATA_CONTEXT_VARIABLES_PATH)
        .with_headers(headers)
        .will_respond_with(200)
        .with_body(DATA_CONTEXT_VARIABLES_RESPONSE_BODY, content_type="application/json")
    )

    with pact_test.serve() as srv:
        response = gx_cloud_session.get(f"{srv.url}{DATA_CONTEXT_VARIABLES_PATH}")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["type"] == "data_context_variables"
    assert "attributes" in data


@pytest.mark.cloud
def test_put_data_context_variables(
    gx_cloud_session: requests.Session,
    cloud_access_token: str,
    pact_test: Pact,
) -> None:
    """PUT /data-context-variables upserts the configuration variables.

    The GX client always uses PUT for data-context-variables (never POST),
    even when no existing row exists.  This is a special case handled in
    GXCloudStoreBackend._set().
    """
    headers: dict = {
        k: (match.regex(str(v), regex=GX_VERSION_REGEX) if k == "Gx-Version" else str(v))
        for k, v in gx_cloud_session.headers.items()
    }

    (
        pact_test.upon_receiving("a request to update data context variables")
        .given("data context variables are being updated")
        .with_request("PUT", DATA_CONTEXT_VARIABLES_PATH)
        .with_headers(headers)
        .with_body(PUT_DATA_CONTEXT_VARIABLES_REQUEST_BODY, content_type="application/json")
        .will_respond_with(200)
        .with_body(DATA_CONTEXT_VARIABLES_RESPONSE_BODY, content_type="application/json")
    )

    # Build a request body matching what the GX client sends
    put_body = {
        "data": {
            "config_version": 4.0,
            "stores": {
                "validation_definition_store": {
                    "class_name": "ValidationDefinitionStore",
                    "store_backend": {
                        "class_name": "GXCloudStoreBackend",
                        "ge_cloud_base_url": "${GX_CLOUD_BASE_URL}",
                        "ge_cloud_credentials": {
                            "access_token": "${GX_CLOUD_ACCESS_TOKEN}",
                            "organization_id": "${GX_CLOUD_ORGANIZATION_ID}",
                        },
                        "ge_cloud_resource_type": "validation_definition",
                        "suppress_store_backend_id": True,
                    },
                },
            },
            "data_context_id": EXISTING_ORGANIZATION_ID,
            "analytics_enabled": True,
        }
    }

    with pact_test.serve() as srv:
        response = gx_cloud_session.put(
            f"{srv.url}{DATA_CONTEXT_VARIABLES_PATH}",
            json=put_body,
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["type"] == "data_context_variables"
    assert "attributes" in data
