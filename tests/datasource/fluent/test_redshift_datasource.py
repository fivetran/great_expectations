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
