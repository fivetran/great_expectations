"""Schema names supplied as quoted identifiers.

Wrapping an identifier in the dialect's quote characters is how a user asks GX to
use that identifier verbatim instead of case-folding it. ``table_name`` supports
this: a quoted value is unwrapped and rebuilt as a quoted SQLAlchemy identifier,
so the quote characters govern the emitted SQL rather than becoming part of the
name. These tests pin down whether a schema named the same way reaches the same
schema.

The shared PostgreSQL setup routes its schema through the connection string's
``search_path``, which never passes through GX's identifier handling, so these
tests name the schema on the asset instead.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations import get_context
from great_expectations.compatibility.typing_extensions import override
from tests.integration.test_utils.data_source_config.postgres import (
    PostgresBatchTestSetup,
    PostgreSQLDatasourceTestConfig,
)

if TYPE_CHECKING:
    from great_expectations.datasource.fluent.sql_datasource import TableAsset

DATA_FRAME = pd.DataFrame(
    {
        "words": [
            "apple",
            "banana",
            "cherry",
        ],
    }
)


class _SchemaOnAssetSetup(PostgresBatchTestSetup):
    """Reaches the table through the asset's schema rather than ``search_path``.

    Subclasses decide whether the schema is handed over bare or bracketed by quotes;
    that is the single variable these tests turn.
    """

    quote_schema: bool

    @override
    def make_asset(self) -> TableAsset:
        assert self.schema is not None, "this setup requires a schema-qualified table"
        schema_name = f'"{self.schema}"' if self.quote_schema else self.schema
        return self.context.data_sources.add_postgres(
            name=self._random_resource_name(),
            # Deliberately no search_path: the schema has to come from the asset.
            connection_string=self.build_connection_string(),
        ).add_table_asset(
            name=self._random_resource_name(),
            table_name=self.table_name,
            schema_name=schema_name,
        )


class _BareSchemaSetup(_SchemaOnAssetSetup):
    quote_schema = False


class _QuotedSchemaSetup(_SchemaOnAssetSetup):
    quote_schema = True


def _validate_row_count(setup_class: type[_SchemaOnAssetSetup]) -> None:
    """Read the schema-qualified table back through a trivial expectation."""
    setup = setup_class(
        config=PostgreSQLDatasourceTestConfig(),
        data=DATA_FRAME,
        extra_data={},
        context=get_context(mode="ephemeral"),
    )
    with setup.batch_test_context() as batch:
        result = batch.validate(gxe.ExpectTableRowCountToEqual(value=3))

    assert result.success


@pytest.mark.postgresql
def test_bare_schema_name_reaches_the_table() -> None:
    """Control: an unquoted schema named on the asset resolves to that schema.

    Establishes that everything except the quoting works, so the companion test's
    failure can only be about the quote characters.
    """
    _validate_row_count(_BareSchemaSetup)


@pytest.mark.postgresql
@pytest.mark.xfail(
    strict=True,
    reason=(
        "A quoted schema keeps its quote characters inside the identifier instead of "
        "being rebuilt as a quoted identifier, so the emitted SQL targets a schema "
        'whose name literally contains quotes (FROM """gx_ci_test_x""".table). Unlike '
        "table_name, a schema is never unwrapped into a quoted SQLAlchemy identifier."
    ),
)
def test_quoted_schema_name_reaches_the_table() -> None:
    """A schema quoted to preserve it verbatim should resolve to that same schema.

    Quoting is GX's documented way to keep an identifier from being case-folded, so
    a schema handed over quoted has to reach the schema the user named. Today it
    does not, which also means a case-sensitive schema is unreachable: folding is
    the only other path, and it destroys the case the quotes were meant to keep.
    """
    _validate_row_count(_QuotedSchemaSetup)
