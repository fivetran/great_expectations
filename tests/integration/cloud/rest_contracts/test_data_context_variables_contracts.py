"""Client-driven Pact contract tests for data-context-variables GET and PUT.

The data-context-variables endpoint is a singleton per org/workspace.  GET
returns the current configuration variables; PUT upserts (creates or updates)
them.  The GX Python client interacts with this endpoint via
``CloudDataContextVariables.save()`` (which always issues PUT).

URL pattern (V1 endpoint):
    /api/v1/organizations/{org_id}/workspaces/{workspace_id}/data-context-variables

These tests exercise ``@public_api`` decorated entry points:
  - ``DataContextVariables`` (the class is ``@public_api``) accessed via
    ``ctx.variables``
  - ``DataContextVariables.save()`` which is ``@public_api``
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

DATA_CONTEXT_VARIABLES_PATH: Final[str] = (
    f"/api/v1/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/data-context-variables"
)

# ---------------------------------------------------------------------------
# PUT request body matchers
# ---------------------------------------------------------------------------

# The PUT request body wraps the serialized DataContextConfig under {"data": ...}.
# ``CloudDataContextVariables.save()`` calls ``store.set(key, config)`` which
# serializes the config via ``DataContextConfigSchema.dump()`` and then wraps it
# with ``_construct_json_payload_v1`` -> ``{"data": {<serialized config>}}``.
#
# The serialized config includes fields from DataContextConfigSchema.  The exact
# set depends on which fields are non-None after the post_dump hook strips None
# values.  The fields that are always present in a cloud context are:
# config_version, stores, analytics_enabled, data_context_id, plus nullable
# fields like plugins_directory, data_docs_sites, config_variables_file_path.
_STORE_BACKEND_EXAMPLE: Final[dict] = {
    "class_name": match.like("GXCloudStoreBackend"),
    "ge_cloud_base_url": match.like("${GX_CLOUD_BASE_URL}"),
    "ge_cloud_credentials": match.like(
        {
            "access_token": match.like("${GX_CLOUD_ACCESS_TOKEN}"),
            "organization_id": match.like("${GX_CLOUD_ORGANIZATION_ID}"),
        }
    ),
    "ge_cloud_resource_type": match.like("expectation_suite"),
    "suppress_store_backend_id": match.like(True),
}

PUT_DATA_CONTEXT_VARIABLES_REQUEST_BODY: Final[dict] = {
    "data": match.like(
        {
            "config_version": match.like(4.0),
            "stores": match.like(
                {
                    "default_expectations_store": match.like(
                        {
                            "class_name": match.like("ExpectationsStore"),
                            "store_backend": match.like(_STORE_BACKEND_EXAMPLE),
                        }
                    ),
                    "default_checkpoint_store": match.like(
                        {
                            "class_name": match.like("CheckpointStore"),
                            "store_backend": match.like(_STORE_BACKEND_EXAMPLE),
                        }
                    ),
                    "default_validations_store": match.like(
                        {
                            "class_name": match.like("ValidationResultsStore"),
                            "store_backend": match.like(_STORE_BACKEND_EXAMPLE),
                        }
                    ),
                    "validation_definition_store": match.like(
                        {
                            "class_name": match.like("ValidationDefinitionStore"),
                            "store_backend": match.like(_STORE_BACKEND_EXAMPLE),
                        }
                    ),
                }
            ),
            "analytics_enabled": match.like(True),
            "data_context_id": match.uuid(EXISTING_ORGANIZATION_ID),
            "config_variables_file_path": match.like(None),
            "data_docs_sites": match.like(None),
            "plugins_directory": match.like(None),
        }
    )
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.cloud
def test_get_data_context_variables(pact_test: Pact) -> None:
    """Accessing ctx.variables on a CloudDataContext returns configuration variables.

    The CloudDataContext constructor fetches the data-context-configuration
    endpoint which provides the project config.  Accessing ``ctx.variables``
    returns a ``DataContextVariables`` instance (``@public_api``) populated
    from this config.

    Full interaction sequence:
      1. GET /data-context-configuration  (context init)
    """
    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="get-data-context-variables",
    )

    with pact_test.serve() as srv:
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )

        # Access the @public_api DataContextVariables
        variables = ctx.variables

    assert variables is not None
    assert variables.config_version is not None
    assert variables.stores is not None


@pytest.mark.cloud
def test_put_data_context_variables(pact_test: Pact) -> None:
    """ctx.variables.save() issues PUT to the data-context-variables endpoint.

    ``DataContextVariables.save()`` is ``@public_api`` and persists the
    current config via the configured store.  For a CloudDataContext this
    results in a PUT request to the data-context-variables endpoint.

    Full interaction sequence:
      1. GET /data-context-configuration       (context init)
      2. PUT /data-context-variables           (save)
    """
    headers = pact_session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="put-data-context-variables",
    )

    # 2. PUT /data-context-variables
    (
        pact_test.upon_receiving("a request to update data context variables (client-driven)")
        .given("data context variables are being updated")
        .with_request("PUT", DATA_CONTEXT_VARIABLES_PATH)
        .with_headers(headers)
        .with_body(PUT_DATA_CONTEXT_VARIABLES_REQUEST_BODY, content_type="application/vnd.api+json")
        .will_respond_with(200)
        .with_body(
            {
                "data": match.like(
                    {
                        "id": match.uuid(),
                        "type": "data_context_variables",
                        "attributes": match.like(
                            {
                                "organization_id": match.uuid(),
                                "data_context_variables": match.like({}),
                            }
                        ),
                    }
                )
            },
            content_type="application/json",
        )
    )

    with pact_test.serve() as srv:
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )

        # Call the @public_api save() method to trigger the PUT
        ctx.variables.save()
