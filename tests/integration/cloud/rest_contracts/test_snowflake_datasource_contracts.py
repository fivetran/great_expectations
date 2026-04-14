"""Client-driven Pact contract tests for Snowflake datasource CRUD operations.

Tests ``SnowflakeDatasourceNoID`` / ``SnowflakeDatasourceWithID`` OpenAPI schemas
with all three connection string variants:
  1. DSN string  (``snowflake://user:password@account/database/schema?...``)
  2. ``ConnectionDetails``  (structured password-based connection)
  3. ``KeyPairConnectionDetails``  (private_key instead of password)

Each test:
1. Registers the GET /data-context-configuration interaction via
   ``setup_data_context_config_interaction()``.
2. Registers the Snowflake-datasource-specific interaction(s).
3. Constructs a ``CloudDataContext`` and exercises the Python client API inside
   the ``with pact_test.serve() as srv:`` block.
4. Asserts the client correctly parses the response.

URL pattern for datasources (V2 endpoint):
    /api/v2/organizations/{org_id}/workspaces/{workspace_id}/datasources
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final
from unittest.mock import patch

import pytest
from pact import Pact, match

if TYPE_CHECKING:
    import pytest_mock

import great_expectations as gx
from great_expectations.datasource.fluent.snowflake_datasource import (
    ConnectionDetails,
    KeyPairConnectionDetails,
    SnowflakeDatasource,
)
from great_expectations.datasource.fluent.sql_datasource import SQLDatasource
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

SF_DATASOURCE_ID: Final[str] = "aabb0033-1234-4abc-8def-ccddaabb3344"
SF_DATASOURCE_NAME: Final[str] = "my_test_snowflake_datasource"

# Variant 1: URL-style DSN string
SF_DSN: Final[str] = "snowflake://user:password@account/database/schema?warehouse=wh&role=role"

# Variant 2: Structured ConnectionDetails object (password-based)
SF_CONNECTION_DETAILS: Final[dict] = {
    "account": "myOrg-my_account",
    "user": "test_user",
    "password": "test_password",
    "database": "test_database",
    "schema": "public",
    "warehouse": "compute_wh",
    "role": "analyst",
}

# Variant 3: KeyPairConnectionDetails (private_key instead of password)
SF_KEY_PAIR_DETAILS: Final[dict] = {
    "account": "myOrg-my_account",
    "user": "test_user",
    "private_key": "MIIEvgIBADANBg...",
    "database": "test_database",
    "schema": "public",
    "warehouse": "compute_wh",
    "role": "analyst",
}

# Base path for the V2 datasources endpoint
DATASOURCES_PATH: Final[str] = (
    f"/api/v2/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/datasources"
)
DATASOURCE_BY_ID_PATH: Final[str] = f"{DATASOURCES_PATH}/{SF_DATASOURCE_ID}"

# ---------------------------------------------------------------------------
# Shared response body payloads
# ---------------------------------------------------------------------------

# Minimal response returned when the datasource list is empty
EMPTY_DATASOURCE_LIST_RESPONSE_BODY: Final[dict] = {
    "data": [],
}

_SF_DS_DSN: Final[dict] = {
    "id": SF_DATASOURCE_ID,
    "type": "snowflake",
    "name": SF_DATASOURCE_NAME,
    "connection_string": SF_DSN,
    "create_temp_table": False,
    "assets": [],
}

_SF_DS_DETAILS: Final[dict] = {
    "id": SF_DATASOURCE_ID,
    "type": "snowflake",
    "name": SF_DATASOURCE_NAME,
    "connection_string": SF_CONNECTION_DETAILS,
    "create_temp_table": False,
    "assets": [],
}

_SF_DS_KEY_PAIR: Final[dict] = {
    "id": SF_DATASOURCE_ID,
    "type": "snowflake",
    "name": SF_DATASOURCE_NAME,
    "connection_string": SF_KEY_PAIR_DETAILS,
    "create_temp_table": False,
    "assets": [],
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
def test_create_snowflake_datasource_with_dsn(
    pact_test: Pact, mocker: pytest_mock.MockerFixture
) -> None:
    """add_snowflake() with a DSN string issues GET /datasources (list),
    POST /datasources, then GET /datasources/{id}.

    Four interactions are registered in total:
      1. GET /data-context-configuration   (context init)
      2. GET /datasources                  (existence check before add)
      3. POST /datasources                 (primary contract under test)
      4. GET /datasources/{id}?name=...    (post-POST refresh in _persist_datasource)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration (required for context init)
    setup_data_context_config_interaction(
        pact_test, access_token=PACT_DUMMY_ACCESS_TOKEN, description_suffix="create-sf-dsn"
    )

    # 2. GET /datasources (list -- _add_fluent_datasource __contains__ check)
    (
        pact_test.upon_receiving(
            "a request to list datasources to check existence before add (snowflake DSN)"
        )
        .given("the Snowflake datasource does not exist (DSN)")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .will_respond_with(200)
        .with_body(EMPTY_DATASOURCE_LIST_RESPONSE_BODY, content_type="application/json")
    )

    # 3. POST /datasources (the primary contract under test)
    post_request_body: dict = {
        "data": match.like(
            {
                "type": match.like("snowflake"),
                "name": match.like(SF_DATASOURCE_NAME),
                "connection_string": match.like(SF_DSN),
            }
        )
    }
    post_response_body: dict = {
        "data": match.like(
            {
                "id": SF_DATASOURCE_ID,
                "type": match.like("snowflake"),
                "name": match.like(SF_DATASOURCE_NAME),
                "connection_string": match.like(SF_DSN),
                "create_temp_table": match.like(False),
                "assets": match.like([]),
            }
        )
    }
    (
        pact_test.upon_receiving("a request to add a Snowflake datasource with DSN (client-driven)")
        .given("the Snowflake datasource does not exist (DSN)")
        .with_request("POST", DATASOURCES_PATH)
        .with_headers(headers)
        .with_body(post_request_body, content_type="application/vnd.api+json")
        .will_respond_with(201)
        .with_body(post_response_body, content_type="application/json")
    )

    # 4. GET /datasources/{id}?name=... (_persist_datasource re-fetches with id + name)
    get_response_body: dict = {
        "data": match.like(
            {
                "id": match.uuid(),
                "type": match.like("snowflake"),
                "name": match.like(SF_DATASOURCE_NAME),
                "connection_string": match.like(SF_DSN),
                "create_temp_table": match.like(False),
                "assets": match.like([]),
            }
        )
    }
    (
        pact_test.upon_receiving(
            "a request to fetch the newly-created Snowflake datasource by id (DSN)"
        )
        .given("the Snowflake datasource was just created (DSN)")
        .with_request("GET", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": SF_DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(get_response_body, content_type="application/json")
    )

    with (
        patch.object(SQLDatasource, "_create_engine", return_value=mocker.MagicMock()),
        patch.object(SnowflakeDatasource, "test_connection"),
        pact_test.serve() as srv,
    ):
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )
        datasource = ctx.data_sources.add_snowflake(
            name=SF_DATASOURCE_NAME, connection_string=SF_DSN
        )

    assert datasource is not None
    assert datasource.name == SF_DATASOURCE_NAME


@pytest.mark.cloud
def test_create_snowflake_datasource_with_connection_details(
    pact_test: Pact, mocker: pytest_mock.MockerFixture
) -> None:
    """add_snowflake() with a ConnectionDetails object issues GET /datasources (list),
    POST /datasources, then GET /datasources/{id}.

    Four interactions are registered in total:
      1. GET /data-context-configuration   (context init)
      2. GET /datasources                  (existence check before add)
      3. POST /datasources                 (primary contract under test)
      4. GET /datasources/{id}?name=...    (post-POST refresh in _persist_datasource)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration (required for context init)
    setup_data_context_config_interaction(
        pact_test, access_token=PACT_DUMMY_ACCESS_TOKEN, description_suffix="create-sf-details"
    )

    # 2. GET /datasources (list -- _add_fluent_datasource __contains__ check)
    (
        pact_test.upon_receiving(
            "a request to list datasources to check existence"
            " before add (snowflake connection details)"
        )
        .given("the Snowflake datasource does not exist (connection details)")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .will_respond_with(200)
        .with_body(EMPTY_DATASOURCE_LIST_RESPONSE_BODY, content_type="application/json")
    )

    # 3. POST /datasources (the primary contract under test)
    post_request_body: dict = {
        "data": match.like(
            {
                "type": match.like("snowflake"),
                "name": match.like(SF_DATASOURCE_NAME),
                "connection_string": match.like(SF_CONNECTION_DETAILS),
            }
        )
    }
    post_response_body: dict = {
        "data": match.like(
            {
                "id": SF_DATASOURCE_ID,
                "type": match.like("snowflake"),
                "name": match.like(SF_DATASOURCE_NAME),
                "connection_string": match.like(SF_CONNECTION_DETAILS),
                "create_temp_table": match.like(False),
                "assets": match.like([]),
            }
        )
    }
    (
        pact_test.upon_receiving(
            "a request to add a Snowflake datasource with connection details (client-driven)"
        )
        .given("the Snowflake datasource does not exist (connection details)")
        .with_request("POST", DATASOURCES_PATH)
        .with_headers(headers)
        .with_body(post_request_body, content_type="application/vnd.api+json")
        .will_respond_with(201)
        .with_body(post_response_body, content_type="application/json")
    )

    # 4. GET /datasources/{id}?name=... (_persist_datasource re-fetches with id + name)
    get_response_body: dict = {
        "data": match.like(
            {
                "id": match.uuid(),
                "type": match.like("snowflake"),
                "name": match.like(SF_DATASOURCE_NAME),
                "connection_string": match.like(SF_CONNECTION_DETAILS),
                "create_temp_table": match.like(False),
                "assets": match.like([]),
            }
        )
    }
    (
        pact_test.upon_receiving(
            "a request to fetch the newly-created Snowflake datasource by id (connection details)"
        )
        .given("the Snowflake datasource was just created (connection details)")
        .with_request("GET", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": SF_DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(get_response_body, content_type="application/json")
    )

    with (
        patch.object(SQLDatasource, "_create_engine", return_value=mocker.MagicMock()),
        patch.object(SnowflakeDatasource, "test_connection"),
        pact_test.serve() as srv,
    ):
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )
        datasource = ctx.data_sources.add_snowflake(
            name=SF_DATASOURCE_NAME,
            connection_string=ConnectionDetails(**SF_CONNECTION_DETAILS),
        )

    assert datasource is not None
    assert datasource.name == SF_DATASOURCE_NAME


@pytest.mark.cloud
def test_create_snowflake_datasource_with_key_pair(
    pact_test: Pact, mocker: pytest_mock.MockerFixture
) -> None:
    """add_snowflake() with a KeyPairConnectionDetails object issues GET /datasources (list),
    POST /datasources, then GET /datasources/{id}.

    Four interactions are registered in total:
      1. GET /data-context-configuration   (context init)
      2. GET /datasources                  (existence check before add)
      3. POST /datasources                 (primary contract under test)
      4. GET /datasources/{id}?name=...    (post-POST refresh in _persist_datasource)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration (required for context init)
    setup_data_context_config_interaction(
        pact_test, access_token=PACT_DUMMY_ACCESS_TOKEN, description_suffix="create-sf-keypair"
    )

    # 2. GET /datasources (list -- _add_fluent_datasource __contains__ check)
    (
        pact_test.upon_receiving(
            "a request to list datasources to check existence before add (snowflake key pair)"
        )
        .given("the Snowflake datasource does not exist (key pair)")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .will_respond_with(200)
        .with_body(EMPTY_DATASOURCE_LIST_RESPONSE_BODY, content_type="application/json")
    )

    # 3. POST /datasources (the primary contract under test)
    post_request_body: dict = {
        "data": match.like(
            {
                "type": match.like("snowflake"),
                "name": match.like(SF_DATASOURCE_NAME),
                "connection_string": match.like(SF_KEY_PAIR_DETAILS),
            }
        )
    }
    post_response_body: dict = {
        "data": match.like(
            {
                "id": SF_DATASOURCE_ID,
                "type": match.like("snowflake"),
                "name": match.like(SF_DATASOURCE_NAME),
                "connection_string": match.like(SF_KEY_PAIR_DETAILS),
                "create_temp_table": match.like(False),
                "assets": match.like([]),
            }
        )
    }
    (
        pact_test.upon_receiving(
            "a request to add a Snowflake datasource with key pair (client-driven)"
        )
        .given("the Snowflake datasource does not exist (key pair)")
        .with_request("POST", DATASOURCES_PATH)
        .with_headers(headers)
        .with_body(post_request_body, content_type="application/vnd.api+json")
        .will_respond_with(201)
        .with_body(post_response_body, content_type="application/json")
    )

    # 4. GET /datasources/{id}?name=... (_persist_datasource re-fetches with id + name)
    get_response_body: dict = {
        "data": match.like(
            {
                "id": match.uuid(),
                "type": match.like("snowflake"),
                "name": match.like(SF_DATASOURCE_NAME),
                "connection_string": match.like(SF_KEY_PAIR_DETAILS),
                "create_temp_table": match.like(False),
                "assets": match.like([]),
            }
        )
    }
    (
        pact_test.upon_receiving(
            "a request to fetch the newly-created Snowflake datasource by id (key pair)"
        )
        .given("the Snowflake datasource was just created (key pair)")
        .with_request("GET", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": SF_DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(get_response_body, content_type="application/json")
    )

    with (
        patch.object(SQLDatasource, "_create_engine", return_value=mocker.MagicMock()),
        patch.object(SnowflakeDatasource, "test_connection"),
        pact_test.serve() as srv,
    ):
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )
        datasource = ctx.data_sources.add_snowflake(
            name=SF_DATASOURCE_NAME,
            connection_string=KeyPairConnectionDetails(**SF_KEY_PAIR_DETAILS),  # type: ignore[call-overload] # KeyPairConnectionDetails works at runtime
        )

    assert datasource is not None
    assert datasource.name == SF_DATASOURCE_NAME


@pytest.mark.cloud
def test_get_snowflake_datasource(pact_test: Pact, mocker: pytest_mock.MockerFixture) -> None:
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
        pact_test, access_token=PACT_DUMMY_ACCESS_TOKEN, description_suffix="get-sf"
    )

    # 2. GET /datasources?name=... (serves both has_key probe and actual get in retrieve_by_name)
    get_response_body: dict = {
        "data": match.each_like(
            {
                "id": match.uuid(),
                "type": match.like("snowflake"),
                "name": match.like(SF_DATASOURCE_NAME),
                "connection_string": match.like(SF_DSN),
                "create_temp_table": match.like(False),
                "assets": match.like([]),
            },
            min=1,
        )
    }
    (
        pact_test.upon_receiving(
            "a request to get the Snowflake datasource by name (client-driven)"
        )
        .given("the Snowflake datasource exists")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": SF_DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(get_response_body, content_type="application/json")
    )

    with (
        patch.object(SQLDatasource, "_create_engine", return_value=mocker.MagicMock()),
        patch.object(SnowflakeDatasource, "test_connection"),
        pact_test.serve() as srv,
    ):
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )
        datasource = ctx.data_sources.get(name=SF_DATASOURCE_NAME)

    assert datasource is not None
    assert datasource.name == SF_DATASOURCE_NAME
    assert isinstance(datasource, SnowflakeDatasource)
