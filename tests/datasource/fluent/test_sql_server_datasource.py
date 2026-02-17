from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from great_expectations.compatibility.pydantic import ValidationError
from great_expectations.datasource.fluent.config_str import ConfigStr
from great_expectations.datasource.fluent.sql_server_datasource import (
    EntraIDPasswordAuthConnectionDetails,
    EntraIDServicePrincipalAuthConnectionDetails,
    SQLServerAuthConnectionDetails,
    SQLServerDatasource,
    SqlServerDsn,
)

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    from great_expectations.data_context import AbstractDataContext

ConnectionDetailsDict: TypeAlias = dict[str, Any]


@pytest.fixture
def connection_details_default() -> ConnectionDetailsDict:
    return {
        "host": "myserver.database.windows.net",
        "port": 1433,
        "database": "mydb",
        "schema": "dbo",
        "driver": "ODBC Driver 18 for SQL Server",
        "encrypt": "Mandatory",
        "username": "myuser",
        "password": "mypassword",
    }


@pytest.fixture
def connection_details_encrypt_optional() -> ConnectionDetailsDict:
    return {
        "host": "host",
        "port": 1433,
        "database": "db",
        "schema": "dbo",
        "driver": "ODBC Driver 18 for SQL Server",
        "encrypt": "Optional",
        "username": "u",
        "password": "p",
    }


@pytest.fixture
def connection_details_encrypt_strict() -> ConnectionDetailsDict:
    return {
        "host": "host",
        "port": 1433,
        "database": "db",
        "schema": "dbo",
        "driver": "ODBC Driver 18 for SQL Server",
        "encrypt": "Strict",
        "username": "u",
        "password": "p",
    }


@pytest.fixture
def connection_details_special_chars() -> ConnectionDetailsDict:
    return {
        "host": "host",
        "port": 1433,
        "database": "db",
        "schema": "dbo",
        "driver": "ODBC Driver 18 for SQL Server",
        "encrypt": "Mandatory",
        "username": "user",
        "password": "p@ss:w/rd",
    }


@pytest.fixture
def entra_id_connection_details_default() -> ConnectionDetailsDict:
    return {
        "host": "myserver.database.windows.net",
        "port": 1433,
        "database": "mydb",
        "schema": "dbo",
        "driver": "ODBC Driver 18 for SQL Server",
        "encrypt": "Mandatory",
        "authentication": "Entra ID Password",
        "username": "myuser@contoso.com",
        "password": "mypassword",
    }


@pytest.fixture
def entra_id_service_principal_connection_details_default() -> ConnectionDetailsDict:
    return {
        "host": "myserver.database.windows.net",
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
class TestSQLServerAuthConnectionDetails:
    def test_create_with_defaults(self) -> None:
        details = SQLServerAuthConnectionDetails(
            host="myserver",
            database="mydb",
            schema="dbo",
            username="myuser",
            password="mypassword",
        )
        assert details.dict(by_alias=True, exclude_unset=False) == {
            "host": "myserver",
            "port": 1433,
            "database": "mydb",
            "schema": "dbo",
            "driver": "ODBC Driver 18 for SQL Server",
            "encrypt": "Mandatory",
            "authentication": "SQL Server",
            "username": "myuser",
            "password": "mypassword",
        }

    def test_password_accepts_config_str(self) -> None:
        details = SQLServerAuthConnectionDetails(
            host="myserver",
            database="mydb",
            schema="dbo",
            username="myuser",
            password="${MY_PASSWORD}",
        )
        assert isinstance(details.password, ConfigStr)
        assert str(details.password) == "${MY_PASSWORD}"

    def test_create_with_custom_values(self) -> None:
        details = SQLServerAuthConnectionDetails(
            host="customserver",
            port=3342,
            database="customdb",
            schema="custom_schema",
            driver="ODBC Driver 17 for SQL Server",
            encrypt="Optional",
            username="admin",
            password="secret",
        )
        assert details.dict(by_alias=True, exclude_unset=False) == {
            "host": "customserver",
            "port": 3342,
            "database": "customdb",
            "schema": "custom_schema",
            "driver": "ODBC Driver 17 for SQL Server",
            "encrypt": "Optional",
            "authentication": "SQL Server",
            "username": "admin",
            "password": "secret",
        }


@pytest.mark.unit
class TestBuildConnectionString:
    def test_basic_connection_string(
        self, connection_details_default: ConnectionDetailsDict
    ) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=SQLServerAuthConnectionDetails(**connection_details_default),
        )
        result = ds._build_connection_string()
        assert result == (
            "mssql+pyodbc://myuser:mypassword"
            "@myserver.database.windows.net:1433/mydb"
            "?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes"
        )

    def test_encrypt_optional(
        self, connection_details_encrypt_optional: ConnectionDetailsDict
    ) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=SQLServerAuthConnectionDetails(**connection_details_encrypt_optional),
        )
        result = ds._build_connection_string()
        assert "Encrypt=no" in result

    def test_encrypt_strict(self, connection_details_encrypt_strict: ConnectionDetailsDict) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=SQLServerAuthConnectionDetails(**connection_details_encrypt_strict),
        )
        result = ds._build_connection_string()
        assert "Encrypt=strict" in result

    def test_special_chars_in_password_are_encoded(
        self, connection_details_special_chars: ConnectionDetailsDict
    ) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=SQLServerAuthConnectionDetails(**connection_details_special_chars),
        )
        result = ds._build_connection_string()
        assert "p%40ss%3Aw%2Frd" in result


@pytest.mark.unit
class TestSQLServerDatasource:
    def test_type_literal(self, connection_details_default: ConnectionDetailsDict) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=SQLServerAuthConnectionDetails(**connection_details_default),
        )
        assert ds.type == "sql_server"

    def test_schema_property(self, connection_details_default: ConnectionDetailsDict) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=SQLServerAuthConnectionDetails(**connection_details_default),
        )
        assert ds.schema_ == "dbo"

    def test_mssql_dsn_rejects_non_pyodbc_scheme(self) -> None:
        with pytest.raises(ValidationError, match="URL scheme not permitted"):
            SqlServerDsn.from_url("mssql+pymssql://user:pass@host:1433/db")

    @pytest.mark.usefixtures("create_engine_fake")
    def test_get_engine_calls_create_engine(
        self,
        connection_details_default: ConnectionDetailsDict,
    ) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=SQLServerAuthConnectionDetails(**connection_details_default),
        )
        engine = ds.get_engine()
        assert engine is not None

    @pytest.mark.usefixtures("create_engine_fake")
    def test_get_engine_caches_engine(
        self,
        connection_details_default: ConnectionDetailsDict,
    ) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=SQLServerAuthConnectionDetails(**connection_details_default),
        )
        engine1 = ds.get_engine()
        engine2 = ds.get_engine()
        assert engine1 is engine2


@pytest.mark.unit
class TestEntraIDPasswordAuthConnectionDetails:
    def test_create_with_defaults(self) -> None:
        details = EntraIDPasswordAuthConnectionDetails(
            host="myserver.database.windows.net",
            database="mydb",
            schema="dbo",
            username="myuser@contoso.com",
            password="mypassword",
        )
        assert details.dict(by_alias=True, exclude_unset=False) == {
            "host": "myserver.database.windows.net",
            "port": 1433,
            "database": "mydb",
            "schema": "dbo",
            "driver": "ODBC Driver 18 for SQL Server",
            "encrypt": "Mandatory",
            "authentication": "Entra ID Password",
            "username": "myuser@contoso.com",
            "password": "mypassword",
        }

    def test_password_accepts_config_str(self) -> None:
        details = EntraIDPasswordAuthConnectionDetails(
            host="myserver",
            database="mydb",
            schema="dbo",
            username="myuser@contoso.com",
            password="${MY_PASSWORD}",
        )
        assert isinstance(details.password, ConfigStr)
        assert str(details.password) == "${MY_PASSWORD}"


@pytest.mark.unit
class TestEntraIDServicePrincipalAuthConnectionDetails:
    def test_create_with_defaults(self) -> None:
        details = EntraIDServicePrincipalAuthConnectionDetails(
            host="myserver.database.windows.net",
            database="mydb",
            schema="dbo",
            client_id="my-client-id-123",
            client_secret="my-secret",
            tenant_id="my-tenant-id-456",
        )
        assert details.dict(by_alias=True, exclude_unset=False) == {
            "host": "myserver.database.windows.net",
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

    def test_client_secret_accepts_config_str(self) -> None:
        details = EntraIDServicePrincipalAuthConnectionDetails(
            host="myserver",
            database="mydb",
            schema="dbo",
            client_id="my-client-id",
            client_secret="${MY_CLIENT_SECRET}",
            tenant_id="my-tenant-id",
        )
        assert isinstance(details.client_secret, ConfigStr)
        assert str(details.client_secret) == "${MY_CLIENT_SECRET}"


@pytest.mark.unit
class TestBuildConnectionStringAzureAD:
    def test_entra_id_password_connection_string(
        self,
        entra_id_connection_details_default: ConnectionDetailsDict,
    ) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=EntraIDPasswordAuthConnectionDetails(
                **entra_id_connection_details_default
            ),
        )
        result = ds._build_connection_string()
        assert result == (
            "mssql+pyodbc://myuser%40contoso.com:mypassword"
            "@myserver.database.windows.net:1433/mydb"
            "?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes"
            "&authentication=ActiveDirectoryPassword"
        )

    def test_entra_id_password_special_chars_in_password(self) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=EntraIDPasswordAuthConnectionDetails(
                host="myserver.database.windows.net",
                database="mydb",
                schema="dbo",
                username="myuser@contoso.com",
                password="p@ss:w/rd",
            ),
        )
        result = ds._build_connection_string()
        assert "p%40ss%3Aw%2Frd" in result
        assert "authentication=ActiveDirectoryPassword" in result

    def test_entra_id_password_encrypt_optional(self) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=EntraIDPasswordAuthConnectionDetails(
                host="myserver.database.windows.net",
                database="mydb",
                schema="dbo",
                encrypt="Optional",
                username="myuser@contoso.com",
                password="pw",
            ),
        )
        result = ds._build_connection_string()
        assert "Encrypt=no" in result
        assert "authentication=ActiveDirectoryPassword" in result

    def test_sql_server_auth_has_no_authentication_param(
        self,
        connection_details_default: ConnectionDetailsDict,
    ) -> None:
        """Ensure SQL Server auth does NOT add the Authentication query param."""
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=SQLServerAuthConnectionDetails(**connection_details_default),
        )
        result = ds._build_connection_string()
        assert "Authentication=" not in result

    def test_entra_id_service_principal_connection_string(
        self,
        entra_id_service_principal_connection_details_default: ConnectionDetailsDict,
    ) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=EntraIDServicePrincipalAuthConnectionDetails(
                **entra_id_service_principal_connection_details_default
            ),
        )
        result = ds._build_connection_string()
        assert "mssql+pyodbc://@myserver.database.windows.net:1433/mydb" in result
        assert "authentication=ActiveDirectoryServicePrincipal" in result
        assert "UID=my-client-id-123" in result
        assert "PWD=my-secret" in result

    def test_entra_id_service_principal_special_chars_in_client_secret(self) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=EntraIDServicePrincipalAuthConnectionDetails(
                host="myserver.database.windows.net",
                database="mydb",
                schema="dbo",
                client_id="my-client-id",
                client_secret="p@ss:w/rd",
                tenant_id="my-tenant-id",
            ),
        )
        result = ds._build_connection_string()
        assert "p%40ss%3Aw%2Frd" in result
        assert "authentication=ActiveDirectoryServicePrincipal" in result

    def test_entra_id_service_principal_encrypt_optional(self) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=EntraIDServicePrincipalAuthConnectionDetails(
                host="myserver.database.windows.net",
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
        assert "authentication=ActiveDirectoryServicePrincipal" in result


@pytest.mark.unit
class TestSQLServerDatasourceDiscriminatedUnion:
    def test_accepts_sql_server_auth(
        self,
        connection_details_default: ConnectionDetailsDict,
    ) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=SQLServerAuthConnectionDetails(**connection_details_default),
        )
        assert isinstance(ds.connection_string, SQLServerAuthConnectionDetails)

    def test_accepts_entra_id_password_auth(
        self,
        entra_id_connection_details_default: ConnectionDetailsDict,
    ) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=EntraIDPasswordAuthConnectionDetails(
                **entra_id_connection_details_default
            ),
        )
        assert isinstance(ds.connection_string, EntraIDPasswordAuthConnectionDetails)

    def test_accepts_entra_id_service_principal_auth(
        self,
        entra_id_service_principal_connection_details_default: ConnectionDetailsDict,
    ) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=EntraIDServicePrincipalAuthConnectionDetails(
                **entra_id_service_principal_connection_details_default
            ),
        )
        assert isinstance(ds.connection_string, EntraIDServicePrincipalAuthConnectionDetails)

    def test_schema_property_entra_id(
        self,
        entra_id_connection_details_default: ConnectionDetailsDict,
    ) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=EntraIDPasswordAuthConnectionDetails(
                **entra_id_connection_details_default
            ),
        )
        assert ds.schema_ == "dbo"

    def test_schema_property_entra_id_service_principal(
        self,
        entra_id_service_principal_connection_details_default: ConnectionDetailsDict,
    ) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=EntraIDServicePrincipalAuthConnectionDetails(
                **entra_id_service_principal_connection_details_default
            ),
        )
        assert ds.schema_ == "dbo"

    @pytest.mark.usefixtures("create_engine_fake")
    def test_get_engine_entra_id(
        self,
        entra_id_connection_details_default: ConnectionDetailsDict,
    ) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=EntraIDPasswordAuthConnectionDetails(
                **entra_id_connection_details_default
            ),
        )
        engine = ds.get_engine()
        assert engine is not None

    @pytest.mark.usefixtures("create_engine_fake")
    def test_get_engine_entra_id_service_principal(
        self,
        entra_id_service_principal_connection_details_default: ConnectionDetailsDict,
    ) -> None:
        ds = SQLServerDatasource(
            name="test_ds",
            connection_string=EntraIDServicePrincipalAuthConnectionDetails(
                **entra_id_service_principal_connection_details_default
            ),
        )
        engine = ds.get_engine()
        assert engine is not None


@pytest.mark.unit
@pytest.mark.usefixtures("mock_test_connection")
class TestAddSQLServerDatasourceAPI:
    def test_add_sql_server_with_sql_server_auth(
        self,
        empty_data_context: AbstractDataContext,
    ) -> None:
        source = empty_data_context.data_sources.add_sql_server(
            name="my_sql_server",
            connection_string=SQLServerAuthConnectionDetails(
                host="myserver.database.windows.net",
                database="mydb",
                schema="dbo",
                username="myuser",
                password="mypassword",
            ),
        )
        assert source.dict(by_alias=True, exclude_unset=False, exclude={"id"}) == {
            "type": "sql_server",
            "name": "my_sql_server",
            "connection_string": {
                "host": "myserver.database.windows.net",
                "port": 1433,
                "database": "mydb",
                "schema": "dbo",
                "driver": "ODBC Driver 18 for SQL Server",
                "encrypt": "Mandatory",
                "authentication": "SQL Server",
                "username": "myuser",
                "password": "mypassword",
            },
            "create_temp_table": False,
            "kwargs": {},
            "assets": [],
        }

    def test_add_sql_server_with_entra_id_password_auth(
        self,
        empty_data_context: AbstractDataContext,
    ) -> None:
        source = empty_data_context.data_sources.add_sql_server(
            name="my_azure_sql",
            connection_string=EntraIDPasswordAuthConnectionDetails(
                host="myserver.database.windows.net",
                database="mydb",
                schema="dbo",
                username="myuser@contoso.com",
                password="mypassword",
            ),
        )
        assert source.dict(by_alias=True, exclude_unset=False, exclude={"id"}) == {
            "type": "sql_server",
            "name": "my_azure_sql",
            "connection_string": {
                "host": "myserver.database.windows.net",
                "port": 1433,
                "database": "mydb",
                "schema": "dbo",
                "driver": "ODBC Driver 18 for SQL Server",
                "encrypt": "Mandatory",
                "authentication": "Entra ID Password",
                "username": "myuser@contoso.com",
                "password": "mypassword",
            },
            "create_temp_table": False,
            "kwargs": {},
            "assets": [],
        }

    def test_add_sql_server_with_entra_id_service_principal_auth(
        self,
        empty_data_context: AbstractDataContext,
    ) -> None:
        source = empty_data_context.data_sources.add_sql_server(
            name="my_azure_sp_sql",
            connection_string=EntraIDServicePrincipalAuthConnectionDetails(
                host="myserver.database.windows.net",
                database="mydb",
                schema="dbo",
                client_id="my-client-id-123",
                client_secret="my-secret",
                tenant_id="my-tenant-id-456",
            ),
        )
        assert source.dict(by_alias=True, exclude_unset=False, exclude={"id"}) == {
            "type": "sql_server",
            "name": "my_azure_sp_sql",
            "connection_string": {
                "host": "myserver.database.windows.net",
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

    def test_add_sql_server_with_flat_kwargs_sql_server_auth(
        self,
        empty_data_context: AbstractDataContext,
    ) -> None:
        source = empty_data_context.data_sources.add_sql_server(
            name="my_sql_server_flat",
            host="myserver.database.windows.net",
            database="mydb",
            schema="dbo",
            username="myuser",
            password="mypassword",
        )
        assert source.dict(by_alias=True, exclude_unset=False, exclude={"id"}) == {
            "type": "sql_server",
            "name": "my_sql_server_flat",
            "connection_string": {
                "host": "myserver.database.windows.net",
                "port": 1433,
                "database": "mydb",
                "schema": "dbo",
                "driver": "ODBC Driver 18 for SQL Server",
                "encrypt": "Mandatory",
                "authentication": "SQL Server",
                "username": "myuser",
                "password": "mypassword",
            },
            "create_temp_table": False,
            "kwargs": {},
            "assets": [],
        }

    def test_add_sql_server_with_flat_kwargs_entra_id_password(
        self,
        empty_data_context: AbstractDataContext,
    ) -> None:
        source = empty_data_context.data_sources.add_sql_server(
            name="my_azure_flat",
            host="myserver.database.windows.net",
            database="mydb",
            schema="dbo",
            username="myuser@contoso.com",
            password="mypassword",
            authentication="Entra ID Password",
        )
        assert source.dict(by_alias=True, exclude_unset=False, exclude={"id"}) == {
            "type": "sql_server",
            "name": "my_azure_flat",
            "connection_string": {
                "host": "myserver.database.windows.net",
                "port": 1433,
                "database": "mydb",
                "schema": "dbo",
                "driver": "ODBC Driver 18 for SQL Server",
                "encrypt": "Mandatory",
                "authentication": "Entra ID Password",
                "username": "myuser@contoso.com",
                "password": "mypassword",
            },
            "create_temp_table": False,
            "kwargs": {},
            "assets": [],
        }

    def test_add_sql_server_with_flat_kwargs_entra_id_service_principal(
        self,
        empty_data_context: AbstractDataContext,
    ) -> None:
        source = empty_data_context.data_sources.add_sql_server(
            name="my_azure_sp_flat",
            host="myserver.database.windows.net",
            database="mydb",
            schema="dbo",
            authentication="Entra ID Service Principal",
            client_id="my-client-id-123",
            client_secret="my-secret",
            tenant_id="my-tenant-id-456",
        )
        assert source.dict(by_alias=True, exclude_unset=False, exclude={"id"}) == {
            "type": "sql_server",
            "name": "my_azure_sp_flat",
            "connection_string": {
                "host": "myserver.database.windows.net",
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

    def test_add_sql_server_flat_kwargs_rejects_connection_string_and_kwargs(
        self,
        empty_data_context: AbstractDataContext,
    ) -> None:
        with pytest.raises(ValueError, match="not both"):
            empty_data_context.data_sources.add_sql_server(  # type: ignore[call-overload]
                name="bad",
                connection_string=SQLServerAuthConnectionDetails(
                    host="h",
                    database="d",
                    schema="s",
                    username="u",
                    password="p",
                ),
                host="other_host",
            )
