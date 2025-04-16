import logging

import pytest
from pytest_mock import MockerFixture

from great_expectations.data_context import EphemeralDataContext
from great_expectations.datasource.fluent.redshift_datasource import (
    RedshiftConnectionDetails,
    RedshiftDsn,
    RedshiftSSLModes,
)

LOGGER = logging.getLogger(__name__)


def build_connection_string(scheme, username, password, host, port, database, ssl_mode):
    return f"{scheme}://{username}:{password}@{host}:{port}/{database}?sslmode={ssl_mode}"


@pytest.fixture
def scheme():
    return "redshift+psycopg2"


@pytest.mark.unit
@pytest.mark.redshift
def test_create_engine_is_called_with_expected_kwargs_using_connection_string(
    sa,
    mocker: MockerFixture,
    ephemeral_context_with_defaults: EphemeralDataContext,
    scheme,
):
    create_engine_spy = mocker.patch.object(sa, "create_engine")

    username = "username"
    password = "password"
    host = "host"
    port = 1234
    database = "database"
    ssl_mode = "allow"
    connection_string = build_connection_string(
        scheme, username, password, host, port, database, ssl_mode
    )

    expected_kwargs = RedshiftDsn(
        connection_string,
        scheme=scheme,
        user=username,
        password=password,
        host=host,
        host_type="int_domain",
        port=port,
        path=f"/{database}",
        query=f"sslmode={ssl_mode}",
    )

    context = ephemeral_context_with_defaults
    data_source = context.data_sources.add_redshift(
        name="redshift_test", connection_string=connection_string
    )
    data_source.get_engine()

    create_engine_spy.assert_called_once_with(expected_kwargs)


@pytest.mark.unit
@pytest.mark.redshift
def test_create_engine_is_called_with_expected_kwargs_using_connection_details(
    sa,
    mocker: MockerFixture,
    ephemeral_context_with_defaults: EphemeralDataContext,
    scheme,
):
    create_engine_spy = mocker.patch.object(sa, "create_engine")

    username = "username"
    password = "password"
    host = "host"
    port = 1234
    database = "database"
    ssl_mode = RedshiftSSLModes.ALLOW
    connection_string = build_connection_string(
        scheme, username, password, host, port, database, ssl_mode.value
    )

    connection_details = RedshiftConnectionDetails(
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
        ssl_mode=ssl_mode,
    )
    expected_kwargs = RedshiftDsn(
        connection_string,
        scheme=scheme,
        user=username,
        password=password,
        host=host,
        host_type="int_domain",
        port=port,
        path=f"/{database}",
        query=f"sslmode={ssl_mode.value}",
    )
    context = ephemeral_context_with_defaults
    data_source = context.data_sources.add_redshift(
        name="redshift_test",
        connection_details=connection_details,  # type: ignore[call-arg]
    )
    data_source.get_engine()
    create_engine_spy.assert_called_once_with(expected_kwargs)


@pytest.mark.unit
@pytest.mark.redshift
def test_value_error_raised_if_invalid_connection_detail_inputs(
    sa,
    ephemeral_context_with_defaults: EphemeralDataContext,
    scheme,
):
    username = "username"
    password = "password"
    host = "host"
    port = 1234
    database = "database"
    ssl_mode = "INVALID"

    with pytest.raises(ValueError):
        RedshiftConnectionDetails(
            username=username,
            password=password,
            host=host,
            port=port,
            database=database,
            ssl_mode=ssl_mode,  # type: ignore[arg-type] # Ignore this for purpose of the test
        )
