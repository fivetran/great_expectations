from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from great_expectations.compatibility.pydantic import ValidationError
from great_expectations.datasource.fluent.fabric_datasource import FabricDatasource
from great_expectations.datasource.fluent.sql_server_datasource import (
    EntraIDServicePrincipalAuthConnectionDetails,
    SQLServerAuthConnectionDetails,
)

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    from great_expectations.data_context import AbstractDataContext

ConnectionDetailsDict: TypeAlias = dict[str, Any]


@pytest.fixture
def entra_id_connection_details() -> ConnectionDetailsDict:
    return {
        "host": "myserver.database.fabric.microsoft.com",
        "port": 1433,
        "database": "mydb",
        "schema": "dbo",
        "driver": "ODBC Driver 18 for SQL Server",
        "encrypt": "Mandatory",
        "authentication": "Entra ID Service Principal",
        "client_id": "my-client-id-123",
        "client_secret": "my-secret",
        "tenant_id": "my-tenant-id-456",
    }


@pytest.mark.unit
class TestFabricDatasource:
    def test_type_literal(self, entra_id_connection_details: ConnectionDetailsDict) -> None:
        ds = FabricDatasource(
            name="test_ds",
            connection_string=EntraIDServicePrincipalAuthConnectionDetails(
                **entra_id_connection_details
            ),
        )
        assert ds.type == "fabric"

    def test_rejects_sql_server_auth(self) -> None:
        with pytest.raises(ValidationError):
            FabricDatasource(
                name="test_ds",
                connection_string=SQLServerAuthConnectionDetails(
                    host="myserver",
                    database="mydb",
                    schema="dbo",
                    username="myuser",
                    password="mypassword",
                ),
            )


@pytest.mark.unit
@pytest.mark.usefixtures("mock_test_connection")
class TestAddFabricDatasourceAPI:
    def test_add_fabric_with_connection_string(
        self,
        empty_data_context: AbstractDataContext,
    ) -> None:
        source = empty_data_context.data_sources.add_fabric(
            name="my_fabric",
            connection_string=EntraIDServicePrincipalAuthConnectionDetails(
                host="myserver.database.fabric.microsoft.com",
                database="mydb",
                schema="dbo",
                client_id="my-client-id-123",
                client_secret="my-secret",
                tenant_id="my-tenant-id-456",
            ),
        )
        assert isinstance(source, FabricDatasource)
        assert source.type == "fabric"
        assert source.name == "my_fabric"

    def test_add_fabric_with_flat_kwargs_defaults_to_entra_id(
        self,
        empty_data_context: AbstractDataContext,
    ) -> None:
        source = empty_data_context.data_sources.add_fabric(
            name="my_fabric_flat",
            host="myserver.database.fabric.microsoft.com",
            database="mydb",
            schema="dbo",
            client_id="my-client-id-123",
            client_secret="my-secret",
            tenant_id="my-tenant-id-456",
        )
        assert isinstance(source.connection_string, EntraIDServicePrincipalAuthConnectionDetails)
        assert source.connection_string.authentication == "Entra ID Service Principal"
