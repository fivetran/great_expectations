"""Tests for SQLServerDatasource.test_connection error handling.

These tests use a mocked get_engine to simulate various connection failures
without requiring a live SQL Server or ODBC driver.
"""

from __future__ import annotations

import functools
from typing import Callable, Union
from unittest.mock import patch

import pytest

from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.datasource.fluent.interfaces import TestConnectionError
from great_expectations.datasource.fluent.sql_server_datasource import (
    AzureADServicePrincipalAuthConnectionDetails,
    MissingODBCDriverError,
    SQLServerAuthConnectionDetails,
    SQLServerDatasource,
    SQLServerNetworkError,
    SQLServerPasswordAuthError,
    SQLServerPrincipalAuthError,
)


def with_mock_engine_raising(
    connect_exception: Union[Exception, Callable[[], Exception]],
) -> Callable:
    """Patch get_engine to return an engine whose connect() raises the given exception.

    Args:
        connect_exception: The exception to raise, or a callable that returns it
            (for lazy/conditional creation, e.g. when the exception may not be available).
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            exc = connect_exception() if callable(connect_exception) else connect_exception
            mock_engine = _make_mock_engine(exc)
            with patch.object(SQLServerDatasource, "get_engine", return_value=mock_engine):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def _make_mock_engine(connect_exception: Exception):
    """Create a mock engine whose connect() raises the given exception."""

    class _MockEngine:
        def connect(self):
            raise connect_exception

    return _MockEngine()


def _get_pyodbc_login_error() -> Exception:
    """Return pyodbc.OperationalError or skip if pyodbc not available."""
    try:
        from great_expectations.compatibility import pyodbc

        return pyodbc.OperationalError("Login failed for user")  # type: ignore[attr-defined] # pyodbc is either the module or a NotImported sentinel
    except (TypeError, AttributeError):
        pytest.skip("pyodbc not installed or OperationalError not available")


@pytest.fixture
def sql_server_datasource() -> SQLServerDatasource:
    """SQL Server datasource with SQL Server auth (for non-Azure tests)."""
    return SQLServerDatasource(
        name="test_ds",
        connection_string=SQLServerAuthConnectionDetails(
            host="myserver.database.windows.net",
            database="mydb",
            schema="dbo",
            username="myuser",
            password="mypassword",
        ),
    )


@pytest.fixture
def azure_ad_service_principal_datasource() -> SQLServerDatasource:
    """SQL Server datasource with Azure AD Service Principal auth."""
    return SQLServerDatasource(
        name="test_ds",
        connection_string=AzureADServicePrincipalAuthConnectionDetails(
            host="myserver.database.windows.net",
            database="mydb",
            schema="dbo",
            client_id="my-client-id",
            client_secret="my-secret",
            tenant_id="my-tenant-id",
        ),
    )


@pytest.mark.mssql
class TestSQLServerDatasourceTestConnectionErrors:
    """Tests for error handling in SQLServerDatasource.test_connection."""

    @with_mock_engine_raising(
        sa.exc.OperationalError("Login failed for user 'myuser'", None, Exception())
    )
    def test_login_failure_sql_server_auth_raises_sql_password_auth_error(
        self, sql_server_datasource: SQLServerDatasource
    ) -> None:
        """OperationalError with 'Login' and SQL Server auth -> SQLServerPasswordAuthError."""
        with pytest.raises(SQLServerPasswordAuthError):
            sql_server_datasource.test_connection()

    @with_mock_engine_raising(sa.exc.OperationalError("Login failed for user", None, Exception()))
    def test_login_failure_azure_ad_service_principal_raises_sql_principal_auth_error(
        self, azure_ad_service_principal_datasource: SQLServerDatasource
    ) -> None:
        """OperationalError with 'Login' -> SQLServerPrincipalAuthError."""
        with pytest.raises(SQLServerPrincipalAuthError):
            azure_ad_service_principal_datasource.test_connection()

    @with_mock_engine_raising(
        sa.exc.OperationalError("Unable to connect: connection refused", None, Exception())
    )
    def test_network_error_raises_sql_server_network_error(
        self, sql_server_datasource: SQLServerDatasource
    ) -> None:
        """OperationalError without 'Login' -> SQLServerNetworkError."""
        with pytest.raises(SQLServerNetworkError):
            sql_server_datasource.test_connection()

    @with_mock_engine_raising(
        sa.exc.DBAPIError(
            "ODBC Driver 18 for SQL Server not found: file not found", None, Exception()
        )
    )
    def test_missing_odbc_driver_raises_missing_odbc_driver_error(
        self, sql_server_datasource: SQLServerDatasource
    ) -> None:
        """DBAPIError with 'file not found' -> MissingODBCDriverError."""
        with pytest.raises(MissingODBCDriverError):
            sql_server_datasource.test_connection()

    @with_mock_engine_raising(_get_pyodbc_login_error)
    def test_pyodbc_operational_error_login_raises_sql_password_auth_error(
        self, sql_server_datasource: SQLServerDatasource
    ) -> None:
        """pyodbc.OperationalError with 'Login' -> SQLServerPasswordAuthError."""
        with pytest.raises(SQLServerPasswordAuthError):
            sql_server_datasource.test_connection()

    @with_mock_engine_raising(ValueError("Something unexpected happened"))
    def test_unhandled_error_reraises_test_connection_error(
        self, sql_server_datasource: SQLServerDatasource
    ) -> None:
        """Unhandled exception types -> original TestConnectionError re-raised."""
        with pytest.raises(TestConnectionError) as exc_info:
            sql_server_datasource.test_connection()

        # Should re-raise the TestConnectionError that wraps the original
        assert isinstance(exc_info.value.cause, ValueError)
        assert "Something unexpected" in str(exc_info.value.cause)
