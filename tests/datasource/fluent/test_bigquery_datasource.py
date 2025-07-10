import logging

import pytest

from great_expectations.data_context import AbstractDataContext
from great_expectations.datasource.fluent import BigQueryDatasource
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
