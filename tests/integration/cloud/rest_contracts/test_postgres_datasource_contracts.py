"""Client-driven Pact contract tests for Postgres datasource operations.

Tests the ``PostgresDatasourceNoID`` / ``PostgresDatasourceWithID`` OpenAPI
schemas, including SQL-specific assets (TableAsset, QueryAsset) and column
partitioners (ColumnPartitionerYearly, ColumnPartitionerDaily).

Each test:
1. Registers the GET /data-context-configuration interaction via
   ``setup_data_context_config_interaction()``.
2. Registers Postgres-specific interaction(s) (create, get, add asset,
   add batch definition).
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
from great_expectations.datasource.fluent import PostgresDatasource
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

PG_DATASOURCE_ID: Final[str] = "ddee0022-6789-4def-afab-bbccddee2233"
PG_DATASOURCE_NAME: Final[str] = "my_test_postgres_datasource"
PG_CONNECTION_STRING: Final[str] = "postgresql+psycopg2://user:password@localhost:5432/test_db"

PG_TABLE_ASSET_ID: Final[str] = "eeff3456-789a-4cde-bef0-334455667788"
PG_TABLE_ASSET_NAME: Final[str] = "my_pg_table_asset"
PG_TABLE_NAME: Final[str] = "my_test_table"

PG_QUERY_ASSET_ID: Final[str] = "eeff4567-89ab-4def-cfa1-445566778899"
PG_QUERY_ASSET_NAME: Final[str] = "my_pg_query_asset"
PG_QUERY: Final[str] = "SELECT id, name FROM users WHERE active = true"

PG_YEARLY_BD_ID: Final[str] = "ffaa4567-89ab-4def-cfa0-445566778899"
PG_YEARLY_BD_NAME: Final[str] = "my_yearly_batch_def"
PG_DAILY_BD_ID: Final[str] = "ffbb5678-9abc-4ef0-dab1-556677889900"
PG_DAILY_BD_NAME: Final[str] = "my_daily_batch_def"
PARTITION_COLUMN: Final[str] = "created_at"

DATASOURCES_PATH: Final[str] = (
    f"/api/v2/organizations/{EXISTING_ORGANIZATION_ID}"
    f"/workspaces/{EXISTING_WORKSPACE_ID}/datasources"
)
DATASOURCE_BY_ID_PATH: Final[str] = f"{DATASOURCES_PATH}/{PG_DATASOURCE_ID}"

# ---------------------------------------------------------------------------
# Shared response-body payloads
# ---------------------------------------------------------------------------

# Postgres datasource with no assets
_PG_DS_NO_ASSETS: Final[dict] = {
    "id": PG_DATASOURCE_ID,
    "type": "postgres",
    "name": PG_DATASOURCE_NAME,
    "connection_string": PG_CONNECTION_STRING,
    "create_temp_table": False,
    "assets": [],
}

# Postgres datasource with a TableAsset (no batch defs yet)
_PG_DS_WITH_TABLE_ASSET: Final[dict] = {
    "id": PG_DATASOURCE_ID,
    "type": "postgres",
    "name": PG_DATASOURCE_NAME,
    "connection_string": PG_CONNECTION_STRING,
    "create_temp_table": False,
    "assets": [
        {
            "id": PG_TABLE_ASSET_ID,
            "type": "table",
            "name": PG_TABLE_ASSET_NAME,
            "table_name": PG_TABLE_NAME,
            "batch_metadata": {},
            "batch_definitions": [],
        }
    ],
}

# Postgres datasource with a QueryAsset (no batch defs yet)
_PG_DS_WITH_QUERY_ASSET: Final[dict] = {
    "id": PG_DATASOURCE_ID,
    "type": "postgres",
    "name": PG_DATASOURCE_NAME,
    "connection_string": PG_CONNECTION_STRING,
    "create_temp_table": False,
    "assets": [
        {
            "id": PG_QUERY_ASSET_ID,
            "type": "query",
            "name": PG_QUERY_ASSET_NAME,
            "query": PG_QUERY,
            "batch_definitions": [],
        }
    ],
}

# Postgres datasource with TableAsset and a yearly BatchDefinition
_PG_DS_WITH_TABLE_AND_YEARLY_BD: Final[dict] = {
    "id": PG_DATASOURCE_ID,
    "type": "postgres",
    "name": PG_DATASOURCE_NAME,
    "connection_string": PG_CONNECTION_STRING,
    "create_temp_table": False,
    "assets": [
        {
            "id": PG_TABLE_ASSET_ID,
            "type": "table",
            "name": PG_TABLE_ASSET_NAME,
            "table_name": PG_TABLE_NAME,
            "batch_definitions": [
                {
                    "id": PG_YEARLY_BD_ID,
                    "name": PG_YEARLY_BD_NAME,
                    "partitioner": {
                        "method_name": "partition_on_year",
                        "column_name": PARTITION_COLUMN,
                        "sort_ascending": True,
                    },
                }
            ],
        }
    ],
}

# Postgres datasource with TableAsset and a daily BatchDefinition
_PG_DS_WITH_TABLE_AND_DAILY_BD: Final[dict] = {
    "id": PG_DATASOURCE_ID,
    "type": "postgres",
    "name": PG_DATASOURCE_NAME,
    "connection_string": PG_CONNECTION_STRING,
    "create_temp_table": False,
    "assets": [
        {
            "id": PG_TABLE_ASSET_ID,
            "type": "table",
            "name": PG_TABLE_ASSET_NAME,
            "table_name": PG_TABLE_NAME,
            "batch_definitions": [
                {
                    "id": PG_DAILY_BD_ID,
                    "name": PG_DAILY_BD_NAME,
                    "partitioner": {
                        "method_name": "partition_on_year_and_month_and_day",
                        "column_name": PARTITION_COLUMN,
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
    """Return request headers matching what the Python client sends."""
    return pact_session_headers()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.cloud
def test_create_postgres_datasource(pact_test: Pact, mocker: pytest_mock.MockerFixture) -> None:
    """add_postgres() issues GET /datasources (list), POST /datasources, then GET /datasources/{id}.

    Four interactions are registered in total:
      1. GET /data-context-configuration   (context init)
      2. GET /datasources                  (existence check before add)
      3. POST /datasources                 (primary contract under test)
      4. GET /datasources/{id}?name=...    (post-POST refresh in _persist_datasource)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration (required for context init)
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="create-pg-datasource",
    )

    # 2. GET /datasources (list -- _add_fluent_datasource __contains__ check)
    (
        pact_test.upon_receiving(
            "a request to list datasources to check existence"
            " before adding Postgres (client-driven)"
        )
        .given("the Postgres datasource does not exist")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .will_respond_with(200)
        .with_body({"data": []}, content_type="application/json")
    )

    # 3. POST /datasources (the primary contract under test)
    post_request_body: Final[dict] = {
        "data": match.like(
            {
                "type": match.like("postgres"),
                "name": match.like(PG_DATASOURCE_NAME),
                "connection_string": match.like(PG_CONNECTION_STRING),
            }
        )
    }
    post_response_body = {
        "data": match.like(
            {
                "id": PG_DATASOURCE_ID,
                "type": match.like("postgres"),
                "name": match.like(PG_DATASOURCE_NAME),
                "connection_string": match.like(PG_CONNECTION_STRING),
                "create_temp_table": match.like(False),
                "assets": match.like([]),
            }
        )
    }
    (
        pact_test.upon_receiving("a request to add a Postgres datasource (client-driven)")
        .given("the Postgres datasource does not exist")
        .with_request("POST", DATASOURCES_PATH)
        .with_headers(headers)
        .with_body(post_request_body, content_type="application/vnd.api+json")
        .will_respond_with(201)
        .with_body(post_response_body, content_type="application/json")
    )

    # 4. GET /datasources/{id}?name=... (_persist_datasource re-fetches with id + name)
    single_ds_response = {
        "data": match.like(
            {
                "id": match.uuid(),
                "type": match.like("postgres"),
                "name": match.like(PG_DATASOURCE_NAME),
                "connection_string": match.like(PG_CONNECTION_STRING),
                "create_temp_table": match.like(False),
                "assets": match.like([]),
            }
        )
    }
    (
        pact_test.upon_receiving(
            "a request to fetch the newly-created Postgres datasource by id (client-driven)"
        )
        .given("the Postgres datasource was just created")
        .with_request("GET", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": PG_DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(single_ds_response, content_type="application/json")
    )

    with patch.object(SQLDatasource, "_create_engine", return_value=mocker.MagicMock()):
        with pact_test.serve() as srv:
            ctx = gx.get_context(
                mode="cloud",
                cloud_base_url=str(srv.url),
                cloud_organization_id=EXISTING_ORGANIZATION_ID,
                cloud_workspace_id=EXISTING_WORKSPACE_ID,
                cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
            )
            datasource = ctx.data_sources.add_postgres(
                name=PG_DATASOURCE_NAME, connection_string=PG_CONNECTION_STRING
            )

    assert datasource is not None
    assert datasource.name == PG_DATASOURCE_NAME


@pytest.mark.cloud
def test_get_postgres_datasource(pact_test: Pact, mocker: pytest_mock.MockerFixture) -> None:
    """data_sources.get() issues GET /datasources?name=... via retrieve_by_name.

    Two interactions are registered in total:
      1. GET /data-context-configuration   (context init)
      2. GET /datasources?name=...         (serves both has_key and get calls)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration (required for context init)
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="get-pg-datasource",
    )

    # 2. GET /datasources?name=...
    get_response_body = {
        "data": match.each_like(
            {
                "id": match.uuid(),
                "type": match.like("postgres"),
                "name": match.like(PG_DATASOURCE_NAME),
                "connection_string": match.like(PG_CONNECTION_STRING),
                "create_temp_table": match.like(False),
                "assets": match.like([]),
            },
            min=1,
        )
    }
    (
        pact_test.upon_receiving("a request to get the Postgres datasource by name (client-driven)")
        .given("the Postgres datasource exists")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": PG_DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(get_response_body, content_type="application/json")
    )

    with patch.object(SQLDatasource, "_create_engine", return_value=mocker.MagicMock()):
        with pact_test.serve() as srv:
            ctx = gx.get_context(
                mode="cloud",
                cloud_base_url=str(srv.url),
                cloud_organization_id=EXISTING_ORGANIZATION_ID,
                cloud_workspace_id=EXISTING_WORKSPACE_ID,
                cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
            )
            datasource = ctx.data_sources.get(name=PG_DATASOURCE_NAME)

    assert datasource is not None
    assert isinstance(datasource, PostgresDatasource)
    assert datasource.name == PG_DATASOURCE_NAME


@pytest.mark.cloud
def test_add_table_asset_to_postgres(pact_test: Pact, mocker: pytest_mock.MockerFixture) -> None:
    """add_table_asset() issues PUT /datasources/{id} then GET /datasources/{id}?name=...

    Full interaction sequence:
      1. GET /data-context-configuration       (context init)
      2. GET /datasources?name=...             (retrieve existing datasource by name)
      3. PUT /datasources/{id}                 (update datasource with new TableAsset)
      4. GET /datasources/{id}?name=...        (post-PUT refresh)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="add-pg-table-asset",
    )

    # 2. GET /datasources?name=... (retrieve_by_name: serves both has_key and get calls)
    (
        pact_test.upon_receiving(
            "fetch Postgres datasource by name before adding TableAsset (client-driven)"
        )
        .given("the Postgres datasource exists for table asset test")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": PG_DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(_PG_DS_NO_ASSETS, min=1)},
            content_type="application/json",
        )
    )

    # 3. PUT /datasources/{id} -- datasource now includes the TableAsset
    (
        pact_test.upon_receiving("PUT Postgres datasource to add a TableAsset (client-driven)")
        .given("the Postgres datasource exists and a TableAsset is being added")
        .with_request("PUT", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_body(
            match.like(
                {
                    "data": match.like(
                        {
                            "id": match.like(PG_DATASOURCE_ID),
                            "type": "postgres",
                            "name": match.like(PG_DATASOURCE_NAME),
                            "connection_string": match.like(PG_CONNECTION_STRING),
                            "create_temp_table": match.like(False),
                            "assets": match.each_like(
                                {
                                    "type": "table",
                                    "name": match.like(PG_TABLE_ASSET_NAME),
                                    "table_name": match.like(PG_TABLE_NAME),
                                    "batch_metadata": match.like({}),
                                },
                                min=1,
                            ),
                        }
                    )
                }
            ),
            content_type="application/vnd.api+json",
        )
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_PG_DS_WITH_TABLE_ASSET)},
            content_type="application/json",
        )
    )

    # 4. GET /datasources/{id}?name=... -- post-PUT refresh
    (
        pact_test.upon_receiving(
            "fetch Postgres datasource by id after adding TableAsset (client-driven)"
        )
        .given("the Postgres datasource now contains the TableAsset")
        .with_request("GET", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": PG_DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_PG_DS_WITH_TABLE_ASSET)},
            content_type="application/json",
        )
    )

    with patch.object(SQLDatasource, "_create_engine", return_value=mocker.MagicMock()):
        with pact_test.serve() as srv:
            ctx = gx.get_context(
                mode="cloud",
                cloud_base_url=str(srv.url),
                cloud_organization_id=EXISTING_ORGANIZATION_ID,
                cloud_workspace_id=EXISTING_WORKSPACE_ID,
                cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
            )
            datasource = ctx.data_sources.get(name=PG_DATASOURCE_NAME)
            assert isinstance(datasource, PostgresDatasource)
            asset = datasource.add_table_asset(name=PG_TABLE_ASSET_NAME, table_name=PG_TABLE_NAME)

    assert asset is not None
    assert asset.name == PG_TABLE_ASSET_NAME


@pytest.mark.cloud
def test_add_query_asset_to_postgres(pact_test: Pact, mocker: pytest_mock.MockerFixture) -> None:
    """add_query_asset() issues PUT /datasources/{id} then GET /datasources/{id}?name=...

    Full interaction sequence:
      1. GET /data-context-configuration       (context init)
      2. GET /datasources?name=...             (retrieve existing datasource by name)
      3. PUT /datasources/{id}                 (update datasource with new QueryAsset)
      4. GET /datasources/{id}?name=...        (post-PUT refresh)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="add-pg-query-asset",
    )

    # 2. GET /datasources?name=... (retrieve_by_name: serves both has_key and get calls)
    (
        pact_test.upon_receiving(
            "fetch Postgres datasource by name before adding QueryAsset (client-driven)"
        )
        .given("the Postgres datasource exists for query asset test")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": PG_DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(_PG_DS_NO_ASSETS, min=1)},
            content_type="application/json",
        )
    )

    # 3. PUT /datasources/{id} -- datasource now includes the QueryAsset
    (
        pact_test.upon_receiving("PUT Postgres datasource to add a QueryAsset (client-driven)")
        .given("the Postgres datasource exists and a QueryAsset is being added")
        .with_request("PUT", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_body(
            match.like(
                {
                    "data": match.like(
                        {
                            "id": match.like(PG_DATASOURCE_ID),
                            "type": "postgres",
                            "name": match.like(PG_DATASOURCE_NAME),
                            "connection_string": match.like(PG_CONNECTION_STRING),
                            "create_temp_table": match.like(False),
                            "assets": match.each_like(
                                {
                                    "type": "query",
                                    "name": match.like(PG_QUERY_ASSET_NAME),
                                    "query": match.like(PG_QUERY),
                                    "batch_metadata": match.like({}),
                                },
                                min=1,
                            ),
                        }
                    )
                }
            ),
            content_type="application/vnd.api+json",
        )
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_PG_DS_WITH_QUERY_ASSET)},
            content_type="application/json",
        )
    )

    # 4. GET /datasources/{id}?name=... -- post-PUT refresh
    (
        pact_test.upon_receiving(
            "fetch Postgres datasource by id after adding QueryAsset (client-driven)"
        )
        .given("the Postgres datasource now contains the QueryAsset")
        .with_request("GET", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": PG_DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_PG_DS_WITH_QUERY_ASSET)},
            content_type="application/json",
        )
    )

    with patch.object(SQLDatasource, "_create_engine", return_value=mocker.MagicMock()):
        with pact_test.serve() as srv:
            ctx = gx.get_context(
                mode="cloud",
                cloud_base_url=str(srv.url),
                cloud_organization_id=EXISTING_ORGANIZATION_ID,
                cloud_workspace_id=EXISTING_WORKSPACE_ID,
                cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
            )
            datasource = ctx.data_sources.get(name=PG_DATASOURCE_NAME)
            assert isinstance(datasource, PostgresDatasource)
            asset = datasource.add_query_asset(name=PG_QUERY_ASSET_NAME, query=PG_QUERY)

    assert asset is not None
    assert asset.name == PG_QUERY_ASSET_NAME


@pytest.mark.cloud
def test_add_batch_definition_yearly(pact_test: Pact, mocker: pytest_mock.MockerFixture) -> None:
    """add_batch_definition_yearly() issues PUT /datasources/{id}
    then GET /datasources/{id}?name=...

    Full interaction sequence:
      1. GET /data-context-configuration       (context init)
      2. GET /datasources?name=...             (retrieve existing datasource with TableAsset)
      3. PUT /datasources/{id}                 (add yearly BatchDefinition to TableAsset)
      4. GET /datasources/{id}?name=...        (post-PUT refresh)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="add-pg-yearly-bd",
    )

    # 2. GET /datasources?name=... (retrieve_by_name: serves both has_key and get calls)
    (
        pact_test.upon_receiving(
            "fetch Postgres datasource by name before adding yearly batch def (client-driven)"
        )
        .given("the Postgres datasource with TableAsset exists for yearly batch def test")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": PG_DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(_PG_DS_WITH_TABLE_ASSET, min=1)},
            content_type="application/json",
        )
    )

    # 3. PUT /datasources/{id} -- datasource now includes the yearly BatchDefinition
    (
        pact_test.upon_receiving(
            "PUT Postgres datasource to add a yearly BatchDefinition (client-driven)"
        )
        .given("Postgres datasource exists and a yearly BatchDefinition is being added")
        .with_request("PUT", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_body(
            match.like(
                {
                    "data": match.like(
                        {
                            "id": match.like(PG_DATASOURCE_ID),
                            "type": "postgres",
                            "name": match.like(PG_DATASOURCE_NAME),
                            "connection_string": match.like(PG_CONNECTION_STRING),
                            "create_temp_table": match.like(False),
                            "assets": match.each_like(
                                {
                                    "id": match.like(PG_TABLE_ASSET_ID),
                                    "type": "table",
                                    "name": match.like(PG_TABLE_ASSET_NAME),
                                    "table_name": match.like(PG_TABLE_NAME),
                                    "batch_metadata": match.like({}),
                                    "batch_definitions": match.each_like(
                                        {
                                            "name": match.like(PG_YEARLY_BD_NAME),
                                            "partitioner": match.like(
                                                {
                                                    "method_name": "partition_on_year",
                                                    "column_name": match.like(PARTITION_COLUMN),
                                                    "sort_ascending": match.like(True),
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
            content_type="application/vnd.api+json",
        )
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_PG_DS_WITH_TABLE_AND_YEARLY_BD)},
            content_type="application/json",
        )
    )

    # 4. GET /datasources/{id}?name=... -- post-PUT refresh
    (
        pact_test.upon_receiving(
            "fetch Postgres datasource by id after adding yearly batch def (client-driven)"
        )
        .given("Postgres datasource contains TableAsset with yearly BatchDefinition")
        .with_request("GET", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": PG_DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_PG_DS_WITH_TABLE_AND_YEARLY_BD)},
            content_type="application/json",
        )
    )

    with patch.object(SQLDatasource, "_create_engine", return_value=mocker.MagicMock()):
        with pact_test.serve() as srv:
            ctx = gx.get_context(
                mode="cloud",
                cloud_base_url=str(srv.url),
                cloud_organization_id=EXISTING_ORGANIZATION_ID,
                cloud_workspace_id=EXISTING_WORKSPACE_ID,
                cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
            )
            datasource = ctx.data_sources.get(name=PG_DATASOURCE_NAME)
            assert isinstance(datasource, PostgresDatasource)
            table_asset = datasource.get_asset(name=PG_TABLE_ASSET_NAME)
            batch_def = table_asset.add_batch_definition_yearly(
                name=PG_YEARLY_BD_NAME, column=PARTITION_COLUMN, validate_batchable=False
            )

    assert batch_def is not None
    assert batch_def.name == PG_YEARLY_BD_NAME


@pytest.mark.cloud
def test_add_batch_definition_daily(pact_test: Pact, mocker: pytest_mock.MockerFixture) -> None:
    """add_batch_definition_daily() issues PUT /datasources/{id} then GET /datasources/{id}?name=...

    Full interaction sequence:
      1. GET /data-context-configuration       (context init)
      2. GET /datasources?name=...             (retrieve existing datasource with TableAsset)
      3. PUT /datasources/{id}                 (add daily BatchDefinition to TableAsset)
      4. GET /datasources/{id}?name=...        (post-PUT refresh)
    """
    headers = _session_headers()

    # 1. GET /data-context-configuration
    setup_data_context_config_interaction(
        pact_test,
        access_token=PACT_DUMMY_ACCESS_TOKEN,
        description_suffix="add-pg-daily-bd",
    )

    # 2. GET /datasources?name=... (retrieve_by_name: serves both has_key and get calls)
    (
        pact_test.upon_receiving(
            "fetch Postgres datasource by name before adding daily batch def (client-driven)"
        )
        .given("the Postgres datasource with TableAsset exists for daily batch def test")
        .with_request("GET", DATASOURCES_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": PG_DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.each_like(_PG_DS_WITH_TABLE_ASSET, min=1)},
            content_type="application/json",
        )
    )

    # 3. PUT /datasources/{id} -- datasource now includes the daily BatchDefinition
    (
        pact_test.upon_receiving(
            "PUT Postgres datasource to add a daily BatchDefinition (client-driven)"
        )
        .given("Postgres datasource exists and a daily BatchDefinition is being added")
        .with_request("PUT", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_body(
            match.like(
                {
                    "data": match.like(
                        {
                            "id": match.like(PG_DATASOURCE_ID),
                            "type": "postgres",
                            "name": match.like(PG_DATASOURCE_NAME),
                            "connection_string": match.like(PG_CONNECTION_STRING),
                            "create_temp_table": match.like(False),
                            "assets": match.each_like(
                                {
                                    "id": match.like(PG_TABLE_ASSET_ID),
                                    "type": "table",
                                    "name": match.like(PG_TABLE_ASSET_NAME),
                                    "table_name": match.like(PG_TABLE_NAME),
                                    "batch_metadata": match.like({}),
                                    "batch_definitions": match.each_like(
                                        {
                                            "name": match.like(PG_DAILY_BD_NAME),
                                            "partitioner": match.like(
                                                {
                                                    "method_name": (
                                                        "partition_on_year_and_month_and_day"
                                                    ),
                                                    "column_name": match.like(PARTITION_COLUMN),
                                                    "sort_ascending": match.like(True),
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
            content_type="application/vnd.api+json",
        )
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_PG_DS_WITH_TABLE_AND_DAILY_BD)},
            content_type="application/json",
        )
    )

    # 4. GET /datasources/{id}?name=... -- post-PUT refresh
    (
        pact_test.upon_receiving(
            "fetch Postgres datasource by id after adding daily batch def (client-driven)"
        )
        .given("Postgres datasource contains TableAsset with daily BatchDefinition")
        .with_request("GET", DATASOURCE_BY_ID_PATH)
        .with_headers(headers)
        .with_query_parameters({"name": PG_DATASOURCE_NAME})
        .will_respond_with(200)
        .with_body(
            {"data": match.like(_PG_DS_WITH_TABLE_AND_DAILY_BD)},
            content_type="application/json",
        )
    )

    with patch.object(SQLDatasource, "_create_engine", return_value=mocker.MagicMock()):
        with pact_test.serve() as srv:
            ctx = gx.get_context(
                mode="cloud",
                cloud_base_url=str(srv.url),
                cloud_organization_id=EXISTING_ORGANIZATION_ID,
                cloud_workspace_id=EXISTING_WORKSPACE_ID,
                cloud_access_token=PACT_DUMMY_ACCESS_TOKEN,
            )
            datasource = ctx.data_sources.get(name=PG_DATASOURCE_NAME)
            assert isinstance(datasource, PostgresDatasource)
            table_asset = datasource.get_asset(name=PG_TABLE_ASSET_NAME)
            batch_def = table_asset.add_batch_definition_daily(
                name=PG_DAILY_BD_NAME, column=PARTITION_COLUMN, validate_batchable=False
            )

    assert batch_def is not None
    assert batch_def.name == PG_DAILY_BD_NAME
