from __future__ import annotations

from typing import Any

import pytest

from great_expectations.execution_engine.sqlalchemy_execution_engine import (
    SqlAlchemyExecutionEngine,
)

pytestmark = pytest.mark.unit


class _FakeDialect:
    def __init__(self, name: str) -> None:
        self.name = name


class _FakeDbapiConn:
    def __init__(self) -> None:
        self.closed = False
        self.created_functions: list[tuple[str, int]] = []

    def create_function(self, name: str, num_params: int, fn: Any) -> None:
        # record that we attempted to register functions
        self.created_functions.append((name, num_params))

    def close(self) -> None:
        self.closed = True


class _FakeEngine:
    def __init__(self, dialect_name: str = "sqlite") -> None:
        self.dialect = _FakeDialect(dialect_name)
        self._raw_conn = _FakeDbapiConn()

    def raw_connection(self) -> _FakeDbapiConn:
        return self._raw_conn


def test_sqlite_adds_functions_and_closes_temp_raw_connection(monkeypatch) -> None:
    fake_engine = _FakeEngine("sqlite")

    listened: dict[str, Any] = {}

    # Prevent calling into real sqlalchemy.event.listen
    import sqlalchemy as sa

    def _fake_listen(engine, event_name, fn):
        listened["engine"] = engine
        listened["event"] = event_name
        listened["fn"] = fn

    monkeypatch.setattr(sa.event, "listen", _fake_listen)

    # Instantiate execution engine with fake engine; this should register sqlite functions
    ee = SqlAlchemyExecutionEngine(engine=fake_engine)  # noqa: F841

    # The raw connection used for immediate function registration must be closed
    assert fake_engine._raw_conn.closed is True

    # An event listener should have been registered for future connections
    assert listened.get("event") == "connect"
    assert listened.get("engine") is fake_engine
