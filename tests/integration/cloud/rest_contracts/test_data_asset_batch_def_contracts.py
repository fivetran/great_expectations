"""Client-driven Pact contract tests for data asset and batch definition CRUD.

Each test:
1. Registers the GET /data-context-configuration interaction via
   ``setup_data_context_config_interaction()``.
2. Retrieves an existing datasource via ``ctx.data_sources.get(name=...)``,
   which issues ``GET /datasources?name=...`` (no {id} in path).
3. Registers the asset / batch-definition-specific interaction(s).
4. Constructs a ``CloudDataContext`` and exercises the Python client API inside
   the ``with pact_test.serve() as srv:`` block.
5. Asserts the client correctly parses the response.

URL patterns:
  Datasources (V2): /api/v2/organizations/{org_id}/workspaces/{ws_id}/datasources
  Data assets are embedded in the datasource payload — no separate endpoint.
"""

from __future__ import annotations

import re
from typing import Final

import pytest
from pact import Pact, match

import great_expectations as gx
from great_expectations.core.partitioners import FileNamePartitionerDaily
from great_expectations.datasource.fluent import PandasDatasource
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

EXISTING_DATASOURCE_ID: Final[str] = "ccdd0011-5678-4cde-9fab-aabbccdd1122"
EXISTING_ASSET_ID: Final[str] = "aabb1234-5678-4abc-9def-112233445566"
EXISTING_BATCH_DEF_ID: Final[str] = "bbcc2345-6789-4bcd-aef0-223344556677"

DATASOURCE_NAME: Final[str] = "my_test_pandas_datasource"
DATAFRAME_ASSET_NAME: Final[str] = "my_dataframe_asset"
BATCH_DEFINITION_NAME: Final[str] = "my_whole_dataframe_batch_def"

DATASOURCES_PATH: Final[str] = (
    f"/api/v2/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/datasources"
)
DATASOURCE_BY_ID_PATH: Final[str] = f"{DATASOURCES_PATH}/{EXISTING_DATASOURCE_ID}"

DATA_ASSETS_PATH: Final[str] = (
    f"/api/v1/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/data-assets"
)
ASSET_BY_ID_PATH: Final[str] = f"{DATA_ASSETS_PATH}/{EXISTING_ASSET_ID}"

# CSV asset constants
CSV_ASSET_ID: Final[str] = "ccdd3456-789a-4bcd-aef0-aabbccddeeff"
CSV_ASSET_NAME: Final[str] = "my_csv_asset"
CSV_FILEPATH: Final[str] = "data.csv"
FILE_BD_DAILY_ID: Final[str] = "ddee4567-89ab-4cde-bfa1-bbccddeeff00"
FILE_BD_DAILY_NAME: Final[str] = "my_daily_file_batch_def"
FILE_REGEX: Final[str] = r"(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/.+\.csv"

# ---------------------------------------------------------------------------
# Shared response-body payloads
# ---------------------------------------------------------------------------

# Datasource with no assets (returned after initial POST)
_DATASOURCE_NO_ASSETS: Final[dict] = {
    "id": EXISTING_DATASOURCE_ID,
    "type": "pandas",
    "name": DATASOURCE_NAME,
    "assets": [],
}

# Datasource payload that includes a DataFrameAsset (no batch defs yet)
_DATASOURCE_WITH_DATAFRAME_ASSET: Final[dict] = {
    "id": EXISTING_DATASOURCE_ID,
    "type": "pandas",
    "name": DATASOURCE_NAME,
    "assets": [
        {
            "id": EXISTING_ASSET_ID,
            "type": "dataframe",
            "name": DATAFRAME_ASSET_NAME,
            "batch_definitions": [],
        }
    ],
}

# Datasource payload that includes a DataFrameAsset WITH a batch definition
_DATASOURCE_WITH_ASSET_AND_BATCH_DEF: Final[dict] = {
    "id": EXISTING_DATASOURCE_ID,
    "type": "pandas",
    "name": DATASOURCE_NAME,
    "assets": [
        {
            "id": EXISTING_ASSET_ID,
            "type": "dataframe",
            "name": DATAFRAME_ASSET_NAME,
            "batch_definitions": [
                {
                    "id": EXISTING_BATCH_DEF_ID,
                    "name": BATCH_DEFINITION_NAME,
                    "partitioner": None,
                }
            ],
        }
    ],
}

# Datasource payload with DataFrameAsset after batch definition removal
_DATASOURCE_WITH_ASSET_NO_BATCH_DEFS: Final[dict] = {
    "id": EXISTING_DATASOURCE_ID,
    "type": "pandas",
    "name": DATASOURCE_NAME,
    "assets": [
        {
            "id": EXISTING_ASSET_ID,
            "type": "dataframe",
            "name": DATAFRAME_ASSET_NAME,
            "batch_definitions": [],
        }
    ],
}

# Datasource payload with CSVAsset and no batch definitions
_DATASOURCE_WITH_CSV_NO_BATCH_DEFS: Final[dict] = {
    "id": EXISTING_DATASOURCE_ID,
    "type": "pandas",
    "name": DATASOURCE_NAME,
    "assets": [
        {
            "id": CSV_ASSET_ID,
            "type": "csv",
            "name": CSV_ASSET_NAME,
            "filepath_or_buffer": CSV_FILEPATH,
            "batch_definitions": [],
        }
    ],
}

# Datasource payload with CSVAsset and a daily file BatchDefinition
_DATASOURCE_WITH_CSV_AND_FILE_BD: Final[dict] = {
    "id": EXISTING_DATASOURCE_ID,
    "type": "pandas",
    "name": DATASOURCE_NAME,
    "assets": [
        {
            "id": CSV_ASSET_ID,
            "type": "csv",
            "name": CSV_ASSET_NAME,
            "filepath_or_buffer": CSV_FILEPATH,
            "batch_definitions": [
                {
                    "id": FILE_BD_DAILY_ID,
                    "name": FILE_BD_DAILY_NAME,
                    "partitioner": {
                        "regex": FILE_REGEX,
                        "param_names": ["year", "month", "day"],
                        "sort_ascending": True,
                    },
                }
            ],
        }
    ],
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
def test_add_dataframe_asset(pact_test: Pact) -> None:
    """add_dataframe_asset() issues PUT /datasources/{id} then GET /datasources/{id}?name=...

    Instead of creating a datasource (which would register two
    GET /datasources/{id}?name=... interactions — one post-POST and one
    post-PUT — causing a "multiple interactions found" conflict),
    we retrieve an existing datasource via ``ctx.data_sources.get()``.
    This uses ``GET /datasources?name=...`` (different path, no {id}),
    leaving only one ``GET /datasources/{id}?name=...`` interaction
    (the post-PUT refresh).

    Full interaction sequence:
      1. GET /data-context-configuration       (context init)
      2. GET /datasources?name=...             (retrieve existing datasource by name)
      3. PUT /datasources/{id}                 (update datasource with new DataFrameAsset)
      4. GET /datasources/{id}?name=...        (post-PUT refresh — primary contract)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="add-dataframe-asset",
    )

    # 2. GET /datasources?name=... (retrieve_by_name: serves both has_key and get calls)
    (
        pact_test.upon_receiving(
            "fetch datasource by name before adding DataFrameAsset (client-driven)"
        )
        .given("the Pandas datasource exists for asset test")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(_DATASOURCE_NO_ASSETS, min=1)},
            content_type="application/json",
        )
    )

    # 3. PUT /datasources/{id} — datasource now includes the DataFrameAsset
    (
        pact_test.upon_receiving("PUT datasource to add a DataFrameAsset (client-driven)")
        .given("the Pandas datasource exists and a DataFrameAsset is being added")
        .with_request("PUT", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_body(
            match.like(
                {
                    "data": match.like(
                        {
                            "id": match.like(EXISTING_DATASOURCE_ID),
                            "type": "pandas",
                            "name": match.like(DATASOURCE_NAME),
                            "assets": match.each_like(
                                {
                                    "type": "dataframe",
                                    "name": match.like(DATAFRAME_ASSET_NAME),
                                    "batch_metadata": match.like({}),
                                },
                                min=1,
                            ),
                        }
                    )
                }
            ),
            content_type="application/json",
        )
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_DATASOURCE_WITH_DATAFRAME_ASSET)},
            content_type="application/json",
        )
    )

    # 4. GET /datasources/{id}?name=... — post-PUT refresh
    (
        pact_test.upon_receiving(
            "fetch datasource by id after adding DataFrameAsset (client-driven)"
        )
        .given("the Pandas datasource now contains the DataFrameAsset")
        .with_request("GET", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_DATASOURCE_WITH_DATAFRAME_ASSET)},
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
        datasource = ctx.data_sources.get(name=DATASOURCE_NAME)
        assert isinstance(datasource, PandasDatasource)
        asset = datasource.add_dataframe_asset(name=DATAFRAME_ASSET_NAME)

    assert asset is not None
    assert asset.name == DATAFRAME_ASSET_NAME


@pytest.mark.cloud
def test_add_batch_definition_whole_dataframe(pact_test: Pact) -> None:
    """add_batch_definition_whole_dataframe() issues PUT + GET on an existing datasource.

    Instead of creating a datasource and adding an asset (which would
    register multiple conflicting GET /datasources/{id}?name=...
    interactions), we retrieve an existing datasource that already
    contains the DataFrameAsset via ``ctx.data_sources.get()``.
    ``get_asset()`` is a local lookup on the returned datasource object —
    no HTTP call.  This leaves only one ``GET /datasources/{id}?name=...``
    interaction (the post-PUT refresh after adding the batch definition).

    Full interaction sequence:
      1. GET /data-context-configuration       (context init)
      2. GET /datasources?name=...             (retrieve existing datasource with asset)
      3. PUT /datasources/{id}                 (add BatchDefinition to datasource)
      4. GET /datasources/{id}?name=...        (post-PUT refresh — primary contract)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="add-batch-definition",
    )

    # 2. GET /datasources?name=... (retrieve_by_name: serves both has_key and get calls)
    (
        pact_test.upon_receiving(
            "fetch datasource by name before adding batch definition (client-driven)"
        )
        .given("the Pandas datasource with DataFrameAsset exists for batch def test")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(_DATASOURCE_WITH_DATAFRAME_ASSET, min=1)},
            content_type="application/json",
        )
    )

    # 3. PUT /datasources/{id} — datasource now includes the BatchDefinition
    (
        pact_test.upon_receiving(
            "PUT datasource to add a whole-dataframe BatchDefinition (client-driven)"
        )
        .given("datasource exists and a BatchDefinition is being added")
        .with_request("PUT", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_body(
            match.like(
                {
                    "data": match.like(
                        {
                            "id": match.like(EXISTING_DATASOURCE_ID),
                            "type": "pandas",
                            "name": match.like(DATASOURCE_NAME),
                            "assets": match.each_like(
                                {
                                    "id": match.like(EXISTING_ASSET_ID),
                                    "type": "dataframe",
                                    "name": match.like(DATAFRAME_ASSET_NAME),
                                    "batch_definitions": match.each_like(
                                        {
                                            "name": match.like(BATCH_DEFINITION_NAME),
                                            "partitioner": match.like(None),
                                        },
                                        min=1,
                                    ),
                                },
                                min=1,
                            ),
                        }
                    )
                }
            ),
            content_type="application/json",
        )
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_DATASOURCE_WITH_ASSET_AND_BATCH_DEF)},
            content_type="application/json",
        )
    )

    # 4. GET /datasources/{id}?name=... — post-PUT refresh after adding batch definition
    (
        pact_test.upon_receiving(
            "fetch datasource by id after adding batch definition (client-driven)"
        )
        .given("datasource contains DataFrameAsset with a BatchDefinition")
        .with_request("GET", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_DATASOURCE_WITH_ASSET_AND_BATCH_DEF)},
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
        datasource = ctx.data_sources.get(name=DATASOURCE_NAME)
        assert isinstance(datasource, PandasDatasource)
        asset = datasource.get_asset(name=DATAFRAME_ASSET_NAME)
        batch_def = asset.add_batch_definition_whole_dataframe(name=BATCH_DEFINITION_NAME)

    assert batch_def is not None
    assert batch_def.name == BATCH_DEFINITION_NAME


@pytest.mark.cloud
def test_delete_dataframe_asset(pact_test: Pact) -> None:
    """delete_asset() issues DELETE /data-assets/{asset_id}.

    Full interaction sequence:
      1. GET /data-context-configuration       (context init)
      2. GET /datasources?name=...             (retrieve existing datasource with asset)
      3. DELETE /data-assets/{asset_id}         (delete the DataFrameAsset)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="delete-asset",
    )

    # 2. GET /datasources?name=... (retrieve datasource containing the DataFrameAsset)
    (
        pact_test.upon_receiving(
            "fetch datasource by name before deleting DataFrameAsset (client-driven)"
        )
        .given("the Pandas datasource with DataFrameAsset exists for delete asset test")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(_DATASOURCE_WITH_DATAFRAME_ASSET, min=1)},
            content_type="application/json",
        )
    )

    # 3. DELETE /data-assets/{asset_id}
    (
        pact_test.upon_receiving("DELETE a DataFrameAsset by id (client-driven)")
        .given("the DataFrameAsset exists for deletion")
        .with_request("DELETE", ASSET_BY_ID_PATH)
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
        datasource = ctx.data_sources.get(name=DATASOURCE_NAME)
        assert isinstance(datasource, PandasDatasource)
        datasource.delete_asset(name=DATAFRAME_ASSET_NAME)


@pytest.mark.cloud
def test_delete_batch_definition(pact_test: Pact) -> None:
    """delete_batch_definition() issues PUT /datasources/{id} with the batch def removed.

    The client calls ``asset.delete_batch_definition(name=...)``, which internally
    fetches the datasource (GET), removes the batch definition, updates via PUT,
    and re-fetches (GET).

    Full interaction sequence:
      1. GET /data-context-configuration       (context init)
      2. GET /datasources?name=...             (retrieve existing datasource with asset+bd)
      3. PUT /datasources/{id}                 (update with batch definition removed)
      4. GET /datasources/{id}?name=...        (post-PUT refresh)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="delete-batch-def",
    )

    # 2. GET /datasources?name=... (retrieve datasource with asset and batch def)
    (
        pact_test.upon_receiving(
            "fetch datasource by name before deleting batch definition (client-driven)"
        )
        .given("the Pandas datasource with asset and batch def exists for batch def deletion")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(_DATASOURCE_WITH_ASSET_AND_BATCH_DEF, min=1)},
            content_type="application/json",
        )
    )

    # 3. PUT /datasources/{id} — datasource with empty batch_definitions
    (
        pact_test.upon_receiving("PUT datasource to remove a BatchDefinition (client-driven)")
        .given("datasource exists and a BatchDefinition is being removed")
        .with_request("PUT", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_body(
            match.like(
                {
                    "data": match.like(
                        {
                            "id": match.like(EXISTING_DATASOURCE_ID),
                            "type": "pandas",
                            "name": match.like(DATASOURCE_NAME),
                            "assets": match.each_like(
                                {
                                    "id": match.like(EXISTING_ASSET_ID),
                                    "type": "dataframe",
                                    "name": match.like(DATAFRAME_ASSET_NAME),
                                },
                                min=1,
                            ),
                        }
                    )
                }
            ),
            content_type="application/json",
        )
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_DATASOURCE_WITH_ASSET_NO_BATCH_DEFS)},
            content_type="application/json",
        )
    )

    # 4. GET /datasources/{id}?name=... — post-PUT refresh after removing batch definition
    (
        pact_test.upon_receiving(
            "fetch datasource by id after removing batch definition (client-driven)"
        )
        .given("datasource contains DataFrameAsset after batch def removal")
        .with_request("GET", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_DATASOURCE_WITH_ASSET_NO_BATCH_DEFS)},
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
        datasource = ctx.data_sources.get(name=DATASOURCE_NAME)
        assert isinstance(datasource, PandasDatasource)
        asset = datasource.get_asset(name=DATAFRAME_ASSET_NAME)
        asset.delete_batch_definition(name=BATCH_DEFINITION_NAME)


@pytest.mark.cloud
def test_add_csv_batch_definition_daily(pact_test: Pact) -> None:
    """add_batch_definition_daily() on a CSVAsset issues PUT + GET with FileNamePartitionerDaily.

    This tests the ``FileNamePartitionerDaily`` schema which is fundamentally
    different from ``ColumnPartitioner``.

    Full interaction sequence:
      1. GET /data-context-configuration       (context init)
      2. GET /datasources?name=...             (retrieve existing datasource with CSVAsset)
      3. PUT /datasources/{id}                 (add daily file BatchDefinition)
      4. GET /datasources/{id}?name=...        (post-PUT refresh — primary contract)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="add-csv-daily-bd",
    )

    # 2. GET /datasources?name=... (retrieve datasource with CSVAsset)
    (
        pact_test.upon_receiving(
            "fetch datasource by name before adding daily file batch def (client-driven)"
        )
        .given("the Pandas datasource with CSVAsset exists for file batch def test")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(_DATASOURCE_WITH_CSV_NO_BATCH_DEFS, min=1)},
            content_type="application/json",
        )
    )

    # 3. PUT /datasources/{id} — datasource now includes daily file BatchDefinition
    (
        pact_test.upon_receiving(
            "PUT datasource to add a daily file BatchDefinition (client-driven)"
        )
        .given("Pandas datasource exists and a daily file BatchDefinition is being added")
        .with_request("PUT", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_body(
            match.like(
                {
                    "data": match.like(
                        {
                            "id": match.like(EXISTING_DATASOURCE_ID),
                            "type": "pandas",
                            "name": match.like(DATASOURCE_NAME),
                            "assets": match.each_like(
                                {
                                    "id": match.like(CSV_ASSET_ID),
                                    "type": "csv",
                                    "name": match.like(CSV_ASSET_NAME),
                                    "filepath_or_buffer": match.like(CSV_FILEPATH),
                                    "batch_definitions": match.each_like(
                                        {
                                            "name": match.like(FILE_BD_DAILY_NAME),
                                            "partitioner": match.like(
                                                {
                                                    "regex": match.like(FILE_REGEX),
                                                    "param_names": match.like(
                                                        ["year", "month", "day"]
                                                    ),
                                                }
                                            ),
                                        },
                                        min=1,
                                    ),
                                },
                                min=1,
                            ),
                        }
                    )
                }
            ),
            content_type="application/json",
        )
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_DATASOURCE_WITH_CSV_AND_FILE_BD)},
            content_type="application/json",
        )
    )

    # 4. GET /datasources/{id}?name=... — post-PUT refresh after adding daily batch def
    (
        pact_test.upon_receiving(
            "fetch datasource by id after adding daily file batch def (client-driven)"
        )
        .given("Pandas datasource contains CSVAsset with daily file BatchDefinition")
        .with_request("GET", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_DATASOURCE_WITH_CSV_AND_FILE_BD)},
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
        datasource = ctx.data_sources.get(name=DATASOURCE_NAME)
        assert isinstance(datasource, PandasDatasource)
        csv_asset = datasource.get_asset(name=CSV_ASSET_NAME)
        batch_def = csv_asset.add_batch_definition(
            name=FILE_BD_DAILY_NAME,
            partitioner=FileNamePartitionerDaily(
                regex=re.compile(FILE_REGEX),
                param_names=("year", "month", "day"),
            ),
        )

    assert batch_def is not None
    assert batch_def.name == FILE_BD_DAILY_NAME
