import logging
from typing import Union

import pytest
from pytest_mock import MockerFixture

from great_expectations.data_context import EphemeralDataContext
from great_expectations.datasource.fluent.config_str import ConfigStr
from great_expectations.datasource.fluent.redshift_datasource import (
    RedshiftConnectionDetails,
    RedshiftDatasource,
    RedshiftDsn,
    RedshiftSSLModes,
)

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def scheme():
    return "redshift+psycopg2"


@pytest.mark.unit
@pytest.mark.parametrize(
    "connection_input,expected_connection_string",
    [
        pytest.param(
            "redshift+psycopg2://user:password@host:1234/database?sslmode=allow",
            "redshift+psycopg2://user:password@host:1234/database?sslmode=allow",
            id="string type",
        ),
        pytest.param(
            {
                "user": "user",
                "password": "password",
                "host": "host",
                "port": 1234,
                "database": "database",
                "sslmode": RedshiftSSLModes.ALLOW,
            },
            "redshift+psycopg2://user:password@host:1234/database?sslmode=allow",
            id="dict type",
        ),
        pytest.param(
            RedshiftConnectionDetails(
                user="user",
                password="password",
                host="host",
                port=1234,
                database="database",
                sslmode=RedshiftSSLModes.ALLOW,
            ),
            "redshift+psycopg2://user:password@host:1234/database?sslmode=allow",
            id="dict type",
        ),
    ],
)
def test_create_engine_is_called_with_expected_kwargs(
    connection_input,
    expected_connection_string,
    sa,
    mocker: MockerFixture,
    ephemeral_context_with_defaults: EphemeralDataContext,
    scheme,
):
    create_engine_spy = mocker.patch.object(sa, "create_engine")

    context = ephemeral_context_with_defaults
    data_source = context.data_sources.add_redshift(
        name="redshift_test",
        connection_string=connection_input,
    )
    data_source.get_engine()  # we will verify that the correct connection details are used when getting the engine  # noqa: E501

    expected_kwargs = RedshiftDsn(
        expected_connection_string,
        scheme=scheme,
    )

    create_engine_spy.assert_called_once_with(expected_kwargs)


@pytest.mark.unit
def test_value_error_raised_if_invalid_connection_detail_inputs(
    sa,
    ephemeral_context_with_defaults: EphemeralDataContext,
    scheme,
):
    user = "user"
    password = "password"
    host = "host"
    port = 1234
    database = "database"
    sslmode = "INVALID"

    with pytest.raises(ValueError):
        RedshiftConnectionDetails(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database,
            sslmode=sslmode,  # type: ignore[arg-type] # Ignore this for purpose of the test
        )


@pytest.mark.unit
def test_connection_updating_templated_connection_string():
    # Create datasource with templated connection string
    conn_str = "redshift+psycopg2://user:${MY_PASSWORD}@host.amazonaws.com:5439/database"
    datasource = RedshiftDatasource(
        name="test_ds",
        connection_string=conn_str,
    )

    # Verify initial connection_string is ConfigStr
    assert isinstance(datasource.connection_string, ConfigStr)
    assert datasource.connection_string.template_str == conn_str

    # Assign a new templated connection string directly
    new_conn_str = (
        "redshift+psycopg2://user:${MY_PASSWORD}@host.amazonaws.com:5439/database".replace(
            "MY_", "NEW_"
        )
    )
    datasource.connection_string = new_conn_str

    # Verify it's still a ConfigStr after assignment (not a plain str)
    assert isinstance(datasource.connection_string, ConfigStr), (
        f"Expected ConfigStr, got {type(datasource.connection_string)}. "
        "This indicates validate_assignment is not enabled."
    )
    assert datasource.connection_string.template_str == new_conn_str


@pytest.mark.unit
def test_connection_updating_plain_connection_string():
    # Create datasource with templated connection string
    conn_str = "redshift+psycopg2://user:${MY_PASSWORD}@host.amazonaws.com:5439/database"
    datasource = RedshiftDatasource(
        name="test_ds",
        connection_string=conn_str,
    )

    # Verify initial connection_string is ConfigStr
    assert isinstance(datasource.connection_string, ConfigStr)
    assert datasource.connection_string.template_str == conn_str

    plain_conn_str = "redshift+psycopg2://plainuser:plainpass@plainhost.amazonaws.com:5439/plaindb"
    datasource.connection_string = plain_conn_str
    assert isinstance(datasource.connection_string, RedshiftDsn), (
        f"Expected RedshiftDsn for plain connection string, "
        f"got {type(datasource.connection_string)}"
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "connection_input,expected_connection_string",
    [
        pytest.param(
            {
                "user": "user",
                "password": "password",
                "host": "host",
                "port": 1234,
                "database": "database",
                "sslmode": RedshiftSSLModes.ALLOW,
                "schema": "my_schema",
            },
            "redshift+psycopg2://user:password@host:1234/database?sslmode=allow&options=-csearch_path%3Dmy_schema",
            id="dict type with schema",
        ),
        pytest.param(
            RedshiftConnectionDetails(
                user="user",
                password="password",
                host="host",
                port=1234,
                database="database",
                sslmode=RedshiftSSLModes.ALLOW,
                schema="my_schema",
            ),
            "redshift+psycopg2://user:password@host:1234/database?sslmode=allow&options=-csearch_path%3Dmy_schema",
            id="RedshiftConnectionDetails with schema_",
        ),
        pytest.param(
            {
                "user": "user",
                "password": "password",
                "host": "host",
                "port": 1234,
                "database": "database",
                "sslmode": RedshiftSSLModes.ALLOW,
            },
            "redshift+psycopg2://user:password@host:1234/database?sslmode=allow",
            id="dict type without schema",
        ),
    ],
)
def test_schema_property_in_connection_string(
    connection_input: Union[ConfigStr, RedshiftDsn],
    expected_connection_string: str,
    sa,
    mocker: MockerFixture,
    ephemeral_context_with_defaults: EphemeralDataContext,
    scheme,
):
    create_engine_spy = mocker.patch.object(sa, "create_engine")

    context = ephemeral_context_with_defaults
    data_source = context.data_sources.add_redshift(
        name="redshift_test_schema",
        connection_string=connection_input,
    )
    data_source.get_engine()

    expected_kwargs = RedshiftDsn(
        expected_connection_string,
        scheme=scheme,
    )

    create_engine_spy.assert_called_once_with(expected_kwargs)
