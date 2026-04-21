"""Client-driven Pact contract tests for validation definition and checkpoint CRUD.

Each test:
1. Registers the GET /data-context-configuration interaction via
   ``setup_data_context_config_interaction()``.
2. Registers resource-specific Pact interaction(s).
3. Constructs a ``CloudDataContext`` and exercises the Python client API
   inside the ``with pact_test.serve() as srv:`` block.
4. Asserts the client correctly parses the response.

URL patterns (V1 with workspace):
  /api/v1/organizations/{org_id}/workspaces/{ws_id}/validation-definitions
  /api/v1/organizations/{org_id}/workspaces/{ws_id}/checkpoints

Note on checkpoint.run():
  Testing checkpoint.run() API interactions is deferred to a multi-step
  workflow test (GX-2731) because it requires a fully configured datasource,
  suite, and validation definition to already exist.
"""

from __future__ import annotations

from typing import Final
from unittest.mock import patch

import pytest
from pact import Pact, match

import great_expectations as gx
from great_expectations import __version__ as ge_version
from tests.integration.cloud.rest_contracts.conftest import (
    EXISTING_ORGANIZATION_ID,
    EXISTING_WORKSPACE_ID,
    PACT_DUMMY_ACCESS_TOKEN,
    pact_session_headers,
    setup_data_context_config_interaction,
)

# ---------------------------------------------------------------------------
# Shared constants -- validation definitions
# ---------------------------------------------------------------------------

VALDEF_NAME: Final[str] = "my_contract_test_valdef"
EXISTING_VALDEF_ID: Final[str] = "ccccdddd-1234-4abc-8def-aabbccddeeff"

VALDEF_PATH: Final[str] = (
    f"/api/v1/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/validation-definitions"
)
VALDEF_BY_ID_PATH: Final[str] = f"{VALDEF_PATH}/{EXISTING_VALDEF_ID}"

# ---------------------------------------------------------------------------
# Shared constants -- checkpoints
# ---------------------------------------------------------------------------

CHECKPOINT_NAME: Final[str] = "my_contract_test_checkpoint"
EXISTING_CHECKPOINT_ID: Final[str] = "eeeeffff-5678-4cde-9fab-112233445566"

CHECKPOINTS_PATH: Final[str] = (
    f"/api/v1/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/checkpoints"
)
CHECKPOINT_BY_ID_PATH: Final[str] = f"{CHECKPOINTS_PATH}/{EXISTING_CHECKPOINT_ID}"

# ---------------------------------------------------------------------------
# Shared constants -- supporting resources for validation definition tests
# ---------------------------------------------------------------------------

EXISTING_DATASOURCE_ID: Final[str] = "aaaabbbb-0001-4abc-8def-112233445566"
EXISTING_ASSET_ID: Final[str] = "aaaabbbb-0002-4abc-8def-112233445566"
EXISTING_BATCH_DEF_ID: Final[str] = "aaaabbbb-0003-4abc-8def-112233445566"
EXISTING_SUITE_ID: Final[str] = "aaaabbbb-0004-4abc-8def-112233445566"

DATASOURCE_NAME: Final[str] = "my_valdef_test_datasource"
ASSET_NAME: Final[str] = "my_valdef_test_asset"
BATCH_DEF_NAME: Final[str] = "my_valdef_test_batch_def"
SUITE_NAME: Final[str] = "my_valdef_test_suite"

DATASOURCES_PATH: Final[str] = (
    f"/api/v2/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/datasources"
)
SUITES_PATH: Final[str] = (
    f"/api/v2/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/expectation-suites"
)

# ---------------------------------------------------------------------------
# Shared response payloads
# ---------------------------------------------------------------------------

# Minimal validation definition payload returned by the cloud API.
_VALDEF_RESPONSE: Final[dict] = {
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

# Datasource payload with one DataFrameAsset that has one BatchDefinition.
_DATASOURCE_WITH_ASSET_AND_BATCH_DEF: Final[dict] = {
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
                }
            ],
        }
    ],
}


# Suite payload (minimal) returned for the test suite.
# The ``meta.great_expectations_version`` value MUST match the installed GX
# version exactly.  The freshness check (``ExpectationSuite._is_fresh``)
# compares the locally-created suite object against the one deserialized from
# the cloud response.  A locally-created suite automatically stamps its meta
# with the real ``ge_version``, so the mock must return the same value or the
# equality check fails with ``ExpectationSuiteNotFreshError``.
_SUITE_RESPONSE: Final[dict] = {
    "id": EXISTING_SUITE_ID,
    "name": SUITE_NAME,
    "expectations": [],
    "meta": {"great_expectations_version": match.like(ge_version)},
    "notes": None,
}

# Minimal checkpoint payload returned by the cloud API.
_CHECKPOINT_RESPONSE: Final[dict] = {
    "id": EXISTING_CHECKPOINT_ID,
    "name": CHECKPOINT_NAME,
    "validation_definitions": [],
    "actions": [],
    "result_format": match.like("SUMMARY"),
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _session_headers() -> dict:
    """Return request headers matching what the Python client sends."""
    return pact_session_headers()


def _register_datasource_get_interactions(
    pact_test: Pact,
    headers: dict,
) -> None:
    """Register an interaction to retrieve an existing Pandas datasource by name.

    ``ctx.data_sources.get(name=...)`` calls ``retrieve_by_name`` which issues
    two identical GET requests (``has_key`` + actual fetch) to the same URL.
    Pact v3 reuses a single interaction for both.

    After retrieval the datasource is cached in ``CacheableDatasourceDict``,
    so subsequent freshness checks during validation definition serialization
    hit the cache and do NOT make additional HTTP calls.

    Interaction sequence:
      1. GET /datasources?name=...  (serves both has_key + fetch in retrieve_by_name)
    """
    response_body = {"data": match.each_like(_DATASOURCE_WITH_ASSET_AND_BATCH_DEF, min=1)}
    (
        pact_test.upon_receiving(
            "fetch existing datasource by name for valdef test (client-driven)"
        )
        .given("the datasource with asset and batch def exists for valdef test")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(response_body, content_type="application/json")
    )


def _register_suite_setup_interactions(
    pact_test: Pact,
    headers: dict,
) -> None:
    """Register interactions to create an ExpectationSuite.

    The factory ``has_key`` probe issues a GET ?name=... that returns an empty
    list.  The POST creates the suite.

    After the POST, ``SuiteFactory.add()`` calls ``self.get(name)`` to re-fetch
    the persisted suite, which would issue the same GET ?name=... but expects a
    *non-empty* response.  The pact v3 mock server matches by
    method/path/query -- not by provider state -- so it cannot serve two
    different responses for the same request.  The caller must patch
    ``SuiteFactory.get`` to avoid this extra GET.

    Interaction sequence:
      1. GET /expectation-suites?name=... (factory has_key probe -- empty list)
      2. POST /expectation-suites         (create the suite)
    """
    # 1. GET ?name=... -- serves factory has_key probe (empty -> suite absent)
    (
        pact_test.upon_receiving(
            "has_key probe for suite before add for valdef test (client-driven)"
        )
        .given("no expectation suite with this name exists for valdef test")
        .with_request("GET", SUITES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": SUITE_NAME})
        .will_respond_with(200)
        .with_body({"data": []}, content_type="application/json")
    )

    # 2. POST /expectation-suites
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
    response_body = {"data": match.like(_SUITE_RESPONSE)}
    (
        pact_test.upon_receiving("create expectation suite for valdef test (client-driven)")
        .given("no expectation suite with this name exists for valdef test")
        .with_request("POST", SUITES_PATH)
        .with_headers(headers)
        .with_body(request_body, content_type="application/vnd.api+json")
        .will_respond_with(201)
        .with_body(response_body, content_type="application/json")
    )


def _register_suite_freshness_interactions(
    pact_test: Pact,
    headers: dict,
    scenario_suffix: str,
) -> None:
    """Register the GET interaction that the suite's is_fresh() check makes.

    When the ValidationDefinition serializer calls suite.identifier_bundle(),
    it runs is_fresh() which calls store.get(key) with the suite id.
    This results in a GET /expectation-suites/{id} request.
    """
    suite_by_id_path = f"{SUITES_PATH}/{EXISTING_SUITE_ID}"
    response_body = {"data": match.like(_SUITE_RESPONSE)}
    (
        pact_test.upon_receiving(
            f"fetch suite by id for freshness check {scenario_suffix} (client-driven)"
        )
        .given("the expectation suite exists and is fresh for valdef test")
        .with_request("GET", suite_by_id_path)
        .with_headers(headers)
        .with_query_parameters({"name": SUITE_NAME})
        .will_respond_with(200)
        .with_body(response_body, content_type="application/json")
    )


# ---------------------------------------------------------------------------
# Validation definition tests
# ---------------------------------------------------------------------------


@pytest.mark.cloud
def test_add_validation_definition(pact_test: Pact) -> None:
    """context.validation_definitions.add() issues has_key probes then POST.

    Creating a ValidationDefinition requires a persisted BatchDefinition (with
    datasource + asset) and a persisted ExpectationSuite.

    The datasource is retrieved (not created) via ``ctx.data_sources.get()``,
    which calls ``retrieve_by_name`` -> ``GET /datasources?name=...``.  After
    retrieval the datasource is cached, so the freshness check during
    validation definition serialization hits the cache without additional
    HTTP calls.

    After the suite POST, ``SuiteFactory.add()`` re-fetches via ``self.get()``
    which issues the same GET ?name=... as the has_key probe but expects a
    different response.  The pact v3 mock server matches by
    method/path/query -- not by provider state -- so we patch the re-fetch.

    Full interaction sequence:
      1.  GET /data-context-configuration          (context init)
      2.  GET /datasources?name=...          (retrieve existing datasource -- cached afterward)
      3.  GET /expectation-suites?name=...   (factory has_key probe -- empty list)
      4.  POST /expectation-suites                 (create suite)
      5.  GET  /expectation-suites/{id}            (suite freshness check)
      6.  GET  /validation-definitions?name=... (factory has_key for valdef -- empty list)
      7.  POST /validation-definitions             (create)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="add-validation-definition",
    )

    # 2. Retrieve existing datasource (cached -- no freshness interaction needed)
    _register_datasource_get_interactions(pact_test=pact_test, headers=headers)

    # 3-4. Create expectation suite (has_key probe + POST; re-fetch is patched)
    _register_suite_setup_interactions(pact_test=pact_test, headers=headers)

    # 5. Suite freshness check (called during valdef serialization)
    _register_suite_freshness_interactions(
        pact_test=pact_test,
        headers=headers,
        scenario_suffix="before valdef add",
    )

    # 6. GET /validation-definitions?name=... -- factory has_key probe (empty list)
    (
        pact_test.upon_receiving(
            "has_key probe for validation definition before add (client-driven)"
        )
        .given("no validation definition with this name exists")
        .with_request("GET", VALDEF_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": VALDEF_NAME})
        .will_respond_with(200)
        .with_body({"data": []}, content_type="application/json")
    )

    # 7. POST /validation-definitions
    post_valdef_request_body: match.AbstractMatcher = match.like(
        {
            "data": match.like(
                {
                    "name": match.like(VALDEF_NAME),
                    "data": match.like(
                        {
                            "datasource": match.like(
                                {
                                    "name": match.like(DATASOURCE_NAME),
                                    "id": match.uuid(EXISTING_DATASOURCE_ID),
                                }
                            ),
                            "asset": match.like(
                                {
                                    "name": match.like(ASSET_NAME),
                                    "id": match.uuid(EXISTING_ASSET_ID),
                                }
                            ),
                            "batch_definition": match.like(
                                {
                                    "name": match.like(BATCH_DEF_NAME),
                                    "id": match.uuid(EXISTING_BATCH_DEF_ID),
                                }
                            ),
                        }
                    ),
                    "suite": match.like(
                        {
                            "name": match.like(SUITE_NAME),
                            "id": match.uuid(EXISTING_SUITE_ID),
                        }
                    ),
                }
            )
        }
    )
    post_valdef_response_body = {"data": match.like(_VALDEF_RESPONSE)}
    (
        pact_test.upon_receiving("a request to add a validation definition (client-driven)")
        .given("no validation definition with this name exists")
        .with_request("POST", VALDEF_PATH)
        .with_headers(headers)
        .with_body(post_valdef_request_body, content_type="application/vnd.api+json")
        .will_respond_with(201)
        .with_body(post_valdef_response_body, content_type="application/json")
    )

    # Build a mock suite for the patched SuiteFactory.get() re-fetch.
    # This avoids the pact v3 limitation where two interactions with the same
    # method/path/query cannot return different responses.
    from great_expectations.core.expectation_suite import ExpectationSuite

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

        # Retrieve the existing datasource + asset + batch definition
        datasource = ctx.data_sources.get(name=DATASOURCE_NAME)
        asset = datasource.get_asset(name=ASSET_NAME)
        batch_def = asset.get_batch_definition(name=BATCH_DEF_NAME)

        # Create the expectation suite (patch the post-creation re-fetch)
        with patch.object(
            type(ctx.suites),
            "get",
            return_value=refetched_suite,
        ):
            suite = ctx.suites.add(ExpectationSuite(name=SUITE_NAME))

        # Create the validation definition
        from great_expectations.core.validation_definition import ValidationDefinition

        val_def = ValidationDefinition(
            name=VALDEF_NAME,
            data=batch_def,
            suite=suite,
        )
        result = ctx.validation_definitions.add(val_def)

    assert result is not None
    assert result.name == VALDEF_NAME


@pytest.mark.cloud
def test_get_validation_definition_by_name(pact_test: Pact) -> None:
    """context.validation_definitions.get(name=...) issues has_key then GET.

    Deserializing the response triggers additional GETs for the datasource
    and suite.  The datasource uses ``retrieve_by_name`` (two identical GETs:
    ``has_key`` + actual get to the collection URL), so a single interaction
    serves that pair.  The suite is fetched by id+name via
    ``expectation_store.get(key)`` which hits ``GET /expectation-suites/{id}``.

    Full interaction sequence:
      1.  GET /data-context-configuration           (context init)
      2.  GET /validation-definitions?name=...      (serves factory has_key + store.get fetch)
      3.  GET /datasources?name=...          (serves datasource has_key + fetch in _decode_data)
      4.  GET /expectation-suites/{id}       (suite fetch by id in _decode_suite)
    """
    headers = _session_headers()

    datasource_by_name_response = {
        "data": match.each_like(_DATASOURCE_WITH_ASSET_AND_BATCH_DEF, min=1)
    }
    suite_by_id_path = f"{SUITES_PATH}/{EXISTING_SUITE_ID}"

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="get-validation-definition",
    )

    # 2. GET /validation-definitions?name=... -- serves factory has_key + store.get fetch
    (
        pact_test.upon_receiving("a request to get a validation definition by name (client-driven)")
        .given("a validation definition with this name exists")
        .with_request("GET", VALDEF_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": VALDEF_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(match.like(_VALDEF_RESPONSE), min=1)},
            content_type="application/json",
        )
    )

    # 3. GET /datasources?name=... -- serves both retrieve_by_name calls in _decode_data
    (
        pact_test.upon_receiving(
            "fetch datasource during validation definition deserialization (client-driven)"
        )
        .given("the datasource exists for validation definition get")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(datasource_by_name_response, content_type="application/json")
    )

    # 4. GET /expectation-suites/{id}?name=... -- suite fetch by id during _decode_suite
    (
        pact_test.upon_receiving(
            "fetch suite by id during validation definition deserialization (client-driven)"
        )
        .given("the expectation suite exists for validation definition get")
        .with_request("GET", suite_by_id_path)
        .with_headers(headers)
        .with_query_parameters({"name": SUITE_NAME})
        .will_respond_with(200)
        .with_body({"data": match.like(_SUITE_RESPONSE)}, content_type="application/json")
    )

    with pact_test.serve() as srv:
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )
        result = ctx.validation_definitions.get(name=VALDEF_NAME)

    assert result is not None
    assert result.name == VALDEF_NAME


@pytest.mark.cloud
def test_delete_validation_definition(pact_test: Pact) -> None:
    """context.validation_definitions.delete(name) fetches then DELETE /{id}.

    ``ValidationDefinitionFactory.delete`` first calls ``self.get(name)``
    to resolve the cloud id, then issues DELETE to the id-scoped URL.
    The get() step triggers suite and datasource deserialization.  The
    datasource uses ``retrieve_by_name`` (two identical GETs to the
    collection URL); the suite is fetched by id via
    ``expectation_store.get(key)`` -> ``GET /expectation-suites/{id}``.

    Full interaction sequence:
      1.  GET /data-context-configuration           (context init)
      2.  GET /validation-definitions?name=...      (serves factory has_key + store.get in get())
      3.  GET /datasources?name=...          (serves datasource has_key + fetch in _decode_data)
      4.  GET /expectation-suites/{id}       (suite fetch by id in _decode_suite)
      5.  DELETE /validation-definitions/{id}       (delete by id)
    """
    headers = _session_headers()

    datasource_by_name_response = {
        "data": match.each_like(_DATASOURCE_WITH_ASSET_AND_BATCH_DEF, min=1)
    }
    suite_by_id_path = f"{SUITES_PATH}/{EXISTING_SUITE_ID}"

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="delete-validation-definition",
    )

    # 2. GET /validation-definitions?name=... -- serves factory has_key + store.get in get()
    (
        pact_test.upon_receiving(
            "fetch validation definition by name to resolve id for delete (client-driven)"
        )
        .given("a validation definition with this name exists for deletion")
        .with_request("GET", VALDEF_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": VALDEF_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(match.like(_VALDEF_RESPONSE), min=1)},
            content_type="application/json",
        )
    )

    # 3. GET /datasources?name=... -- serves both retrieve_by_name calls in _decode_data
    (
        pact_test.upon_receiving(
            "fetch datasource during validation definition delete deserialization (client-driven)"
        )
        .given("the datasource exists for validation definition delete")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(datasource_by_name_response, content_type="application/json")
    )

    # 4. GET /expectation-suites/{id}?name=... -- suite fetch by id during _decode_suite
    (
        pact_test.upon_receiving(
            "fetch suite by id during validation definition delete deserialization (client-driven)"
        )
        .given("the expectation suite exists for validation definition delete")
        .with_request("GET", suite_by_id_path)
        .with_headers(headers)
        .with_query_parameters({"name": SUITE_NAME})
        .will_respond_with(200)
        .with_body({"data": match.like(_SUITE_RESPONSE)}, content_type="application/json")
    )

    # 5. DELETE /validation-definitions/{id}
    (
        pact_test.upon_receiving(
            "a request to delete a validation definition by id (client-driven)"
        )
        .given("a validation definition with this name exists for deletion")
        .with_request("DELETE", VALDEF_BY_ID_PATH)
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
        ctx.validation_definitions.delete(name=VALDEF_NAME)


# ---------------------------------------------------------------------------
# Checkpoint tests
#
# These tests use an empty validation_definitions list to avoid the cascading
# lookups required when deserializing ValidationDefinition objects.  Full
# workflow tests including checkpoint.run() are covered in GX-2731.
# ---------------------------------------------------------------------------


@pytest.mark.cloud
def test_add_checkpoint(pact_test: Pact) -> None:
    """context.checkpoints.add_or_update(checkpoint) exercises create-or-update.

    ``CheckpointFactory.add`` requires three ``GET /checkpoints?name=...``
    calls (has_key probes returning empty, then a post-POST re-fetch returning
    the checkpoint).  Pact v3 cannot serve different responses for the same
    request criteria, so we use ``add_or_update`` instead.  When the checkpoint
    already exists, the factory fetches it (has_key + get -- two identical GETs
    served by one interaction), then updates via ``checkpoint.save()``.

    The save path uses ``GET /checkpoints/{id}?name=...`` (a DIFFERENT URL
    that includes the id) for the update's existence check, so there is no
    conflict with the name-only GET.

    Full interaction sequence:
      1. GET /data-context-configuration              (context init)
      2. GET /checkpoints?name=...               (serves factory has_key + get in add_or_update)
      3. GET /checkpoints/{id}?name=...          (update existence check in _update)
      4. PUT /checkpoints/{id}                   (update the checkpoint)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="add-checkpoint",
    )

    # 2. GET /checkpoints?name=... -- serves factory has_key + store.get (checkpoint exists)
    (
        pact_test.upon_receiving("fetch checkpoint by name for add_or_update (client-driven)")
        .given("the checkpoint already exists for add_or_update")
        .with_request("GET", CHECKPOINTS_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": CHECKPOINT_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(match.like(_CHECKPOINT_RESPONSE), min=1)},
            content_type="application/json",
        )
    )

    # 3. GET /checkpoints/{id}?name=... (update existence check via _update -> _get)
    (
        pact_test.upon_receiving(
            "fetch checkpoint by id for update existence check (client-driven)"
        )
        .given("the checkpoint already exists for add_or_update")
        .with_request("GET", CHECKPOINT_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": CHECKPOINT_NAME})
        .will_respond_with(200)
        .with_body({"data": match.like(_CHECKPOINT_RESPONSE)}, content_type="application/json")
    )

    # 4. PUT /checkpoints/{id} (update)
    put_checkpoint_request_body: match.AbstractMatcher = match.like(
        {
            "data": match.like(
                {
                    "id": match.like(EXISTING_CHECKPOINT_ID),
                    "name": match.like(CHECKPOINT_NAME),
                    "validation_definitions": match.like([]),
                    "actions": match.like([]),
                    "result_format": match.like("SUMMARY"),
                }
            )
        }
    )
    (
        pact_test.upon_receiving("a request to update a checkpoint via PUT (client-driven)")
        .given("the checkpoint already exists for add_or_update")
        .with_request("PUT", CHECKPOINT_BY_ID_PATH)
        .with_headers(headers)
        .with_body(put_checkpoint_request_body, content_type="application/vnd.api+json")
        .will_respond_with(200)
        .with_body({"data": match.like(_CHECKPOINT_RESPONSE)}, content_type="application/json")
    )

    with pact_test.serve() as srv:
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )
        from great_expectations.checkpoint.checkpoint import Checkpoint

        checkpoint = Checkpoint(name=CHECKPOINT_NAME, validation_definitions=[])
        result = ctx.checkpoints.add_or_update(checkpoint)

    assert result is not None
    assert result.name == CHECKPOINT_NAME


@pytest.mark.cloud
def test_get_checkpoint_by_name(pact_test: Pact) -> None:
    """context.checkpoints.get(name=...) issues has_key then GET.

    Both the ``has_key`` probe and the actual ``store.get`` fetch issue
    identical GET requests; a single interaction serves both.

    Full interaction sequence:
      1. GET /data-context-configuration        (context init)
      2. GET /checkpoints?name=...              (serves factory has_key + store.get fetch)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="get-checkpoint",
    )

    # 2. GET /checkpoints?name=... -- serves both factory has_key and store.get fetch
    (
        pact_test.upon_receiving("a request to get a checkpoint by name (client-driven)")
        .given("a checkpoint with this name exists")
        .with_request("GET", CHECKPOINTS_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": CHECKPOINT_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(match.like(_CHECKPOINT_RESPONSE), min=1)},
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
        result = ctx.checkpoints.get(name=CHECKPOINT_NAME)

    assert result is not None
    assert result.name == CHECKPOINT_NAME


@pytest.mark.cloud
def test_delete_checkpoint(pact_test: Pact) -> None:
    """context.checkpoints.delete(name) fetches (has_key + get) then DELETE /{id}.

    ``CheckpointFactory.delete`` calls ``self.get(name)`` to resolve the cloud
    id before issuing DELETE.  The two GET requests (``has_key`` + actual get)
    are identical; a single interaction serves both.

    Full interaction sequence:
      1. GET /data-context-configuration        (context init)
      2. GET /checkpoints?name=...              (serves factory has_key + store.get)
      3. DELETE /checkpoints/{id}               (delete by id)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="delete-checkpoint",
    )

    # 2. GET /checkpoints?name=... -- serves both factory has_key and store.get
    (
        pact_test.upon_receiving(
            "fetch checkpoint by name to resolve id for delete (client-driven)"
        )
        .given("a checkpoint with this name exists for deletion")
        .with_request("GET", CHECKPOINTS_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": CHECKPOINT_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(match.like(_CHECKPOINT_RESPONSE), min=1)},
            content_type="application/json",
        )
    )

    # 3. DELETE /checkpoints/{id}
    (
        pact_test.upon_receiving("a request to delete a checkpoint by id (client-driven)")
        .given("a checkpoint with this name exists for deletion")
        .with_request("DELETE", CHECKPOINT_BY_ID_PATH)
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
        ctx.checkpoints.delete(name=CHECKPOINT_NAME)


# ---------------------------------------------------------------------------
# Validation definition update test
# ---------------------------------------------------------------------------


@pytest.mark.cloud
def test_update_validation_definition(pact_test: Pact) -> None:
    """validation_definition.save() issues a GET existence check then PUT.

    ``ValidationDefinition.save()`` calls ``store.update(key, self)`` which:
    1. GETs the validation definition by id+name to verify it exists (``_update``).
    2. Serializes the validation definition (triggering suite freshness check).
    3. PUTs the serialized payload to ``/validation-definitions/{id}``.

    To obtain a fully populated ``ValidationDefinition`` object with an id,
    we first retrieve it via ``ctx.validation_definitions.get(name=...)``.
    The get step triggers datasource and suite deserialization interactions.
    The suite freshness check during serialization (step 2) reuses the same
    ``GET /expectation-suites/{id}`` interaction registered for deserialization.

    Full interaction sequence:
      1.  GET /data-context-configuration           (context init)
      2.  GET /validation-definitions?name=...      (factory has_key + store.get)
      3.  GET /datasources?name=...                 (datasource deserialization)
      4.  GET /expectation-suites/{id}?name=...     (suite deserialization + freshness check)
      5.  GET /validation-definitions/{id}?name=... (existence check from _update)
      6.  PUT /validation-definitions/{id}          (update)
    """
    headers = _session_headers()
    suite_by_id_path = f"{SUITES_PATH}/{EXISTING_SUITE_ID}"

    datasource_by_name_response = {
        "data": match.each_like(_DATASOURCE_WITH_ASSET_AND_BATCH_DEF, min=1)
    }

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="update-validation-definition",
    )

    # 2. GET /validation-definitions?name=... -- serves factory has_key + store.get
    (
        pact_test.upon_receiving("fetch validation definition by name for update (client-driven)")
        .given("a validation definition exists for update")
        .with_request("GET", VALDEF_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": VALDEF_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(match.like(_VALDEF_RESPONSE), min=1)},
            content_type="application/json",
        )
    )

    # 3. GET /datasources?name=... -- datasource deserialization (cached afterward)
    (
        pact_test.upon_receiving(
            "fetch datasource during validation definition update deserialization (client-driven)"
        )
        .given("the datasource exists for validation definition update")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(datasource_by_name_response, content_type="application/json")
    )

    # 4. GET /expectation-suites/{id}?name=... -- suite deserialization AND freshness check
    #    One interaction serves both: the initial deserialization fetch and the
    #    is_fresh() call during serialization for the PUT.
    (
        pact_test.upon_receiving(
            "fetch suite by id during validation definition update (client-driven)"
        )
        .given("the expectation suite exists for validation definition update")
        .with_request("GET", suite_by_id_path)
        .with_headers(headers)
        .with_query_parameters({"name": SUITE_NAME})
        .will_respond_with(200)
        .with_body({"data": match.like(_SUITE_RESPONSE)}, content_type="application/json")
    )

    # 5. GET /validation-definitions/{id}?name=... -- existence check from store._update
    (
        pact_test.upon_receiving(
            "fetch validation definition by id for update existence check (client-driven)"
        )
        .given("a validation definition exists for update")
        .with_request("GET", VALDEF_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": VALDEF_NAME})
        .will_respond_with(200)
        .with_body({"data": match.like(_VALDEF_RESPONSE)}, content_type="application/json")
    )

    # 6. PUT /validation-definitions/{id} -- the actual update
    put_valdef_request_body: match.AbstractMatcher = match.like(
        {
            "data": match.like(
                {
                    "name": match.like(VALDEF_NAME),
                    "data": match.like(
                        {
                            "datasource": match.like(
                                {
                                    "name": match.like(DATASOURCE_NAME),
                                    "id": match.uuid(EXISTING_DATASOURCE_ID),
                                }
                            ),
                            "asset": match.like(
                                {
                                    "name": match.like(ASSET_NAME),
                                    "id": match.uuid(EXISTING_ASSET_ID),
                                }
                            ),
                            "batch_definition": match.like(
                                {
                                    "name": match.like(BATCH_DEF_NAME),
                                    "id": match.uuid(EXISTING_BATCH_DEF_ID),
                                }
                            ),
                        }
                    ),
                    "suite": match.like(
                        {
                            "name": match.like(SUITE_NAME),
                            "id": match.uuid(EXISTING_SUITE_ID),
                        }
                    ),
                }
            )
        }
    )
    put_valdef_response_body = {"data": match.like(_VALDEF_RESPONSE)}
    (
        pact_test.upon_receiving(
            "a request to update a validation definition via PUT (client-driven)"
        )
        .given("a validation definition exists for update")
        .with_request("PUT", VALDEF_BY_ID_PATH)
        .with_headers(headers)
        .with_body(put_valdef_request_body, content_type="application/vnd.api+json")
        .will_respond_with(200)
        .with_body(put_valdef_response_body, content_type="application/json")
    )

    with pact_test.serve() as srv:
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )

        # Retrieve the existing validation definition (populates id + dependencies)
        val_def = ctx.validation_definitions.get(name=VALDEF_NAME)

        # Update (save) the validation definition
        val_def.save()


# ---------------------------------------------------------------------------
# Checkpoint expectation parameters test
# ---------------------------------------------------------------------------


CHECKPOINT_EXPECTATION_PARAMS_PATH: Final[str] = f"{CHECKPOINT_BY_ID_PATH}/expectation-parameters"


@pytest.mark.cloud
def test_get_checkpoint_expectation_parameters(pact_test: Pact) -> None:
    """context.prepare_checkpoint_run() fetches expectation parameters.

    When a checkpoint has windowed expectations, ``CloudDataContext
    .prepare_checkpoint_run()`` issues a GET to
    ``/checkpoints/{id}/expectation-parameters`` to retrieve computed parameter
    values.  The response contains a ``data.expectation_parameters`` dict.

    This test patches ``_checkpoint_has_windowed_expectations`` to return True
    so the HTTP call is made without needing actual windowed expectations.

    Full interaction sequence:
      1.  GET /data-context-configuration                       (context init)
      2.  GET /checkpoints/{id}/expectation-parameters          (parameter fetch)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="get-checkpoint-expectation-parameters",
    )

    # 2. GET /checkpoints/{id}/expectation-parameters
    expectation_params_response: dict = {
        "data": match.like(
            {
                "expectation_parameters": match.like({}),
            }
        ),
    }
    (
        pact_test.upon_receiving(
            "a request to get checkpoint expectation parameters (client-driven)"
        )
        .given("a checkpoint with expectation parameters exists")
        .with_request("GET", CHECKPOINT_EXPECTATION_PARAMS_PATH)
        .with_query_parameters({"batch_definition_id": match.like(EXISTING_BATCH_DEF_ID)})
        .with_headers(headers)
        .will_respond_with(200)
        .with_body(expectation_params_response, content_type="application/json")
    )

    with pact_test.serve() as srv:
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )

        # Build a minimal checkpoint stand-in with the known ID
        from great_expectations.checkpoint.checkpoint import Checkpoint

        checkpoint = Checkpoint(name=CHECKPOINT_NAME, validation_definitions=[])
        checkpoint.id = EXISTING_CHECKPOINT_ID

        # Patch so the method proceeds to the HTTP call without needing
        # actual windowed expectations on the checkpoint.
        expectation_parameters: dict = {}
        with (
            patch.object(
                type(ctx),
                "_checkpoint_has_windowed_expectations",
                return_value=True,
            ),
            patch.object(
                type(ctx),
                "_distinct_batch_definition_ids",
                return_value={EXISTING_BATCH_DEF_ID},
            ),
        ):
            ctx.prepare_checkpoint_run(
                checkpoint=checkpoint,
                batch_parameters={},
                expectation_parameters=expectation_parameters,
            )
