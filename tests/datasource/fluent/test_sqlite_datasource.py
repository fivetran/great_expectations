from __future__ import annotations

import pathlib
from contextlib import _GeneratorContextManager, contextmanager
from typing import TYPE_CHECKING, Any, Callable, Generator, Optional

import pytest

from great_expectations.compatibility.pydantic import ValidationError
from great_expectations.core.partitioners import (
    PartitionerConvertedDatetime,
)
from great_expectations.datasource.fluent import SqliteDatasource
from great_expectations.datasource.fluent.config_str import ConfigStr
from great_expectations.datasource.fluent.sqlite_datasource import SqliteDsn
from tests.datasource.fluent.conftest import sqlachemy_execution_engine_mock_cls

if TYPE_CHECKING:
    from great_expectations.data_context import AbstractDataContext


@pytest.fixture
def sqlite_datasource_name() -> str:
    return "sqlite_datasource"


@pytest.fixture
def sqlite_database_path() -> pathlib.Path:
    relative_path = pathlib.Path(
        "..",
        "..",
        "test_sets",
        "taxi_yellow_tripdata_samples",
        "sqlite",
        "yellow_tripdata.db",
    )
    return pathlib.Path(__file__).parent.joinpath(relative_path).resolve(strict=True)


@pytest.fixture
def sqlite_datasource(
    empty_data_context, sqlite_database_path, sqlite_datasource_name
) -> SqliteDatasource:
    connection_string = f"sqlite:///{sqlite_database_path}"
    return SqliteDatasource(
        name=sqlite_datasource_name,
        connection_string=connection_string,
    )


@pytest.mark.unit
def test_connection_string_starts_with_sqlite(
    sqlite_datasource, sqlite_database_path, sqlite_datasource_name
):
    # The actual file doesn't matter only it's existence since SqlAlchemy does a check
    # when it creates the database engine.
    assert sqlite_datasource.name == sqlite_datasource_name
    assert sqlite_datasource.connection_string == f"sqlite:///{sqlite_database_path}"


@pytest.mark.unit
def test_connection_string_that_does_not_start_with_sqlite():
    name = "sqlite_datasource"
    connection_string = "stuff+sqlite:///path/to/database/file.db"
    with pytest.raises(ValidationError) as e:
        SqliteDatasource(
            name=name,
            connection_string=connection_string,
        )
    # the first error is due to missing a config template string
    assert e.value.errors()[1]["msg"] == "URL scheme not permitted"
    assert e.value.errors()[1].get("ctx") == {
        "allowed_schemes": {
            "sqlite",
            "sqlite+aiosqlite",
            "sqlite+pysqlcipher",
            "sqlite+pysqlite",
        }
    }


@pytest.mark.unit
def test_non_select_query_asset(sqlite_datasource):
    with pytest.raises(ValueError):
        sqlite_datasource.add_query_asset(name="query_asset", query="* from table")


# Test double used to return canned responses for partitioner queries.
@contextmanager
def _create_sqlite_source(
    data_context: Optional[AbstractDataContext] = None,
    partitioner_query_response: Optional[list[tuple[str]]] = None,
    create_temp_table: bool = True,
) -> Generator[Any, Any, Any]:
    execution_eng_cls = sqlachemy_execution_engine_mock_cls(
        validate_batch_spec=lambda _: None,
        dialect="sqlite",
        partitioner_query_response=partitioner_query_response,
    )
    # These type ignores when dealing with the execution_engine_override are because
    # it is a generic. We don't care about the exact type since we swap it out with our
    # mock for the purpose of this test and then replace it with the original.
    original_override = SqliteDatasource.execution_engine_override  # type: ignore[misc] # FIXME CoP
    try:
        SqliteDatasource.execution_engine_override = execution_eng_cls  # type: ignore[misc] # FIXME CoP
        sqlite_datasource = SqliteDatasource(
            name="sqlite_datasource",
            connection_string="sqlite://",
            create_temp_table=create_temp_table,
        )
        if data_context:
            sqlite_datasource._data_context = data_context
        yield sqlite_datasource
    finally:
        SqliteDatasource.execution_engine_override = original_override  # type: ignore[misc] # FIXME CoP


@pytest.fixture
def create_sqlite_source() -> Callable[
    [Optional[AbstractDataContext], list[tuple[str]]], _GeneratorContextManager[Any]
]:
    return _create_sqlite_source


@pytest.mark.unit
@pytest.mark.parametrize(
    [
        "partitioner_class",
        "partitioner_kwargs",
        "partitioner_query_responses",
        "all_batches_cnt",
        "specified_batch_request",
        "specified_batch_cnt",
        "last_specified_batch_metadata",
    ],
    [
        pytest.param(
            PartitionerConvertedDatetime,
            {"column_name": "pickup_datetime", "date_format_string": "%Y-%m-%d"},
            [("2019-02-01",), ("2019-02-23",)],
            2,
            {"datetime": "2019-02-23"},
            1,
            {"datetime": "2019-02-23"},
            id="converted_datetime",
        ),
    ],
)
def test_sqlite_specific_partitioner(
    empty_data_context,
    create_sqlite_source,
    partitioner_class,
    partitioner_kwargs,
    partitioner_query_responses,
    all_batches_cnt,
    specified_batch_request,
    specified_batch_cnt,
    last_specified_batch_metadata,
):
    with create_sqlite_source(
        data_context=empty_data_context,
        partitioner_query_response=[response for response in partitioner_query_responses],
    ) as source:
        asset = source.add_query_asset(name="query_asset", query="SELECT * from table")
        # Test getting all batches
        partitioner = partitioner_class(**partitioner_kwargs)
        batch_request = asset.build_batch_request(partitioner=partitioner)
        all_batches = asset.get_batch_identifiers_list(batch_request=batch_request)
        assert len(all_batches) == all_batches_cnt
        # Test getting specified batches
        batch_request = asset.build_batch_request(specified_batch_request, partitioner=partitioner)
        specified_batches = asset.get_batch_identifiers_list(batch_request)
        assert len(specified_batches) == specified_batch_cnt

        batch = asset.get_batch(batch_request)
        assert batch.metadata == last_specified_batch_metadata


@pytest.mark.unit
def test_create_temp_table(empty_data_context, create_sqlite_source):
    with create_sqlite_source(data_context=empty_data_context, create_temp_table=False) as source:
        assert source.create_temp_table is False
        asset = source.add_query_asset(name="query_asset", query="SELECT * from table")
        _ = asset.get_batch(asset.build_batch_request())
        assert source._execution_engine._create_temp_table is False


@pytest.mark.unit
def test_connection_updating_templated_connection_string():
    # Create datasource with templated connection string
    conn_str = "sqlite:///${MY_DB_PATH}"
    datasource = SqliteDatasource(
        name="test_ds",
        connection_string=conn_str,
    )

    # Verify initial connection_string is ConfigStr
    assert isinstance(datasource.connection_string, ConfigStr)
    assert datasource.connection_string.template_str == conn_str

    # Assign a new templated connection string directly
    new_conn_str = "sqlite:///${MY_DB_PATH}".replace("MY_", "NEW_")
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
    conn_str = "sqlite:///${MY_DB_PATH}"
    datasource = SqliteDatasource(
        name="test_ds",
        connection_string=conn_str,
    )

    # Verify initial connection_string is ConfigStr
    assert isinstance(datasource.connection_string, ConfigStr)
    assert datasource.connection_string.template_str == conn_str

    plain_conn_str = "sqlite:///path/to/my.db"
    datasource.connection_string = plain_conn_str
    assert isinstance(datasource.connection_string, SqliteDsn), (
        f"Expected SqliteDsn for plain connection string, got {type(datasource.connection_string)}"
    )
