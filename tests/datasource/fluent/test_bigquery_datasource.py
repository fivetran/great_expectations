import logging

import pytest

from great_expectations.data_context import AbstractDataContext
from great_expectations.datasource.fluent import BigQueryDatasource
from great_expectations.datasource.fluent.config_str import ConfigStr
from great_expectations.execution_engine import SqlAlchemyExecutionEngine

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def mock_test_connection(monkeypatch: pytest.MonkeyPatch):
    """Patches the test_connection method of the BigQueryDatasource class to return True."""

    def _mock_test_connection(self: BigQueryDatasource) -> bool:
        LOGGER.warning(
            f"Mocked {self.__class__.__name__}.test_connection() called and returning True"
        )
        return True

    monkeypatch.setattr(BigQueryDatasource, "test_connection", _mock_test_connection)


@pytest.mark.unit
def test_add_bigquery_datasource(
    mock_test_connection,
    empty_data_context: AbstractDataContext,
):
    test_datasource_name = "test_datasource"
    test_connection_string = "bigquery://gcp_project_name/bigquery_dataset"
    source = empty_data_context.data_sources.add_bigquery(
        name=test_datasource_name, connection_string=test_connection_string
    )
    assert source.type == "bigquery"
    assert source.name == test_datasource_name
    assert source.execution_engine_type is SqlAlchemyExecutionEngine
    assert source.assets == []


@pytest.mark.unit
def test_connection_updating_templated_connection_string():
    # Create datasource with templated connection string
    conn_str = "bigquery://project-id/${MY_DATASET}"
    datasource = BigQueryDatasource(
        name="test_ds",
        connection_string=conn_str,
    )

    # Verify initial connection_string is ConfigStr
    assert isinstance(datasource.connection_string, ConfigStr)
    assert datasource.connection_string.template_str == conn_str

    # Assign a new templated connection string directly
    new_conn_str = "bigquery://project-id/${MY_DATASET}".replace("MY_", "NEW_")
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
    conn_str = "bigquery://project-id/${MY_DATASET}"
    datasource = BigQueryDatasource(
        name="test_ds",
        connection_string=conn_str,
    )

    # Verify initial connection_string is ConfigStr
    assert isinstance(datasource.connection_string, ConfigStr)
    assert datasource.connection_string.template_str == conn_str

    plain_conn_str = "bigquery://my-project/my-dataset"
    datasource.connection_string = plain_conn_str
    assert isinstance(datasource.connection_string, str), (
        f"Expected str for plain connection string, got {type(datasource.connection_string)}"
    )
