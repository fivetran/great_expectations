"""Client-driven Pact contract tests for datasource CRUD operations.

Each test:
1. Registers the GET /data-context-configuration interaction via
   ``setup_data_context_config_interaction()``.
2. Registers the datasource-specific interaction(s).
3. Constructs a ``CloudDataContext`` and exercises the Python client API inside
   the ``with pact_test.serve() as srv:`` block.
4. Asserts the client correctly parses the response.

URL pattern for datasources (V2 endpoint):
    /api/v2/organizations/{org_id}/workspaces/{workspace_id}/datasources
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

EXISTING_DATASOURCE_ID: Final[str] = "aabbccdd-1234-4abc-8def-1122334455aa"
DATASOURCE_NAME: Final[str] = "my_pandas_datasource"

# Base path for the V2 datasources endpoint
DATASOURCES_PATH: Final[str] = (
    f"/api/v2/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/datasources"
)
DATASOURCE_BY_ID_PATH: Final[str] = f"{DATASOURCES_PATH}/{EXISTING_DATASOURCE_ID}"

# ---------------------------------------------------------------------------
# Shared response body matchers
# ---------------------------------------------------------------------------

# Minimal response returned by a single-datasource GET (by id or by name)
SINGLE_DATASOURCE_RESPONSE_BODY: Final[dict] = {
    "data": match.like(
        {
            "id": match.uuid(),
            "type": match.like("pandas"),
            "name": match.like(DATASOURCE_NAME),
            "assets": match.like([]),
        }
    )
}

# Minimal response returned when the datasource list is empty
EMPTY_DATASOURCE_LIST_RESPONSE_BODY: Final[dict] = {
    "data": [],
}

# POST request body matcher for a Pandas datasource (no id -- datasource doesn't exist yet)
PANDAS_DATASOURCE_REQUEST_BODY: Final[dict] = {
    "data": match.like(
        {
            "type": match.like("pandas"),
            "name": match.like(DATASOURCE_NAME),
        }
    )
}

# PUT request body matcher for a Pandas datasource (includes id -- datasource already exists)
PANDAS_DATASOURCE_UPDATE_REQUEST_BODY: Final[dict] = {
    "data": match.like(
        {
            "id": match.uuid(EXISTING_DATASOURCE_ID),
            "type": match.like("pandas"),
            "name": match.like(DATASOURCE_NAME),
        }
    )
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _session_headers() -> dict:
    """Return request headers matching what the Python client sends."""
    return pact_session_headers()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.cloud
def test_add_pandas_datasource(pact_test: Pact) -> None:
    """add_pandas() issues GET /datasources (list), POST /datasources, then GET /datasources/{id}.

    ``_add_fluent_datasource`` checks ``if datasource_name in self.data_sources.all()``
    before POSTing, which triggers ``DatasourceDict.__contains__`` ->
    ``_get_all()`` -> ``GET /datasources`` (no params).  After a successful
    POST, ``_persist_datasource`` re-fetches with both id in the path and name
    as a query parameter.

    Four interactions are registered in total:
      1. GET /data-context-configuration   (context init)
      2. GET /datasources                  (existence check before add)
      3. POST /datasources                 (primary contract under test)
      4. GET /datasources/{id}?name=...    (post-POST refresh in _persist_datasource)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration (required for context init)
    setup_data_context_config_interaction(
        pact_test, access_token=PACT_DUMMY_ACCESS_TOKEN, description_suffix="add-datasource"
    )

    # 2. GET /datasources (list -- _add_fluent_datasource __contains__ check)
    (
        pact_test.upon_receiving(
            "a request to list datasources to check existence before add (client-driven)"
        )
        .given("the Pandas datasource does not exist")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .will_respond_with(200)
        .with_body(EMPTY_DATASOURCE_LIST_RESPONSE_BODY, content_type="application/json")
    )

    # 3. POST /datasources (the primary contract under test)
    # Use EXISTING_DATASOURCE_ID as the exact id so the follow-up GET path is deterministic.
    post_response_body = {
        "data": match.like(
            {
                "id": EXISTING_DATASOURCE_ID,
                "type": match.like("pandas"),
                "name": match.like(DATASOURCE_NAME),
                "assets": match.like([]),
            }
        )
    }
    (
        pact_test.upon_receiving("a request to add a Pandas datasource (client-driven)")
        .given("the Pandas datasource does not exist")
        .with_request("POST", DATASOURCES_PATH)
        .with_headers(headers)
        .with_body(PANDAS_DATASOURCE_REQUEST_BODY, content_type="application/vnd.api+json")
        .will_respond_with(201)
        .with_body(post_response_body, content_type="application/json")
    )

    # 4. GET /datasources/{id}?name=... (_persist_datasource re-fetches with id + name)
    (
        pact_test.upon_receiving(
            "a request to fetch the newly-created Pandas datasource by id (client-driven)"
        )
        .given("the Pandas datasource was just created")
        .with_request("GET", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(SINGLE_DATASOURCE_RESPONSE_BODY, content_type="application/json")
    )

    with pact_test.serve() as srv:
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )
        datasource = ctx.data_sources.add_pandas(name=DATASOURCE_NAME)

    assert datasource is not None
    assert datasource.name == DATASOURCE_NAME


@pytest.mark.cloud
def test_get_pandas_datasource(pact_test: Pact) -> None:
    """data_sources.get() issues two GET /datasources?name=... requests via retrieve_by_name.

    ``retrieve_by_name`` first calls ``has_key`` (one GET) then ``get``
    (a second GET).  Both GETs target the same URL with the same query
    parameter.  Pact v3 reuses a single registered interaction for both
    identical requests, so only one interaction is registered here.

    Two interactions are registered in total:
      1. GET /data-context-configuration   (context init)
      2. GET /datasources?name=...         (serves both has_key and get calls)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration (required for context init)
    setup_data_context_config_interaction(
        pact_test, access_token=PACT_DUMMY_ACCESS_TOKEN, description_suffix="get-datasource"
    )

    # 2. GET /datasources?name=... (serves both has_key probe and actual get in retrieve_by_name)
    get_response_body = {
        "data": match.each_like(
            {
                "id": match.uuid(),
                "type": match.like("pandas"),
                "name": match.like(DATASOURCE_NAME),
                "assets": match.like([]),
            },
            min=1,
        )
    }
    (
        pact_test.upon_receiving("a request to get the Pandas datasource by name (client-driven)")
        .given("the Pandas datasource exists")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(get_response_body, content_type="application/json")
    )

    with pact_test.serve() as srv:
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )
        datasource = ctx.data_sources.get(name=DATASOURCE_NAME)

    assert datasource is not None
    assert datasource.name == DATASOURCE_NAME


@pytest.mark.cloud
def test_add_or_update_pandas_datasource_puts_when_exists(
    pact_test: Pact,
) -> None:
    """add_or_update_pandas() issues a PUT /datasources/{id} when the datasource already exists.

    ``add_or_update_datasource`` makes list GETs (via ``DatasourceDict.__contains__``)
    and by-name GETs (via ``retrieve_by_name``).  In Pact v3, an interaction
    registered WITHOUT query parameters means "expect NO query parameters",
    so we must register separate interactions for the list call (no query)
    and the by-name call (with ``?name=...``).  After PUT,
    ``_persist_datasource`` re-fetches with both id in the path and name as
    a query parameter.

    Five interactions are registered in total:
      1. GET /data-context-configuration   (context init)
      2. GET /datasources                  (list -- DatasourceDict.__contains__)
      3. GET /datasources?name=...         (by-name -- retrieve_by_name)
      4. PUT /datasources/{id}             (primary contract under test)
      5. GET /datasources/{id}?name=...    (post-PUT refresh in _persist_datasource)
    """
    headers = _session_headers()

    # -- Single-datasource payload used in list and by-name responses --
    existing_ds_payload = {
        "id": EXISTING_DATASOURCE_ID,
        "type": "pandas",
        "name": DATASOURCE_NAME,
        "assets": [],
    }
    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test, access_token=PACT_DUMMY_ACCESS_TOKEN, description_suffix="update-datasource"
    )

    # 2. GET /datasources (no query -- list call from DatasourceDict.__contains__)
    (
        pact_test.upon_receiving(
            "list datasources for add_or_update existence check (client-driven)"
        )
        .given("the Pandas datasource exists for update")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(existing_ds_payload, min=1)},
            content_type="application/json",
        )
    )

    # 3. GET /datasources?name=... (by-name -- retrieve_by_name calls)
    (
        pact_test.upon_receiving(
            "get datasource by name for add_or_update retrieve_by_name (client-driven)"
        )
        .given("the Pandas datasource exists for update")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(existing_ds_payload, min=1)},
            content_type="application/json",
        )
    )

    # 4. PUT /datasources/{id} -- the primary contract under test
    (
        pact_test.upon_receiving("a request to update a Pandas datasource via PUT (client-driven)")
        .given("the Pandas datasource exists for update")
        .with_request("PUT", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_body(PANDAS_DATASOURCE_UPDATE_REQUEST_BODY, content_type="application/vnd.api+json")
        .will_respond_with(200)
        .with_body(SINGLE_DATASOURCE_RESPONSE_BODY, content_type="application/json")
    )

    # 5. GET /datasources/{id}?name=... (post-PUT refresh in _persist_datasource)
    (
        pact_test.upon_receiving(
            "a request to fetch the updated Pandas datasource by id (client-driven)"
        )
        .given("the Pandas datasource exists for update")
        .with_request("GET", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(SINGLE_DATASOURCE_RESPONSE_BODY, content_type="application/json")
    )

    with pact_test.serve() as srv:
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )
        datasource = ctx.data_sources.add_or_update_pandas(name=DATASOURCE_NAME)

    assert datasource is not None
    assert datasource.name == DATASOURCE_NAME


@pytest.mark.cloud
def test_delete_pandas_datasource(pact_test: Pact) -> None:
    """data_sources.delete() issues GET /datasources?name=... (via retrieve_by_name),
    then DELETE /datasources/{id}.

    ``_delete_fluent_datasource`` looks up the datasource via
    ``self.data_sources.all()[name]`` (direct ``__getitem__``), which calls
    ``retrieve_by_name`` (by-name GET).  After resolving the datasource, it
    issues the DELETE by id.

    Three interactions are registered in total:
      1. GET /data-context-configuration   (context init)
      2. GET /datasources?name=...         (by-name -- DatasourceDict.__getitem__)
      3. DELETE /datasources/{id}          (primary contract under test)
    """
    headers = _session_headers()

    existing_ds_payload = {
        "id": EXISTING_DATASOURCE_ID,
        "type": "pandas",
        "name": DATASOURCE_NAME,
        "assets": [],
    }
    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test, access_token=PACT_DUMMY_ACCESS_TOKEN, description_suffix="delete-datasource"
    )

    # 2. GET /datasources?name=... (by-name -- DatasourceDict.__getitem__ -> retrieve_by_name)
    (
        pact_test.upon_receiving(
            "a request to fetch datasource by name before delete (client-driven)"
        )
        .given("the Pandas datasource exists for deletion")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(existing_ds_payload, min=1)},
            content_type="application/json",
        )
    )

    # 3. DELETE /datasources/{id} -- the primary contract under test
    (
        pact_test.upon_receiving("a request to delete a Pandas datasource by id (client-driven)")
        .given("the Pandas datasource exists for deletion")
        .with_request("DELETE", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .will_respond_with(204)
    )

    with pact_test.serve() as srv:
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )
        ctx.data_sources.delete(name=DATASOURCE_NAME)
