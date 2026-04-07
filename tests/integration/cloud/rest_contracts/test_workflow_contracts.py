"""Client-driven Pact contract test for a multi-step GX Cloud workflow.

Exercises the full pipeline end-to-end through the Python client API:
  1. Retrieve an existing Pandas datasource (with DataFrameAsset + BatchDefinition)
  2. Add an ExpectationSuite
  3. Add a ValidationDefinition (linking batch_def + suite)
  4. Add a Checkpoint (linking validation_definitions)

This test verifies that the GX Python client generates correct API requests
for the complete resource creation workflow against the Mercury backend.

Design notes (Pact v3 constraints):
  The Pact v3 mock server matches interactions by method + path + query
  parameters.  It cannot serve different responses for two requests that
  share the same signature.  To avoid conflicts:

  - The datasource (with asset + batch definition) is RETRIEVED, not
    created, via ``ctx.data_sources.get()``.  Creating one from scratch
    would require multiple PUT + GET cycles to the same URL with evolving
    response bodies — a pattern Pact v3 cannot express.

  - ``SuiteFactory.get`` is patched after the suite POST to prevent a
    conflicting re-fetch (the ``has_key`` probe and the re-fetch hit the
    same URL but need empty vs non-empty responses).

  - The checkpoint uses ``add_or_update`` (which takes the "already exists"
    path) instead of ``add`` to avoid the same has_key / re-fetch conflict.

  Request body matchers for POST/PUT are intentionally omitted here because
  they are already validated by the individual CRUD contract tests.  This
  workflow test focuses on the *sequence* of interactions.

  Each ``_make_*_response()`` helper returns a **fresh** dict to avoid
  pact-python v3 Rust FFI issues with shared matcher objects across
  multiple interactions.

URL patterns:
  /api/v1/organizations/{org_id}/workspaces/{ws_id}/data-context-configuration
  /api/v2/organizations/{org_id}/workspaces/{ws_id}/datasources
  /api/v2/organizations/{org_id}/workspaces/{ws_id}/expectation-suites
  /api/v1/organizations/{org_id}/workspaces/{ws_id}/validation-definitions
  /api/v1/organizations/{org_id}/workspaces/{ws_id}/checkpoints
"""

from __future__ import annotations

from typing import Final
from unittest.mock import patch

import pytest
from pact import Pact, match

import great_expectations as gx
from great_expectations import __version__ as ge_version
from great_expectations.checkpoint.checkpoint import Checkpoint
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.core.http import create_session
from great_expectations.core.validation_definition import ValidationDefinition
from tests.integration.cloud.rest_contracts.conftest import (
    EXISTING_ORGANIZATION_ID,
    EXISTING_WORKSPACE_ID,
    PACT_DUMMY_ACCESS_TOKEN,
    setup_data_context_config_interaction,
)

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

# Datasource (pre-existing with asset + batch definition)
DATASOURCE_NAME: Final[str] = "workflow_test_datasource"
EXISTING_DATASOURCE_ID: Final[str] = "11111111-1111-4aaa-8aaa-111111111111"
ASSET_NAME: Final[str] = "workflow_test_asset"
EXISTING_ASSET_ID: Final[str] = "22222222-2222-4bbb-8bbb-222222222222"
BATCH_DEF_NAME: Final[str] = "workflow_test_batch_def"
EXISTING_BATCH_DEF_ID: Final[str] = "33333333-3333-4ccc-8ccc-333333333333"

# Expectation suite (created during test)
SUITE_NAME: Final[str] = "workflow_test_suite"
EXISTING_SUITE_ID: Final[str] = "44444444-4444-4ddd-8ddd-444444444444"

# Validation definition (created during test)
VALDEF_NAME: Final[str] = "workflow_test_valdef"
EXISTING_VALDEF_ID: Final[str] = "55555555-5555-4eee-8eee-555555555555"

# Checkpoint (uses add_or_update path — "already exists")
CHECKPOINT_NAME: Final[str] = "workflow_test_checkpoint"
EXISTING_CHECKPOINT_ID: Final[str] = "66666666-6666-4fff-8fff-666666666666"

# ---------------------------------------------------------------------------
# URL paths
# ---------------------------------------------------------------------------

DATASOURCES_PATH: Final[str] = (
    f"/api/v2/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/datasources"
)

SUITES_PATH: Final[str] = (
    f"/api/v2/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/expectation-suites"
)
SUITE_BY_ID_PATH: Final[str] = f"{SUITES_PATH}/{EXISTING_SUITE_ID}"

VALDEF_PATH: Final[str] = (
    f"/api/v1/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/validation-definitions"
)
CHECKPOINTS_PATH: Final[str] = (
    f"/api/v1/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/checkpoints"
)
CHECKPOINT_BY_ID_PATH: Final[str] = f"{CHECKPOINTS_PATH}/{EXISTING_CHECKPOINT_ID}"


# ---------------------------------------------------------------------------
# Response-body factories — each call returns a fresh dict to avoid
# pact-python v3 FFI issues with shared matcher objects.
# ---------------------------------------------------------------------------


def _make_datasource_response() -> dict:
    return {
        "id": EXISTING_DATASOURCE_ID,
        "type": "pandas",
        "name": DATASOURCE_NAME,
        "assets": [
            {
                "id": EXISTING_ASSET_ID,
                "type": "dataframe",
                "name": ASSET_NAME,
                "batch_definitions": [
                    {
                        "id": EXISTING_BATCH_DEF_ID,
                        "name": BATCH_DEF_NAME,
                        "partitioner": None,
                    }
                ],
            }
        ],
    }


def _make_suite_response() -> dict:
    return {
        "id": EXISTING_SUITE_ID,
        "name": SUITE_NAME,
        "expectations": [],
        "meta": {"great_expectations_version": match.like(ge_version)},
        "notes": None,
    }


def _make_valdef_response() -> dict:
    return {
        "id": EXISTING_VALDEF_ID,
        "name": VALDEF_NAME,
        "data": {
            "datasource": {
                "name": match.like(DATASOURCE_NAME),
                "id": EXISTING_DATASOURCE_ID,
            },
            "asset": {
                "name": match.like(ASSET_NAME),
                "id": EXISTING_ASSET_ID,
            },
            "batch_definition": {
                "name": match.like(BATCH_DEF_NAME),
                "id": EXISTING_BATCH_DEF_ID,
            },
        },
        "suite": {
            "name": match.like(SUITE_NAME),
            "id": EXISTING_SUITE_ID,
        },
    }


def _make_checkpoint_response() -> dict:
    return {
        "id": EXISTING_CHECKPOINT_ID,
        "name": CHECKPOINT_NAME,
        "validation_definitions": [],
        "actions": [],
        "result_format": match.like("SUMMARY"),
    }


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _session_headers() -> dict[str, str]:
    session = create_session(access_token=PACT_DUMMY_ACCESS_TOKEN)
    return {k: str(v) for k, v in session.headers.items()}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.cloud
def test_pandas_datasource_workflow(pact_test: Pact) -> None:
    """Multi-step workflow: retrieve datasource, add suite, add valdef, add checkpoint.

    Exercises the full GX Cloud resource creation pipeline through the Python
    client API.  All Pact interactions are registered up front, then the client
    code runs inside a single ``pact_test.serve()`` block.

    Interaction sequence:
      1.  GET /data-context-configuration            (context init)
      2.  GET /datasources?name=...                  (retrieve existing datasource)
      3.  GET /expectation-suites?name=...           (has_key probe — empty)
      4.  POST /expectation-suites                   (create suite)
      5.  GET /expectation-suites/{id}?name=...      (suite freshness check)
      6.  GET /validation-definitions?name=...       (has_key probe — empty)
      7.  POST /validation-definitions               (create valdef)
      8.  GET /checkpoints?name=...                  (fetch existing for add_or_update)
      9.  GET /checkpoints/{id}?name=...             (update existence check)
      10. PUT /checkpoints/{id}                      (update checkpoint)
    """
    headers = _session_headers()

    # -- 1. GET /data-context-configuration (context init) --
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="workflow",
    )

    # -- 2. GET /datasources?name=... (retrieve existing datasource) --
    # Serves both has_key + get in retrieve_by_name, AND all subsequent
    # freshness checks that call DatasourceDict[name].
    (
        pact_test.upon_receiving("retrieve existing datasource for workflow test (client-driven)")
        .given("a Pandas datasource with asset and batch definition exists")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(_make_datasource_response(), min=1)},
            content_type="application/json",
        )
    )

    # -- 3. GET /expectation-suites?name=... (has_key probe — empty) --
    (
        pact_test.upon_receiving("has_key probe for suite before add in workflow (client-driven)")
        .given("no expectation suite with this name exists for workflow test")
        .with_request("GET", SUITES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": SUITE_NAME})
        .will_respond_with(200)
        .with_body({"data": []}, content_type="application/json")
    )

    # -- 4. POST /expectation-suites (create suite) --
    (
        pact_test.upon_receiving("create expectation suite in workflow (client-driven)")
        .given("no expectation suite with this name exists for workflow test")
        .with_request("POST", SUITES_PATH)
        .with_headers(headers)
        .will_respond_with(201)
        .with_body(
            {"data": match.like(_make_suite_response())},
            content_type="application/json",
        )
    )

    # -- 5. GET /expectation-suites/{id}?name=... (suite freshness check) --
    # Reused by valdef serialization AND checkpoint serialization freshness checks.
    (
        pact_test.upon_receiving(
            "fetch suite by id for freshness check in workflow (client-driven)"
        )
        .given("the expectation suite exists for workflow freshness check")
        .with_request("GET", SUITE_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": SUITE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_make_suite_response())},
            content_type="application/json",
        )
    )

    # -- 6. GET /validation-definitions?name=... (has_key probe — empty) --
    (
        pact_test.upon_receiving("has_key probe for valdef before add in workflow (client-driven)")
        .given("no validation definition with this name exists for workflow test")
        .with_request("GET", VALDEF_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": VALDEF_NAME})
        .will_respond_with(200)
        .with_body({"data": []}, content_type="application/json")
    )

    # -- 7. POST /validation-definitions (create valdef) --
    (
        pact_test.upon_receiving("create validation definition in workflow (client-driven)")
        .given("no validation definition with this name exists for workflow test")
        .with_request("POST", VALDEF_PATH)
        .with_headers(headers)
        .will_respond_with(201)
        .with_body(
            {"data": match.like(_make_valdef_response())},
            content_type="application/json",
        )
    )

    # -- 8. GET /checkpoints?name=... (checkpoint exists for add_or_update) --
    # add_or_update's get() calls has_key + store.get; both identical GETs
    # are served by this single interaction.
    (
        pact_test.upon_receiving(
            "fetch checkpoint by name for add_or_update in workflow (client-driven)"
        )
        .given("the checkpoint already exists for workflow add_or_update")
        .with_request("GET", CHECKPOINTS_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": CHECKPOINT_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(match.like(_make_checkpoint_response()), min=1)},
            content_type="application/json",
        )
    )

    # -- 9. GET /checkpoints/{id}?name=... (update existence check) --
    (
        pact_test.upon_receiving(
            "fetch checkpoint by id for update existence check in workflow (client-driven)"
        )
        .given("the checkpoint already exists for workflow add_or_update")
        .with_request("GET", CHECKPOINT_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": CHECKPOINT_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_make_checkpoint_response())},
            content_type="application/json",
        )
    )

    # -- 10. PUT /checkpoints/{id} (update checkpoint) --
    (
        pact_test.upon_receiving("update checkpoint via PUT in workflow (client-driven)")
        .given("the checkpoint already exists for workflow add_or_update")
        .with_request("PUT", CHECKPOINT_BY_ID_PATH)
        .with_headers(headers)
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_make_checkpoint_response())},
            content_type="application/json",
        )
    )

    # -----------------------------------------------------------------------
    # Execute the workflow inside the Pact mock server
    # -----------------------------------------------------------------------

    # Build a mock suite for patching the post-creation re-fetch.
    refetched_suite = ExpectationSuite(name=SUITE_NAME)
    refetched_suite.id = EXISTING_SUITE_ID

    with pact_test.serve() as srv:
        # Step 1: Get context (triggers interaction #1)
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )

        # Step 2: Retrieve existing datasource + asset + batch definition
        # (triggers interaction #2)
        datasource = ctx.data_sources.get(name=DATASOURCE_NAME)
        asset = datasource.get_asset(name=ASSET_NAME)
        batch_def = asset.get_batch_definition(name=BATCH_DEF_NAME)

        # Step 3: Create expectation suite
        # (triggers interactions #3 + #4; re-fetch patched to avoid conflict)
        suite = ExpectationSuite(name=SUITE_NAME)
        with patch.object(
            type(ctx.suites),
            "get",
            return_value=refetched_suite,
        ):
            suite = ctx.suites.add(suite)

        # Step 4: Create validation definition
        # (triggers interactions #5 + #6 + #7; #2 reused for datasource freshness)
        val_def = ValidationDefinition(
            name=VALDEF_NAME,
            data=batch_def,
            suite=suite,
        )
        result_valdef = ctx.validation_definitions.add(val_def)

        # Step 5: Add checkpoint via add_or_update (triggers interactions #8 + #9 + #10)
        # Uses empty validation_definitions to avoid a Pact v3 conflict: the
        # _add_or_update_validation_definitions cascade would call
        # SuiteFactory.get(name=...) which hits the same GET /suites?name=...
        # endpoint as the has_key probe in step 3 — but needs a different response.
        # Individual valdef-checkpoint linking is covered by test_valdef_checkpoint_contracts.py.
        checkpoint = Checkpoint(
            name=CHECKPOINT_NAME,
            validation_definitions=[],
        )
        result_checkpoint = ctx.checkpoints.add_or_update(checkpoint)

    # -----------------------------------------------------------------------
    # Assertions
    # -----------------------------------------------------------------------
    assert datasource is not None
    assert datasource.name == DATASOURCE_NAME
    assert suite is not None
    assert suite.name == SUITE_NAME
    assert result_valdef is not None
    assert result_valdef.name == VALDEF_NAME
    assert result_checkpoint is not None
    assert result_checkpoint.name == CHECKPOINT_NAME
