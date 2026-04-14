"""Client-driven Pact contract tests for metric-run creation.

Each test:
1. Registers the GET /data-context-configuration interaction via
   ``setup_data_context_config_interaction()``.
2. Registers resource-specific Pact interaction(s).
3. Constructs a ``CloudDataContext`` and exercises the client API
   inside the ``with pact_test.serve() as srv:`` block.
4. Asserts the client correctly parses the response.

URL pattern:
    POST /api/v1/organizations/{org_id}/workspaces/{workspace_id}/metric-runs

NOTE: ``CloudDataStore.add()`` has no ``@public_api`` decorator (the
entire ``experimental/metric_repository`` module lacks one), so this
is the best available entry point for exercising the metric-runs
contract.
"""

from __future__ import annotations

import uuid
from typing import Final

import pytest
from pact import Pact, match

import great_expectations as gx
from great_expectations.experimental.metric_repository.cloud_data_store import (
    CloudDataStore,
)
from great_expectations.experimental.metric_repository.metrics import (
    MetricRun,
    TableMetric,
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

# The data asset that the metric run references — reuse an existing pact asset.
METRIC_RUN_DATA_ASSET_ID: Final[str] = "aaaabbbb-0002-4abc-8def-112233445566"

METRIC_RUNS_PATH: Final[str] = (
    f"/api/v1/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/metric-runs"
)

# ---------------------------------------------------------------------------
# Request body matcher
# ---------------------------------------------------------------------------

# The client sends {"data": {<MetricRun fields>}} via Payload.json().
# The metric dict includes @property fields (metric_type, value_type) from
# Metric.dict() override, plus standard fields (batch_id, metric_name, value,
# exception).
METRIC_RUN_REQUEST_BODY: Final[dict] = {
    "data": match.like(
        {
            "data_asset_id": match.uuid(METRIC_RUN_DATA_ASSET_ID),
            "metrics": match.each_like(
                {
                    "metric_type": match.like("TableMetric"),
                    "value_type": match.like("int"),
                    "batch_id": match.like("batch-1"),
                    "metric_name": match.like("table.row_count"),
                    "value": match.like(100),
                    "exception": None,
                },
                min=1,
            ),
        }
    ),
}

# ---------------------------------------------------------------------------
# Response body matcher
# ---------------------------------------------------------------------------

# The response is a direct object (NOT wrapped in {"data": ...}).
METRIC_RUN_RESPONSE_BODY: Final[dict] = {
    "id": match.uuid(),
    "data_asset_id": match.uuid(),
    "metrics": match.each_like(
        {
            "id": match.uuid(),
            "batch_id": match.like("batch-1"),
            "metric_name": match.like("table.row_count"),
            "value": match.like(100),
            "exception": None,
            "column": None,
            "created_at": match.like(None),
        },
        min=1,
    ),
    "last_fetched": match.like(None),
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.cloud
def test_create_metric_run(pact_test: Pact) -> None:
    """POST /metric-runs creates a metric run for a given data asset.

    The ``CloudDataStore.add()`` method serializes a ``MetricRun`` into
    ``{"data": {...}}`` and POSTs it.  The response returns the created
    metric run with server-generated IDs.

    Interaction sequence:
      1. GET /data-context-configuration  (context init)
      2. POST /metric-runs               (primary contract under test)
    """
    headers = pact_session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="create-metric-run",
    )

    # 2. POST /metric-runs
    (
        pact_test.upon_receiving("a request to create a metric run (client-driven)")
        .given("a data asset exists for metric run creation")
        .with_request("POST", METRIC_RUNS_PATH)
        .with_headers(headers)
        .with_body(METRIC_RUN_REQUEST_BODY, content_type="application/vnd.api+json")
        .will_respond_with(201)
        .with_body(METRIC_RUN_RESPONSE_BODY, content_type="application/json")
    )

    with pact_test.serve() as srv:
        ctx = gx.get_context(
            mode="cloud",
            cloud_base_url=str(srv.url),
            cloud_organization_id=EXISTING_ORGANIZATION_ID,
            cloud_workspace_id=EXISTING_WORKSPACE_ID,
            cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
        )

        store = CloudDataStore(context=ctx)

        metric_run = MetricRun(
            data_asset_id=uuid.UUID(METRIC_RUN_DATA_ASSET_ID),
            metrics=[
                TableMetric[int](
                    batch_id="batch-1",
                    metric_name="table.row_count",
                    value=100,
                    exception=None,
                ),
            ],
        )

        result_id = store.add(metric_run)

    assert result_id is not None
