import pytest

from great_expectations.util import (
    get_clickhouse_sqlalchemy_potential_type,
    is_library_loadable,
)
from tests.test_utils import get_awsathena_connection_url


@pytest.mark.athena
def test_get_awsathena_connection_url(monkeypatch):
    monkeypatch.setenv("ATHENA_STAGING_S3", "s3://test-staging/")
    monkeypatch.setenv("ATHENA_DB_NAME", "test_db_name")
    monkeypatch.setenv("ATHENA_TEN_TRIPS_DB_NAME", "test_ten_trips_db_name")

    assert (
        get_awsathena_connection_url()
        == "awsathena+rest://@athena.us-east-1.amazonaws.com/test_db_name?s3_staging_dir=s3://test-staging/"
    )

    assert (
        get_awsathena_connection_url(db_name_env_var="ATHENA_TEN_TRIPS_DB_NAME")
        == "awsathena+rest://@athena.us-east-1.amazonaws.com/test_ten_trips_db_name?s3_staging_dir=s3://test-staging/"
    )


@pytest.mark.clickhouse
@pytest.mark.skipif(
    not is_library_loadable(library_name="clickhouse_sqlalchemy"),
    reason="clickhouse_sqlalchemy is not installed",
)
def test_get_clickhouse_sqlalchemy_potential_type():
    import clickhouse_sqlalchemy
    from clickhouse_sqlalchemy import types

    input_output = (
        ("Nullable(String)", types.String),
        ("Int8", types.Int8),
        ("Map(String, String)", types.Map),
    )
    for pair in input_output:
        assert (
            get_clickhouse_sqlalchemy_potential_type(clickhouse_sqlalchemy.drivers.base, pair[0])
            == pair[1]
        )


def _introspect_db_with_mocked_inspector(mocker, **kwargs):
    """Run introspect_db against a mocked inspector, returning the schemas it visited."""
    from tests.test_utils import introspect_db

    inspector = mocker.Mock()
    inspector.get_schema_names.return_value = ["schema_a", "schema_b", "INFORMATION_SCHEMA"]
    inspector.get_table_names.return_value = ["some_table"]
    inspector.get_view_names.return_value = []
    mocker.patch("tests.test_utils.sa.inspect", return_value=inspector)

    introspect_db(execution_engine=mocker.Mock(), **kwargs)

    visited = [call.kwargs["schema"] for call in inspector.get_table_names.call_args_list]
    return visited, inspector


@pytest.mark.unit
def test_introspect_db_scopes_to_requested_schema(mocker):
    visited, inspector = _introspect_db_with_mocked_inspector(mocker, schema_name="schema_b")

    assert visited == ["schema_b"]
    # Listing every schema on the server is the expensive call this scoping avoids.
    inspector.get_schema_names.assert_not_called()


@pytest.mark.unit
def test_introspect_db_skips_information_schemas(mocker):
    visited, _ = _introspect_db_with_mocked_inspector(mocker)

    assert visited == ["schema_a", "schema_b"]


@pytest.mark.unit
def test_introspect_db_includes_information_schemas_when_not_ignored(mocker):
    visited, _ = _introspect_db_with_mocked_inspector(
        mocker, ignore_information_schemas_and_system_tables=False
    )

    assert visited == ["schema_a", "schema_b", "INFORMATION_SCHEMA"]
