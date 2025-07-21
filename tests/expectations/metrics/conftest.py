from typing import Iterable, Optional, Union
from unittest import mock

import pytest
from typing_extensions import override

from great_expectations.compatibility.sqlalchemy import (
    sqlalchemy as sa,
)
from great_expectations.core.metric_domain_types import MetricDomainTypes
from great_expectations.execution_engine import SqlAlchemyExecutionEngine
from great_expectations.execution_engine.sqlalchemy_batch_data import SqlAlchemyBatchData


def create_mock_dialect(dialect_name: str = "sqlite"):
    """Create a mock SQLAlchemy dialect using MagicMock."""
    mock_dialect = mock.MagicMock()  # noqa: TID251
    mock_dialect.name = dialect_name

    # Mock the statement compiler chain to return proper compiled SQL
    def mock_statement_compiler(dialect, element, **kw):
        """Mock statement compiler that returns appropriate SQL based on element type."""
        mock_compiled = mock.MagicMock()  # noqa: TID251

        # Determine what SQL to return based on the element type
        if hasattr(element, "_is_subquery") and element._is_subquery:
            # This is a subquery - return the expected subquery SQL
            mock_compiled.__str__ = lambda self: "SELECT * \nFROM my_table"
        elif hasattr(element, "get_final_froms"):
            # This is a select statement - use the non-deprecated method
            try:
                final_froms = element.get_final_froms()
                if final_froms:
                    mock_compiled.__str__ = lambda self: "SELECT * \nFROM my_table"
                else:
                    mock_compiled.__str__ = lambda self: str(element)
            except Exception:
                # Fallback if get_final_froms() fails
                mock_compiled.__str__ = lambda self: "SELECT * \nFROM my_table"
        elif hasattr(element, "name"):
            # This is a table - return the table name
            mock_compiled.__str__ = lambda self: element.name
        else:
            # Fallback - try to get a reasonable string representation
            mock_compiled.__str__ = lambda self: str(element)

        return mock_compiled

    mock_dialect.statement_compiler = mock_statement_compiler

    return mock_dialect


class MockSaEngine:
    def __init__(self, dialect_name: str = "sqlite"):
        self.dialect = create_mock_dialect(dialect_name)

    def connect(self) -> None:
        pass


class MockResult:
    def fetchmany(self, recordcount: int):
        return None


class MockConnection:
    def execute(self, query: str):
        return MockResult()


_batch_selectable = sa.Table("my_table", sa.MetaData(), schema=None)


@pytest.fixture
def batch_selectable() -> sa.Table:
    return _batch_selectable


class MockSqlAlchemyExecutionEngine(SqlAlchemyExecutionEngine):
    def __init__(self, create_temp_table: bool = True, *args, **kwargs):
        self.engine = MockSaEngine("sqlite")  # type: ignore[assignment] # FIXME CoP
        self._create_temp_table = create_temp_table
        self._connection = MockConnection()  # type: ignore[assignment] # FIXME CoP

        self._batch_manager = None  # type: ignore[assignment] # FIXME CoP

    @override
    def get_compute_domain(
        self,
        domain_kwargs: dict,
        domain_type: Union[str, MetricDomainTypes],
        accessor_keys: Optional[Iterable[str]] = None,
    ) -> tuple[sa.Table, dict, dict]:
        return _batch_selectable, {}, {}


class MockBatchManager:
    active_batch_data = SqlAlchemyBatchData(
        execution_engine=MockSqlAlchemyExecutionEngine(),
        table_name="my_table",
    )

    def save_batch_data(self) -> None: ...


@pytest.fixture
def mock_sqlalchemy_execution_engine():
    execution_engine = MockSqlAlchemyExecutionEngine()
    execution_engine._batch_manager = MockBatchManager()
    return execution_engine
