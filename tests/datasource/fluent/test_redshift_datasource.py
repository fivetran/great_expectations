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


def build_connection_string(scheme, user, password, host, port, database, sslmode):
    return f"{scheme}://{user}:{password}@{host}:{port}/{database}?sslmode={sslmode}"


@pytest.fixture
def scheme():
    return "redshift+psycopg2"


@pytest.mark.unit
def test_create_engine_is_called_with_expected_kwargs_using_connection_string_string_type(
    sa,
    mocker: MockerFixture,
    ephemeral_context_with_defaults: EphemeralDataContext,
    scheme,
):
    create_engine_spy = mocker.patch.object(sa, "create_engine")

    user = "user"
    password = "password"
    host = "host"
    port = 1234
    database = "database"
    sslmode = "allow"

    context = ephemeral_context_with_defaults
    connection_string = build_connection_string(
        scheme, user, password, host, port, database, sslmode
    )
    data_source = context.data_sources.add_redshift(
        name="redshift_test", connection_string=connection_string
    )
    data_source.get_engine()  # we will verify that the correct connection details are used when getting the engine  # noqa: E501

    expected_kwargs = RedshiftDsn(
        connection_string,
        scheme=scheme,
    )

    create_engine_spy.assert_called_once_with(expected_kwargs)


@pytest.mark.unit
def test_create_engine_is_called_with_expected_kwargs_using_connection_string_object_type(
    sa,
    mocker: MockerFixture,
    ephemeral_context_with_defaults: EphemeralDataContext,
    scheme,
):
    create_engine_spy = mocker.patch.object(sa, "create_engine")

    user = "user"
    password = "password"
    host = "host"
    port = 1234
    database = "database"
    sslmode = RedshiftSSLModes.ALLOW
    connection_details = RedshiftConnectionDetails(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database,
        sslmode=sslmode,
    )

    context = ephemeral_context_with_defaults
    data_source = context.data_sources.add_redshift(
        name="redshift_test",
        connection_string=connection_details,  # type: ignore[arg-type]
    )
    data_source.get_engine()  # we will verify that the correct connection details are used when getting the engine  # noqa: E501

    connection_string = build_connection_string(
        scheme, user, password, host, port, database, sslmode.value
    )
    expected_kwargs = RedshiftDsn(
        connection_string,
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
