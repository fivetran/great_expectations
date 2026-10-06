from __future__ import annotations

import gc
import sqlite3
import subprocess
import sys
import textwrap
import threading
import weakref
from typing import TYPE_CHECKING, Any, Callable, Iterator

import pytest

from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.datasource.fluent import SqliteDatasource
from great_expectations.execution_engine import SqlAlchemyExecutionEngine
from great_expectations.execution_engine.sqlalchemy_engine_lifecycle import (
    _close_quietly,
    _close_with_its_pool,
    close_connections_when_collected,
)

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

pytestmark = pytest.mark.unit


@pytest.fixture
def opened_dbapi_connections() -> Iterator[list[Any]]:
    """Every DB-API connection any SQLAlchemy pool opens during the test.

    Holding them here keeps them from being finalized, so a test can look at whether something
    closed them; without that, the interpreter would close them itself on collection.
    """
    opened: list[Any] = []

    def _record(dbapi_connection: Any, connection_record: Any) -> None:
        opened.append(dbapi_connection)

    sa.event.listen(sa.pool.Pool, "connect", _record)
    try:
        yield opened
    finally:
        sa.event.remove(sa.pool.Pool, "connect", _record)
        for dbapi_connection in opened:
            dbapi_connection.close()


def _is_closed(dbapi_connection: sqlite3.Connection) -> bool:
    try:
        dbapi_connection.execute("select 1")
    except sqlite3.ProgrammingError:
        return True
    return False


def _use_and_drop(make_engine: Callable[[], sa.engine.Engine]) -> weakref.ref:
    engine = make_engine()
    with engine.connect() as connection:
        connection.execute(sa.text("select 1"))
    engine_ref = weakref.ref(engine)
    del engine, connection
    gc.collect()
    return engine_ref


@pytest.mark.parametrize("url", ["sqlite://", "sqlite:///{tmp_path}/db.sqlite"])
def test_pooled_connection_is_closed_once_its_engine_is_collected(
    url: str, tmp_path, opened_dbapi_connections: list[Any]
):
    engine_ref = _use_and_drop(
        lambda: close_connections_when_collected(sa.create_engine(url.format(tmp_path=tmp_path)))
    )

    # The finalizer must not keep the engine alive: the pool refers back to it.
    assert engine_ref() is None
    assert len(opened_dbapi_connections) == 1
    assert _is_closed(opened_dbapi_connections[0])


def test_unguarded_engine_leaves_its_pooled_connection_open(opened_dbapi_connections: list[Any]):
    # Control: what the guard fixes. Without it the pool's connection outlives the engine.
    engine_ref = _use_and_drop(lambda: sa.create_engine("sqlite://"))

    assert engine_ref() is None
    assert len(opened_dbapi_connections) == 1
    assert not _is_closed(opened_dbapi_connections[0])


def test_connections_of_a_reachable_engine_stay_open(opened_dbapi_connections: list[Any]):
    engine = close_connections_when_collected(sa.create_engine("sqlite://"))
    with engine.connect() as connection:
        connection.execute(sa.text("create table t (x int)"))
    gc.collect()

    with engine.connect() as connection:
        # The in-memory table survives only if the pooled connection was never closed.
        connection.execute(sa.text("select * from t"))
    assert len(opened_dbapi_connections) == 1
    assert not _is_closed(opened_dbapi_connections[0])


def test_pool_recreated_by_dispose_is_covered(opened_dbapi_connections: list[Any]):
    def make_engine() -> sa.engine.Engine:
        engine = close_connections_when_collected(sa.create_engine("sqlite://"))
        with engine.connect() as connection:
            connection.execute(sa.text("select 1"))
        engine.dispose()
        return engine

    engine_ref = _use_and_drop(make_engine)

    assert engine_ref() is None
    assert len(opened_dbapi_connections) == 2
    assert all(_is_closed(c) for c in opened_dbapi_connections)


def test_reconnecting_a_pool_record_keeps_one_finalizer_for_it(tmp_path):
    # A file database gets a QueuePool, which hands the same record back after invalidation.
    engine = close_connections_when_collected(sa.create_engine(f"sqlite:///{tmp_path}/db.sqlite"))
    records: list[Any] = []
    sa.event.listen(engine, "connect", lambda _, record: records.append(record))
    for _ in range(3):
        with engine.connect() as connection:
            connection.execute(sa.text("select 1"))
            # Closes the DB-API connection; the next checkout reconnects on the same record.
            connection.invalidate()

    assert len(records) == 3
    assert len({id(record) for record in records}) == 1
    finalizers = [
        obj
        for obj in gc.get_objects()
        if isinstance(obj, weakref.finalize) and obj.alive and obj.peek()[0] is records[0]
    ]
    # One per reconnect would pin every connection the pool already closed, for as long as the
    # engine lives.
    assert len(finalizers) == 1
    engine.dispose()


def test_connection_of_a_reachable_engine_is_still_open_in_an_exit_handler():
    # The exit handler is registered before anything can create a `weakref.finalize`, whose
    # own exit hook would then run ahead of it.
    script = textwrap.dedent(
        """
        import atexit

        def use_engine_at_exit():
            with engine.connect() as connection:
                connection.execute(sa.text("select * from t"))
            print("connection usable at exit")

        atexit.register(use_engine_at_exit)

        from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
        from great_expectations.execution_engine.sqlalchemy_engine_lifecycle import (
            close_connections_when_collected,
        )

        engine = close_connections_when_collected(sa.create_engine("sqlite://"))
        with engine.connect() as connection:
            connection.execute(sa.text("create table t (x int)"))
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True, timeout=120
    )

    assert "connection usable at exit" in result.stdout, result.stderr


def test_a_close_that_raises_is_swallowed():
    # sqlite3 refuses to close a connection from a thread other than the one that opened it,
    # which is where the garbage collector can run the finalizer.
    opened: list[sqlite3.Connection] = []
    opener = threading.Thread(target=lambda: opened.append(sqlite3.connect(":memory:")))
    opener.start()
    opener.join()
    (dbapi_connection,) = opened
    with pytest.raises(sqlite3.ProgrammingError):
        dbapi_connection.close()

    _close_quietly(dbapi_connection)

    closer = threading.Thread(target=dbapi_connection.close)
    closer.start()
    closer.join()


def test_leaves_an_engine_of_another_dialect_alone(mocker: MockerFixture):
    # Closing from the collector would run a network driver's close I/O on whatever thread
    # triggered the collection.
    engine = sa.create_engine("sqlite://")
    mocker.patch.object(engine.dialect, "name", "snowflake")

    assert close_connections_when_collected(engine) is engine
    assert not sa.event.contains(engine, "connect", _close_with_its_pool)


def test_is_idempotent(mocker: MockerFixture):
    engine = sa.create_engine("sqlite://")
    listen = mocker.patch.object(sa.event, "listen", wraps=sa.event.listen)

    assert close_connections_when_collected(engine) is engine
    assert close_connections_when_collected(engine) is engine

    listen.assert_called_once_with(engine, "connect", _close_with_its_pool)


def test_returns_a_non_engine_untouched(mocker: MockerFixture):
    not_an_engine = mocker.MagicMock()

    assert close_connections_when_collected(not_an_engine) is not_an_engine
    assert not_an_engine.mock_calls == []


def test_datasource_engine_connection_is_closed_once_the_datasource_is_collected(
    opened_dbapi_connections: list[Any],
):
    datasource = SqliteDatasource(name="ds", connection_string="sqlite://")
    datasource.test_connection()
    engine_ref = weakref.ref(datasource.get_engine())
    del datasource
    gc.collect()

    assert engine_ref() is None
    assert len(opened_dbapi_connections) == 1
    assert _is_closed(opened_dbapi_connections[0])


def test_execution_engine_guards_the_engine_it_creates():
    execution_engine = SqlAlchemyExecutionEngine(connection_string="sqlite://")

    assert sa.event.contains(execution_engine.engine, "connect", _close_with_its_pool)


def test_execution_engine_leaves_a_passed_engine_alone():
    engine = sa.create_engine("sqlite://")
    SqlAlchemyExecutionEngine(engine=engine)

    assert not sa.event.contains(engine, "connect", _close_with_its_pool)
