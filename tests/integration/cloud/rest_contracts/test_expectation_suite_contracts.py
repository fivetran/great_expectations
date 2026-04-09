"""Client-driven Pact contract tests for expectation suite CRUD.

Each test:
1. Registers the GET /data-context-configuration interaction via
   ``setup_data_context_config_interaction()``.
2. Registers expectation-suite-specific Pact interaction(s).
3. Constructs a ``CloudDataContext`` and exercises the Python client API
   inside the ``with pact_test.serve() as srv:`` block.
4. Asserts the client correctly parses the response.

URL pattern (V2):
  /api/v2/organizations/{org_id}/workspaces/{ws_id}/expectation-suites
"""

from __future__ import annotations

from typing import Final
from unittest.mock import patch

import pytest
from pact import Pact, match

import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.expectations.expectation_configuration import (
    ExpectationConfiguration,
)
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

SUITE_NAME: Final[str] = "my_contract_test_suite"
EXISTING_SUITE_ID: Final[str] = "aaaabbbb-1234-4abc-8def-112233445566"

SUITES_PATH: Final[str] = (
    f"/api/v2/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/expectation-suites"
)
SUITE_BY_ID_PATH: Final[str] = f"{SUITES_PATH}/{EXISTING_SUITE_ID}"

# ---------------------------------------------------------------------------
# Shared response-body payloads
# ---------------------------------------------------------------------------

# Minimal suite payload returned by the server (GET / POST response).
_SUITE_RESPONSE: Final[dict] = {
    "id": EXISTING_SUITE_ID,
    "name": SUITE_NAME,
    "expectations": [],
    "meta": {"great_expectations_version": match.like("1.0.0")},
    "notes": None,
}

# Suite payload that includes one expectation (used to validate round-trip).
_SUITE_WITH_EXPECTATION_RESPONSE: Final[dict] = {
    "id": EXISTING_SUITE_ID,
    "name": SUITE_NAME,
    "expectations": [
        {
            "id": match.uuid(),
            "type": "expect_table_row_count_to_be_between",
            "kwargs": {"min_value": 1, "max_value": 10},
            "meta": {},
            "severity": match.like("critical"),
        }
    ],
    "meta": {"great_expectations_version": match.like("1.0.0")},
    "notes": None,
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _session_headers() -> dict:
    return pact_session_headers()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.cloud
def test_add_expectation_suite(pact_test: Pact) -> None:
    """context.suites.add() issues GET (has_key probe) then POST.

    After POSTing, SuiteFactory.add() calls self.get(name) to re-fetch the
    persisted suite.  That re-fetch issues the same GET ?name=... request as
    the has_key probe but expects a *different* response (non-empty list).
    The pact v3 mock server matches by method/path/query -- not by provider
    state -- so it cannot serve two different responses for the same request.

    To work around this, we patch the post-creation re-fetch so only the
    has_key probe and POST contract are exercised against the mock server.
    The GET contract is already covered by test_get_expectation_suite_by_name.

    Full interaction sequence:
      1. GET /data-context-configuration   (context init)
      2. GET /expectation-suites?name=...  (has_key probe -- suite must not exist)
      3. POST /expectation-suites          (create the suite)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="add-expectation-suite",
    )

    # 2. GET /expectation-suites?name=... -- has_key probe (expect empty list -> suite absent)
    (
        pact_test.upon_receiving("has_key probe for expectation suite before add (client-driven)")
        .given("no expectation suite with this name exists")
        .with_request("GET", SUITES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": SUITE_NAME})
        .will_respond_with(200)
        .with_body({"data": []}, content_type="application/json")
    )

    # 3. POST /expectation-suites -- create the new suite
    request_body: match.AbstractMatcher = match.like(
        {
            "data": match.like(
                {
                    "name": match.like(SUITE_NAME),
                    "id": None,
                    "expectations": match.like([]),
                    "meta": match.like({"great_expectations_version": match.like("1.0.0")}),
                    "notes": None,
                }
            )
        }
    )
    (
        pact_test.upon_receiving("a request to add an expectation suite (client-driven)")
        .given("no expectation suite with this name exists")
        .with_request("POST", SUITES_PATH)
        .with_headers(headers)
        .with_body(request_body, content_type="application/vnd.api+json")
        .will_respond_with(201)
        .with_body({"data": match.like(_SUITE_RESPONSE)}, content_type="application/json")
    )

    # Patch the post-creation re-fetch: SuiteFactory.add() calls self.get(name)
    # after the POST.  We return a locally-built suite so no additional GET is
    # needed.  This avoids the pact v3 limitation where two interactions with
    # the same method/path/query cannot return different responses.
    refetched_suite = ExpectationSuite(name=SUITE_NAME)
    refetched_suite.id = EXISTING_SUITE_ID

    with pact_test.serve() as srv:
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )
        suite = ExpectationSuite(name=SUITE_NAME)
        with patch.object(
            type(ctx.suites),
            "get",
            return_value=refetched_suite,
        ):
            result = ctx.suites.add(suite)

    assert result is not None
    assert result.name == SUITE_NAME


@pytest.mark.cloud
def test_get_expectation_suite_by_name(pact_test: Pact) -> None:
    """context.suites.get(name=...) issues two identical GET?name=... requests.

    ``retrieve_by_name`` calls ``has_key`` (one GET) then ``get`` (a second
    GET) with identical request parameters.  Pact v3 reuses a single registered
    interaction for both requests.

    Two interactions are registered in total:
      1. GET /data-context-configuration   (context init)
      2. GET /expectation-suites?name=...  (serves both has_key and actual get)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="get-expectation-suite",
    )

    # 2. GET ?name=... -- serves both has_key probe and actual fetch
    (
        pact_test.upon_receiving("a request to get an expectation suite by name (client-driven)")
        .given("an expectation suite with this name exists")
        .with_request("GET", SUITES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": SUITE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(match.like(_SUITE_RESPONSE), min=1)},
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
        result = ctx.suites.get(name=SUITE_NAME)

    assert result is not None
    assert result.name == SUITE_NAME


@pytest.mark.cloud
def test_update_expectation_suite(pact_test: Pact) -> None:
    """suite.save() (update) issues GET (has_key + fetch), GET /{id}, then PUT /{id}.

    Updating a suite goes through ``add_or_update``, which first fetches the
    existing suite to resolve its id.  The two GET requests (``has_key`` probe
    + actual fetch) are identical so Pact v3 reuses a single interaction for
    both.  Then ``suite.save()`` triggers ``store.update()`` which calls
    ``_update`` on the cloud backend -- this performs a GET by id (to confirm
    the object exists) before issuing the PUT.

    Full interaction sequence:
      1. GET /data-context-configuration              (context init)
      2. GET /expectation-suites?name=...             (serves both has_key and fetch)
      3. GET /expectation-suites/{id}?name=...        (_update refresh before PUT)
      4. PUT /expectation-suites/{id}                 (update with new content)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="update-expectation-suite",
    )

    # 2. GET ?name=... -- serves both has_key probe and actual fetch
    (
        pact_test.upon_receiving(
            "a request to get an expectation suite by name before update (client-driven)"
        )
        .given("an expectation suite exists for update")
        .with_request("GET", SUITES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": SUITE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(match.like(_SUITE_WITH_EXPECTATION_RESPONSE), min=1)},
            content_type="application/json",
        )
    )

    # 3. GET /expectation-suites/{id}?name=... -- _update refresh before PUT
    (
        pact_test.upon_receiving(
            "a request to fetch expectation suite by id before update PUT (client-driven)"
        )
        .given("an expectation suite exists for update")
        .with_request("GET", SUITE_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": SUITE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_SUITE_WITH_EXPECTATION_RESPONSE)},
            content_type="application/json",
        )
    )

    # 4. PUT /expectation-suites/{id} -- write the updated suite
    put_request_body: match.AbstractMatcher = match.like(
        {
            "data": match.like(
                {
                    "name": match.like(SUITE_NAME),
                    "id": match.like(EXISTING_SUITE_ID),
                    "expectations": match.each_like(
                        {
                            "type": match.like("expect_table_row_count_to_be_between"),
                            "kwargs": match.like({"min_value": 1, "max_value": 10}),
                            "meta": match.like({}),
                            "severity": match.like("critical"),
                            "rendered_content": match.each_like(
                                {
                                    "name": match.like("atomic.prescriptive.summary"),
                                    "value": match.like(
                                        {
                                            "schema": match.like(
                                                {
                                                    "type": match.like(
                                                        "com.superconductive.rendered.string"
                                                    )
                                                }
                                            ),
                                            "template": match.like(
                                                "Must have greater than or equal to"
                                                " $min_value rows."
                                            ),
                                            "params": match.like(
                                                {
                                                    "min_value": match.like(
                                                        {
                                                            "schema": match.like(
                                                                {"type": match.like("number")}
                                                            ),
                                                            "value": match.like(1),
                                                        }
                                                    ),
                                                    "max_value": match.like(
                                                        {
                                                            "schema": match.like(
                                                                {"type": match.like("number")}
                                                            ),
                                                            "value": match.like(10),
                                                        }
                                                    ),
                                                }
                                            ),
                                        }
                                    ),
                                    "value_type": match.like("StringValueType"),
                                },
                                min=1,
                            ),
                        },
                        min=1,
                    ),
                    "meta": match.like({"great_expectations_version": match.like("1.0.0")}),
                    "notes": None,
                }
            )
        }
    )
    (
        pact_test.upon_receiving("a request to update an expectation suite via PUT (client-driven)")
        .given("an expectation suite exists for update")
        .with_request("PUT", SUITE_BY_ID_PATH)
        .with_headers(headers)
        .with_body(put_request_body, content_type="application/vnd.api+json")
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_SUITE_WITH_EXPECTATION_RESPONSE)},
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
        suite = ExpectationSuite(name=SUITE_NAME)
        cfg = ExpectationConfiguration(
            type="expect_table_row_count_to_be_between",
            kwargs={"min_value": 1, "max_value": 10},
        )
        suite.add_expectation_configuration(cfg)
        result = ctx.suites.add_or_update(suite)

    assert result is not None
    assert result.name == SUITE_NAME


@pytest.mark.cloud
def test_delete_expectation_suite(pact_test: Pact) -> None:
    """context.suites.delete(name) issues GET (has_key + fetch) then DELETE /{id}.

    ``SuiteFactory.delete`` first fetches the suite to resolve its cloud id,
    then issues DELETE to the id-scoped URL.  The two GET requests are
    identical so Pact v3 reuses a single interaction for both.

    Full interaction sequence:
      1. GET /data-context-configuration        (context init)
      2. GET /expectation-suites?name=...       (serves both has_key and fetch)
      3. DELETE /expectation-suites/{id}        (delete by id)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="delete-expectation-suite",
    )

    # 2. GET ?name=... -- serves both has_key probe and actual fetch
    (
        pact_test.upon_receiving(
            "a request to get an expectation suite by name before delete (client-driven)"
        )
        .given("an expectation suite exists for deletion")
        .with_request("GET", SUITES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": SUITE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(match.like(_SUITE_RESPONSE), min=1)},
            content_type="application/json",
        )
    )

    # 3. DELETE /expectation-suites/{id}
    (
        pact_test.upon_receiving("a request to delete an expectation suite by id (client-driven)")
        .given("an expectation suite exists for deletion")
        .with_request("DELETE", SUITE_BY_ID_PATH)
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
        ctx.suites.delete(name=SUITE_NAME)
