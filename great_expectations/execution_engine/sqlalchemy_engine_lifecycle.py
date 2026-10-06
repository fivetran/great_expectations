"""Release the DB-API connections pooled by SQLAlchemy engines that GX creates.

An engine's pool keeps the DB-API connections it opens until the engine is disposed. GX
creates engines on behalf of datasources and execution engines, which have no close step of
their own, so nothing disposes them: when such an engine is garbage collected, its pooled
connections are finalized while still open. For sqlite3 that emits a ResourceWarning from
Python 3.13, attributed to whatever code happens to be running when the collector does.
"""

from __future__ import annotations

import contextlib
import weakref
from typing import TYPE_CHECKING, Any

from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa

if TYPE_CHECKING:
    from great_expectations.compatibility import sqlalchemy


def _close_quietly(dbapi_connection: Any) -> None:
    # Runs from the garbage collector, possibly on another thread than the one that opened the
    # connection (which sqlite3 refuses by default). A failure here leaves the connection as it
    # would have been without this hook, so there is nothing better to do with it.
    with contextlib.suppress(Exception):
        dbapi_connection.close()


def _close_with_its_pool(dbapi_connection: Any, connection_record: Any) -> None:
    # Keyed on the pool's record for the connection, not on the engine: the pool refers back to
    # the engine, so a finalizer that held the pool would keep the engine alive. The record dies
    # with its pool, and closing an already closed connection is a no-op.
    weakref.finalize(connection_record, _close_quietly, dbapi_connection)


def close_connections_when_collected(engine: sqlalchemy.Engine) -> sqlalchemy.Engine:
    """Close every DB-API connection the engine's pool opens once that pool is garbage collected.

    Connections are only closed once no one can use them any more; an engine that is still
    reachable, and every connection checked out of it, is unaffected. Covers pools the engine
    recreates on `dispose()`. Idempotent. Anything that is not an `Engine` (an execution engine
    can hold a `Connection` instead) is returned untouched.

    Returns:
        The same engine, so a call can wrap the expression that creates it.
    """
    if not isinstance(engine, sa.engine.Engine):
        return engine
    if not sa.event.contains(engine, "connect", _close_with_its_pool):
        sa.event.listen(engine, "connect", _close_with_its_pool)
    return engine
