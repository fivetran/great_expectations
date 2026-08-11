from typing import TYPE_CHECKING, Sequence

from great_expectations.compatibility.sqlalchemy import TextClause
from tests.integration.test_utils.data_source_config.backend_spec import TableSchemaItemFactory

if TYPE_CHECKING:
    import sqlalchemy as sa  # type-only, exactly as `sql.py` and `backend_spec.py` do it


def _clickhouse_table_engines() -> Sequence["sa.sql.schema.SchemaItem"]:
    from clickhouse_sqlalchemy import engines

    return (engines.MergeTree(order_by=TextClause("tuple()")),)


# Alias-conformance binding: this is the value the record declares, and its annotation is the
# framework's alias rather than a restatement of the signature.
_CLICKHOUSE_TABLE_SCHEMA_ITEMS: TableSchemaItemFactory = _clickhouse_table_engines
