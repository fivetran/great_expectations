from __future__ import annotations

from typing import TYPE_CHECKING

from great_expectations.core.batch import BatchData

if TYPE_CHECKING:
    import duckdb


class DuckDBBatchData(BatchData):
    """Wraps a DuckDB relation so it can be cached and re-queried as an execution engine batch.

    A `duckdb.DuckDBPyRelation` is a lazy, chainable query (comparable to a SQLAlchemy
    Selectable) rather than materialized data, so wrapping it here costs nothing until a
    metric actually executes it.
    """

    def __init__(self, execution_engine, relation: duckdb.DuckDBPyRelation) -> None:
        super().__init__(execution_engine=execution_engine)
        self._relation = relation

    @property
    def relation(self) -> duckdb.DuckDBPyRelation:
        return self._relation
