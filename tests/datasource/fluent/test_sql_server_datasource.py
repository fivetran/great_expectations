from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from great_expectations.compatibility.pydantic import ValidationError
from great_expectations.datasource.fluent.config_str import ConfigStr
from great_expectations.datasource.fluent.sql_server_datasource import (
    SQLServerAuthConnectionDetails,
    SQLServerDatasource,
    SqlServerDsn,
)

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

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
