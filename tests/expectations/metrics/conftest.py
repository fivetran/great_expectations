from typing import Iterable, Optional, Union

import pytest

from great_expectations.compatibility.sqlalchemy import (
    sqlalchemy as sa,
)
from great_expectations.core.metric_domain_types import MetricDomainTypes
from great_expectations.execution_engine import SqlAlchemyExecutionEngine
from great_expectations.execution_engine.sqlalchemy_batch_data import SqlAlchemyBatchData


class Dialect:
    def __init__(self, dialect: str):
        self.name = dialect


class MockSaEngine:
    def __init__(self, dialect: Dialect):
        self.dialect = dialect

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
        self.engine = MockSaEngine(dialect=Dialect("sqlite"))  # type: ignore[assignment] # FIXME CoP
        self._create_temp_table = create_temp_table
        self._connection = MockConnection()

        self._batch_manager = None

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
