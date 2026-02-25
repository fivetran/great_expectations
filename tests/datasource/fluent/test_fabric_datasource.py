from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest

from great_expectations.compatibility.pydantic import ValidationError
from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.datasource.fluent.fabric_datasource import FabricDatasource
from great_expectations.datasource.fluent.interfaces import TestConnectionError
from great_expectations.datasource.fluent.sql_server_datasource import (
    EntraIDServicePrincipalAuthConnectionDetails,
    MissingODBCDriverError,
    MSSQLNetworkError,
    MSSQLPrincipalAuthError,
    SQLServerAuthConnectionDetails,
)

if TYPE_CHECKING:
    from typing import Callable, Union

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

    def test_schema_property(self, entra_id_connection_details: ConnectionDetailsDict) -> None:
        ds = FabricDatasource(
            name="test_ds",
            connection_string=EntraIDServicePrincipalAuthConnectionDetails(
                **entra_id_connection_details
            ),
        )
        assert ds.schema_ == "dbo"

    def test_connection_string_type(
        self, entra_id_connection_details: ConnectionDetailsDict
    ) -> None:
        ds = FabricDatasource(
            name="test_ds",
            connection_string=EntraIDServicePrincipalAuthConnectionDetails(
                **entra_id_connection_details
            ),
        )
        assert isinstance(ds.connection_string, EntraIDServicePrincipalAuthConnectionDetails)

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

    @pytest.mark.usefixtures("create_engine_fake")
    def test_get_engine(self, entra_id_connection_details: ConnectionDetailsDict) -> None:
        ds = FabricDatasource(
            name="test_ds",
            connection_string=EntraIDServicePrincipalAuthConnectionDetails(
                **entra_id_connection_details
            ),
        )
        engine = ds.get_engine()
        assert engine is not None

    @pytest.mark.usefixtures("create_engine_fake")
    def test_get_engine_caches(self, entra_id_connection_details: ConnectionDetailsDict) -> None:
        ds = FabricDatasource(
            name="test_ds",
            connection_string=EntraIDServicePrincipalAuthConnectionDetails(
                **entra_id_connection_details
            ),
        )
        engine1 = ds.get_engine()
        engine2 = ds.get_engine()
        assert engine1 is engine2


@pytest.mark.unit
class TestFabricBuildConnectionString:
    def test_basic_connection_string(
        self, entra_id_connection_details: ConnectionDetailsDict
    ) -> None:
        ds = FabricDatasource(
            name="test_ds",
            connection_string=EntraIDServicePrincipalAuthConnectionDetails(
                **entra_id_connection_details
            ),
        )
        result = ds._build_connection_string()
        assert "mssql+pyodbc://@myserver.database.fabric.microsoft.com:1433/mydb" in result
        assert "authentication=ActiveDirectoryServicePrincipal" in result
        assert "UID=my-client-id-123" in result
        assert "PWD=my-secret" in result

    def test_encrypt_optional(self) -> None:
        ds = FabricDatasource(
            name="test_ds",
            connection_string=EntraIDServicePrincipalAuthConnectionDetails(
                host="myserver.database.fabric.microsoft.com",
                database="mydb",
                schema="dbo",
                encrypt="Optional",
                client_id="my-client-id",
                client_secret="secret",
                tenant_id="my-tenant-id",
            ),
        )
        result = ds._build_connection_string()
        assert "Encrypt=no" in result

    def test_special_chars_in_client_secret(self) -> None:
        ds = FabricDatasource(
            name="test_ds",
            connection_string=EntraIDServicePrincipalAuthConnectionDetails(
                host="myserver.database.fabric.microsoft.com",
                database="mydb",
                schema="dbo",
                client_id="my-client-id",
                client_secret="p@ss:w/rd",
                tenant_id="my-tenant-id",
            ),
        )
        result = ds._build_connection_string()
        assert "p%40ss%3Aw%2Frd" in result


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
        assert source.dict(by_alias=True, exclude_unset=False, exclude={"id"}) == {
            "type": "fabric",
            "name": "my_fabric",
            "connection_string": {
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
            },
            "create_temp_table": False,
            "kwargs": {},
            "assets": [],
        }

    def test_add_fabric_with_flat_kwargs(
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
        assert source.dict(by_alias=True, exclude_unset=False, exclude={"id"}) == {
            "type": "fabric",
            "name": "my_fabric_flat",
            "connection_string": {
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
            },
            "create_temp_table": False,
            "kwargs": {},
            "assets": [],
        }

    def test_add_fabric_flat_kwargs_rejects_connection_string_and_kwargs(
        self,
        empty_data_context: AbstractDataContext,
    ) -> None:
        with pytest.raises(ValueError, match="not both"):
            empty_data_context.data_sources.add_fabric(
                name="bad",
                connection_string=EntraIDServicePrincipalAuthConnectionDetails(
                    host="h",
                    database="d",
                    schema="s",
                    client_id="c",
                    client_secret="s",
                    tenant_id="t",
                ),
                host="other_host",
            )


def _make_mock_engine(connect_exception: Exception):
    class _MockEngine:
        def connect(self):
            raise connect_exception

    return _MockEngine()


def with_mock_engine_raising(
    connect_exception: Union[Exception, Callable[[], Exception]],
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            exc = connect_exception() if callable(connect_exception) else connect_exception
            mock_engine = _make_mock_engine(exc)
            with patch.object(FabricDatasource, "get_engine", return_value=mock_engine):
                return func(*args, **kwargs)

        return wrapper

    return decorator


@pytest.fixture
def fabric_datasource() -> FabricDatasource:
    return FabricDatasource(
        name="test_ds",
        connection_string=EntraIDServicePrincipalAuthConnectionDetails(
            host="myserver.database.fabric.microsoft.com",
            database="mydb",
            schema="dbo",
            client_id="my-client-id",
            client_secret="my-secret",
            tenant_id="my-tenant-id",
        ),
    )


@pytest.mark.sql_server
class TestFabricDatasourceTestConnectionErrors:
    @with_mock_engine_raising(sa.exc.OperationalError("Login failed for user", None, Exception()))
    def test_login_failure_raises_principal_auth_error(
        self, fabric_datasource: FabricDatasource
    ) -> None:
        """OperationalError with 'Login' -> MSSQLPrincipalAuthError."""
        with pytest.raises(MSSQLPrincipalAuthError):
            fabric_datasource.test_connection()

    @with_mock_engine_raising(
        sa.exc.OperationalError("Unable to connect: connection refused", None, Exception())
    )
    def test_network_error_raises_network_error(self, fabric_datasource: FabricDatasource) -> None:
        """OperationalError without 'Login' -> MSSQLNetworkError."""
        with pytest.raises(MSSQLNetworkError):
            fabric_datasource.test_connection()

    @with_mock_engine_raising(
        sa.exc.DBAPIError(
            "ODBC Driver 18 for SQL Server not found: file not found", None, Exception()
        )
    )
    def test_missing_odbc_driver_raises_missing_odbc_driver_error(
        self, fabric_datasource: FabricDatasource
    ) -> None:
        """DBAPIError with 'file not found' -> MissingODBCDriverError."""
        with pytest.raises(MissingODBCDriverError):
            fabric_datasource.test_connection()

    @with_mock_engine_raising(ValueError("Something unexpected happened"))
    def test_unhandled_error_reraises_test_connection_error(
        self, fabric_datasource: FabricDatasource
    ) -> None:
        """Unhandled exception types -> original TestConnectionError re-raised."""
        with pytest.raises(TestConnectionError) as exc_info:
            fabric_datasource.test_connection()
        assert isinstance(exc_info.value.cause, ValueError)
        assert "Something unexpected" in str(exc_info.value.cause)
