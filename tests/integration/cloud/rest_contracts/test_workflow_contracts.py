"""Client-driven Pact contract test for a multi-step GX Cloud workflow.

Exercises the full resource creation pipeline through the Python client API:
  1. Add a Pandas datasource  (``ctx.data_sources.add_pandas``)
  2. Add an ExpectationSuite  (``ctx.suites.add``)
  3. Add a ValidationDefinition (``ctx.validation_definitions.add``)
  4. Add a Checkpoint         (``ctx.checkpoints.add``)

The datasource is created via ``add_pandas`` and the mock returns a fully
configured datasource (with DataFrameAsset + BatchDefinition) in the POST
response.  The asset and batch definition are then available via local
lookup.  Individual PUT contracts for datasource mutation are covered by
``test_data_asset_batch_def_contracts.py``.

Each Pact interaction carries a distinct provider state so the provider
verification harness can set up the correct backend data for each step.

Design notes (Pact v3 mock server constraints):
  The mock server matches requests by HTTP method + path + query + headers +
  body.  When multiple interactions share the same HTTP signature, the mock
  returns the *first-registered* response for every matching request and
  marks all registered interactions as matched.

  This means the *pact contract file* records every interaction with its
  correct provider state for independent provider verification, while the
  *consumer test* receives a single consistent response per unique HTTP
  signature.  Where the client issues the same request at different
  lifecycle stages expecting different responses (e.g. a has_key probe
  returning empty, then a post-creation re-fetch returning non-empty),
  the later interactions are still recorded in the contract but the mock
  can only serve one response.

  ``SuiteFactory.get`` and ``CheckpointFactory._get`` are patched for
  post-creation re-fetches because the has_key probe and the re-fetch share
  an identical HTTP signature yet require opposite responses (empty vs
  non-empty).  This is the canonical pattern used by all individual CRUD
  contract tests in this directory.

  Each ``_make_*_response()`` helper returns a **fresh** dict to avoid
  pact-python v3 Rust FFI issues with shared matcher objects across
  interactions.

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

DATASOURCE_NAME: Final[str] = "workflow_test_datasource"
EXISTING_DATASOURCE_ID: Final[str] = "11111111-1111-4aaa-8aaa-111111111111"
ASSET_NAME: Final[str] = "workflow_test_asset"
EXISTING_ASSET_ID: Final[str] = "22222222-2222-4bbb-8bbb-222222222222"
BATCH_DEF_NAME: Final[str] = "workflow_test_batch_def"
EXISTING_BATCH_DEF_ID: Final[str] = "33333333-3333-4ccc-8ccc-333333333333"

SUITE_NAME: Final[str] = "workflow_test_suite"
EXISTING_SUITE_ID: Final[str] = "44444444-4444-4ddd-8ddd-444444444444"

VALDEF_NAME: Final[str] = "workflow_test_valdef"
EXISTING_VALDEF_ID: Final[str] = "55555555-5555-4eee-8eee-555555555555"

CHECKPOINT_NAME: Final[str] = "workflow_test_checkpoint"
EXISTING_CHECKPOINT_ID: Final[str] = "66666666-6666-4fff-8fff-666666666666"

# ---------------------------------------------------------------------------
# URL paths
# ---------------------------------------------------------------------------

DATASOURCES_PATH: Final[str] = (
    f"/api/v2/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/datasources"
)
DATASOURCE_BY_ID_PATH: Final[str] = f"{DATASOURCES_PATH}/{EXISTING_DATASOURCE_ID}"

SUITES_PATH: Final[str] = (
    f"/api/v2/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/expectation-suites"
)
SUITE_BY_ID_PATH: Final[str] = f"{SUITES_PATH}/{EXISTING_SUITE_ID}"

VALDEF_PATH: Final[str] = (
    f"/api/v1/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/validation-definitions"
)
VALDEF_BY_ID_PATH: Final[str] = f"{VALDEF_PATH}/{EXISTING_VALDEF_ID}"

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
    """Datasource with DataFrameAsset and BatchDefinition (final state)."""
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
        "validation_definitions": [
            {
                "id": EXISTING_VALDEF_ID,
                "name": match.like(VALDEF_NAME),
            }
        ],
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
    """Full workflow: add datasource → add suite → add valdef → add checkpoint.

    Exercises the complete GX Cloud resource creation pipeline through the
    Python client API.  All Pact interactions are registered up front, then
    the client code runs inside a single ``pact_test.serve()`` block.

    Each interaction carries a provider state describing the backend's data
    at that point in the pipeline.  The pact contract file records every
    interaction for independent provider verification.

    Interaction map (grouped by unique HTTP signature):

      Datasource lifecycle:
        GET  /datasources                     (list — empty before add)
        POST /datasources                     (create datasource)
        GET  /datasources/{id}?name=...       (post-creation refresh)
        GET  /datasources?name=...            (retrieve by name for freshness)

      Expectation suite lifecycle:
        GET  /expectation-suites?name=...     (has_key probe — empty)
        POST /expectation-suites              (create suite)
        GET  /expectation-suites?name=...     (re-fetch — non-empty) [provider state only]
        GET  /expectation-suites/{id}?name=.. (freshness check, reused)

      Validation definition lifecycle:
        GET  /validation-definitions?name=... (has_key probe — empty)
        POST /validation-definitions          (create valdef)

      Checkpoint lifecycle:
        GET  /checkpoints?name=...            (has_key probe — empty)
        POST /checkpoints                     (create checkpoint)
        GET  /checkpoints?name=...            (re-fetch — non-empty) [provider state only]
        GET  /validation-definitions/{id}?... (valdef freshness during request serialization)
    """
    headers = _session_headers()

    # ===================================================================
    # Register interactions — ordered by first occurrence in the workflow
    # ===================================================================

    # -- Context init --
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="workflow",
    )

    # -- Datasource: add_pandas --
    # GET /datasources (list — existence check before add)
    (
        pact_test.upon_receiving("list all datasources to check existence before add (workflow)")
        .given("no datasources exist yet")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .will_respond_with(200)
        .with_body({"data": []}, content_type="application/json")
    )

    # POST /datasources (create)
    # The mock returns a fully-configured datasource (with DataFrameAsset
    # + BatchDefinition) representing the provider state after creation.
    # The provider state handler sets up these child resources.
    (
        pact_test.upon_receiving("create Pandas datasource (workflow)")
        .given("the Pandas datasource is being created with asset and batch definition")
        .with_request("POST", DATASOURCES_PATH)
        .with_headers(headers)
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_make_datasource_response())},
            content_type="application/json",
        )
    )

    # GET /datasources/{id}?name=... (post-creation refresh)
    (
        pact_test.upon_receiving("refresh datasource by id after creation (workflow)")
        .given("the Pandas datasource exists with asset and batch definition")
        .with_request("GET", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_make_datasource_response())},
            content_type="application/json",
        )
    )

    # GET /datasources?name=... (retrieve by name)
    # Used by freshness checks during valdef/checkpoint serialization.
    (
        pact_test.upon_receiving("retrieve datasource by name for freshness check (workflow)")
        .given("the Pandas datasource exists with asset and batch definition")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(_make_datasource_response(), min=1)},
            content_type="application/json",
        )
    )

    # -- ExpectationSuite: suites.add --
    # GET /expectation-suites?name=... (has_key probe — empty)
    (
        pact_test.upon_receiving("has_key probe for suite before creation (workflow)")
        .given("no expectation suite with this name exists")
        .with_request("GET", SUITES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": SUITE_NAME})
        .will_respond_with(200)
        .with_body({"data": []}, content_type="application/json")
    )

    # POST /expectation-suites (create)
    (
        pact_test.upon_receiving("create expectation suite (workflow)")
        .given("no expectation suite with this name exists")
        .with_request("POST", SUITES_PATH)
        .with_headers(headers)
        .will_respond_with(201)
        .with_body(
            {"data": match.like(_make_suite_response())},
            content_type="application/json",
        )
    )

    # GET /expectation-suites?name=... (post-creation re-fetch — non-empty)
    # Recorded in the pact file for provider verification.  At the mock
    # level this shares a signature with the has_key probe above, so the
    # mock serves the first-registered (empty) response for all matching
    # calls.  SuiteFactory.get is patched in the test body to supply the
    # post-creation result locally.
    (
        pact_test.upon_receiving("re-fetch suite by name after creation (workflow)")
        .given("the expectation suite was just created")
        .with_request("GET", SUITES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": SUITE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(match.like(_make_suite_response()), min=1)},
            content_type="application/json",
        )
    )

    # GET /expectation-suites/{id}?name=... (freshness check — reused)
    (
        pact_test.upon_receiving("fetch suite by id for freshness check (workflow)")
        .given("the expectation suite exists for freshness check")
        .with_request("GET", SUITE_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": SUITE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_make_suite_response())},
            content_type="application/json",
        )
    )

    # -- ValidationDefinition: validation_definitions.add --
    # GET /validation-definitions?name=... (has_key probe — empty)
    (
        pact_test.upon_receiving("has_key probe for valdef before creation (workflow)")
        .given("no validation definition with this name exists")
        .with_request("GET", VALDEF_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": VALDEF_NAME})
        .will_respond_with(200)
        .with_body({"data": []}, content_type="application/json")
    )

    # POST /validation-definitions (create)
    (
        pact_test.upon_receiving("create validation definition (workflow)")
        .given("no validation definition with this name exists")
        .with_request("POST", VALDEF_PATH)
        .with_headers(headers)
        .will_respond_with(201)
        .with_body(
            {"data": match.like(_make_valdef_response())},
            content_type="application/json",
        )
    )

    # -- Checkpoint: checkpoints.add --
    # GET /checkpoints?name=... (has_key probe — empty)
    (
        pact_test.upon_receiving("has_key probe for checkpoint before creation (workflow)")
        .given("no checkpoint with this name exists")
        .with_request("GET", CHECKPOINTS_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": CHECKPOINT_NAME})
        .will_respond_with(200)
        .with_body({"data": []}, content_type="application/json")
    )

    # POST /checkpoints (create)
    (
        pact_test.upon_receiving("create checkpoint (workflow)")
        .given("no checkpoint with this name exists")
        .with_request("POST", CHECKPOINTS_PATH)
        .with_headers(headers)
        .will_respond_with(201)
        .with_body(
            {"data": match.like(_make_checkpoint_response())},
            content_type="application/json",
        )
    )

    # GET /checkpoints?name=... (post-creation re-fetch — non-empty)
    # Same provider-state pattern as the suite re-fetch above.
    (
        pact_test.upon_receiving("re-fetch checkpoint by name after creation (workflow)")
        .given("the checkpoint was just created")
        .with_request("GET", CHECKPOINTS_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": CHECKPOINT_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(match.like(_make_checkpoint_response()), min=1)},
            content_type="application/json",
        )
    )

    # GET /validation-definitions/{id}?name=... (freshness during ckpt request serialization)
    # Serializing the checkpoint request calls ValidationDefinition.identifier_bundle(),
    # which refreshes the validation definition via store.get.
    (
        pact_test.upon_receiving(
            "fetch valdef by id during checkpoint request serialization (workflow)"
        )
        .given("the validation definition exists for checkpoint request serialization")
        .with_request("GET", VALDEF_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": VALDEF_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_make_valdef_response())},
            content_type="application/json",
        )
    )

    # ===================================================================
    # Execute the workflow
    # ===================================================================

    # Pre-build objects for post-creation patches (see design notes above).
    refetched_suite = ExpectationSuite(name=SUITE_NAME)
    refetched_suite.id = EXISTING_SUITE_ID

    refetched_checkpoint = Checkpoint(name=CHECKPOINT_NAME, validation_definitions=[])
    refetched_checkpoint.id = EXISTING_CHECKPOINT_ID

    with pact_test.serve() as srv:
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )

        # Step 1: Add Pandas datasource
        # The mock returns a datasource with asset + batch definition already
        # configured, representing the provider's state after full setup.
        datasource = ctx.data_sources.add_pandas(name=DATASOURCE_NAME)
        asset = datasource.get_asset(name=ASSET_NAME)
        batch_def = asset.get_batch_definition(name=BATCH_DEF_NAME)

        # Step 2: Add ExpectationSuite
        suite = ExpectationSuite(name=SUITE_NAME)
        with patch.object(type(ctx.suites), "get", return_value=refetched_suite):
            suite = ctx.suites.add(suite)

        # Step 3: Add ValidationDefinition
        val_def = ValidationDefinition(
            name=VALDEF_NAME,
            data=batch_def,
            suite=suite,
        )
        result_valdef = ctx.validation_definitions.add(val_def)

        # Step 4: Add Checkpoint with the validation definition
        checkpoint = Checkpoint(
            name=CHECKPOINT_NAME,
            validation_definitions=[result_valdef],
        )
        with patch.object(type(ctx.checkpoints), "_get", return_value=refetched_checkpoint):
            result_checkpoint = ctx.checkpoints.add(checkpoint)

    # ===================================================================
    # Assertions
    # ===================================================================
    assert datasource is not None
    assert datasource.name == DATASOURCE_NAME
    assert asset is not None
    assert asset.name == ASSET_NAME
    assert batch_def is not None
    assert batch_def.name == BATCH_DEF_NAME
    assert suite is not None
    assert suite.name == SUITE_NAME
    assert result_valdef is not None
    assert result_valdef.name == VALDEF_NAME
    assert result_checkpoint is not None
    assert result_checkpoint.name == CHECKPOINT_NAME
