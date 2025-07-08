from __future__ import annotations

import logging

import pytest

from great_expectations.datasource.fluent import CitusDatasource
from great_expectations.execution_engine import SqlAlchemyExecutionEngine
from tests.datasource.fluent.conftest import (
    CreateSourceFixture,
)

# We set a default time range that we use for testing.

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def mock_test_connection(monkeypatch: pytest.MonkeyPatch):
    """Patches the test_connection method of the CitusDatasource class to return True."""

    def _mock_test_connection(self: CitusDatasource) -> bool:
        LOGGER.warning(
            f"Mocked {self.__class__.__name__}.test_connection() called and returning True"
        )
        return True

    monkeypatch.setattr(CitusDatasource, "test_connection", _mock_test_connection)


@pytest.mark.postgresql
def test_construct_citus_datasource(create_source: CreateSourceFixture):
    with create_source(validate_batch_spec=lambda _: None, dialect="postgresql") as source:
        assert source.name == "my_datasource"
        assert source.execution_engine_type is SqlAlchemyExecutionEngine
        assert source.assets == []
