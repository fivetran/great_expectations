from __future__ import annotations

import pytest

from great_expectations.compatibility import pydantic
from great_expectations.datasource.fluent.config_str import ConfigStr
from great_expectations.datasource.fluent.databricks_sql_datasource import (
    DatabricksDsn,
    DatabricksSQLDatasource,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "connection_string, expected_errors",
    [
        pytest.param(
            "databricks://token:my_token>@my_host:1234",
            [
                {
                    "loc": ("connection_string",),
                    "msg": "ConfigStr - contains no config template strings in the format '${MY_CONFIG_VAR}' or '$MY_CONFIG_VAR'",  # noqa: E501 # FIXME CoP
                    "type": "value_error",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "URL query is invalid or missing",
                    "type": "value_error.url.query",
                },
            ],
            id="missing query",
        ),
        pytest.param(
            "databricks://token:my_token>@my_host:1234?my_query=data",
            [
                {
                    "loc": ("connection_string",),
                    "msg": "ConfigStr - contains no config template strings in the format '${MY_CONFIG_VAR}' or '$MY_CONFIG_VAR'",  # noqa: E501 # FIXME CoP
                    "type": "value_error",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "'http_path' query param is invalid or missing",
                    "type": "value_error.url.query.http_path",
                },
            ],
            id="missing http_path",
        ),
        pytest.param(
            "databricks://token:my_token>@my_host:1234?http_path=/path/a/&http_path=/path/b/",
            [
                {
                    "loc": ("connection_string",),
                    "msg": "ConfigStr - contains no config template strings in the format '${MY_CONFIG_VAR}' or '$MY_CONFIG_VAR'",  # noqa: E501 # FIXME CoP
                    "type": "value_error",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "Only one `http_path` query entry is allowed",
                    "type": "value_error",
                },
            ],
            id="multiple http_paths",
        ),
        pytest.param(
            "databricks://token:my_token>@my_host:1234?http_path=/a/b/c&schema=dev",
            [
                {
                    "loc": ("connection_string",),
                    "msg": "ConfigStr - contains no config template strings in the format '${MY_CONFIG_VAR}' or '$MY_CONFIG_VAR'",  # noqa: E501 # FIXME CoP
                    "type": "value_error",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "'catalog' query param is invalid or missing",
                    "type": "value_error.url.query.catalog",
                },
            ],
            id="missing catalog",
        ),
        pytest.param(
            "databricks://token:my_token>@my_host:1234?http_path=/a/b/c&catalog=dev",
            [
                {
                    "loc": ("connection_string",),
                    "msg": "ConfigStr - contains no config template strings in the format '${MY_CONFIG_VAR}' or '$MY_CONFIG_VAR'",  # noqa: E501 # FIXME CoP
                    "type": "value_error",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "'schema' query param is invalid or missing",
                    "type": "value_error.url.query.schema",
                },
            ],
            id="missing schema",
        ),
    ],
)
def test_invalid_connection_string_raises_dsn_error(
    connection_string: str, expected_errors: list[dict]
):
    with pytest.raises(pydantic.ValidationError) as exc_info:
        _ = DatabricksSQLDatasource(name="my_databricks", connection_string=connection_string)

    assert expected_errors == exc_info.value.errors()
    assert "my_token" not in str(exc_info.value.errors())


@pytest.mark.unit
def test_connection_updating_templated_connection_string():
    # Create datasource with templated connection string
    conn_str = "databricks://token:${MY_TOKEN}@hostname:443?http_path=/path/to/warehouse"
    datasource = DatabricksSQLDatasource(
        name="test_ds",
        connection_string=conn_str,
    )

    # Verify initial connection_string is ConfigStr
    assert isinstance(datasource.connection_string, ConfigStr)
    assert datasource.connection_string.template_str == conn_str

    # Assign a new templated connection string directly
    new_conn_str = "databricks://token:${NEW_TOKEN}@hostname:443?http_path=/path/to/warehouse"
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
    conn_str = "databricks://token:${MY_TOKEN}@hostname:443?http_path=/path/to/warehouse"
    datasource = DatabricksSQLDatasource(
        name="test_ds",
        connection_string=conn_str,
    )

    # Verify initial connection_string is ConfigStr
    assert isinstance(datasource.connection_string, ConfigStr)
    assert datasource.connection_string.template_str == conn_str

    plain_conn_str = "databricks://token:plaintoken@plainhost:443?http_path=/plain/path&catalog=main&schema=default"
    datasource.connection_string = plain_conn_str
    assert isinstance(datasource.connection_string, DatabricksDsn), (
        f"Expected DatabricksDsn for plain connection string, "
        f"got {type(datasource.connection_string)}"
    )
