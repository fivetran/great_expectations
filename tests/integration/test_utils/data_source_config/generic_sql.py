from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping, Optional

import pytest

from great_expectations.compatibility.sqlalchemy import sqltypes
from great_expectations.compatibility.typing_extensions import override
from great_expectations.data_context import AbstractDataContext
from tests.integration.sql_session_manager import SessionSQLEngineManager
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)
from tests.integration.test_utils.data_source_config.sql import (
    InferrableTypesLookup,
    SQLBatchTestSetup,
)

if TYPE_CHECKING:
    import pandas as pd

    from great_expectations.data_context import AbstractDataContext
    from great_expectations.datasource.fluent.sql_datasource import TableAsset
    from tests.integration.sql_session_manager import SessionSQLEngineManager


@dataclass(frozen=True)
class GenericSQLDatasourceTestConfig(DataSourceTestConfig):
    """Config for testing against any SQL backend via a caller-provided connection string.

    Unlike the dialect-specific configs (e.g. PostgreSQLDatasourceTestConfig),
    the connection string is not baked in — it must be supplied at construction
    time.  This makes the config reusable across any SQLAlchemy-compatible
    database.
    """

    connection_string: str = ""

    @property
    @override
    def label(self) -> str:
        return "generic_sql"

    @property
    @override
    def pytest_mark(self) -> pytest.MarkDecorator:
        return pytest.mark.generic_sql

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
        engine_manager: Optional[SessionSQLEngineManager] = None,
    ) -> BatchTestSetup:
        return GenericSQLBatchTestSetup(
            data=data,
            config=self,
            extra_data=extra_data,
            table_name=self.table_name,
            context=context,
            engine_manager=engine_manager,
        )


class GenericSQLBatchTestSetup(SQLBatchTestSetup[GenericSQLDatasourceTestConfig]):
    """Batch setup that works with any SQLAlchemy connection string.

    Uses ``context.data_sources.add_sql`` — the dialect-agnostic datasource —
    so callers only need to provide a valid connection string.

    If no connection_string is provided in the config, reads from the
    GX_TEST_GENERIC_SQL_CONNECTION_STRING environment variable.
    """

    def __init__(
        self,
        config: GenericSQLDatasourceTestConfig,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
        table_name: Optional[str] = None,
        engine_manager: Optional[SessionSQLEngineManager] = None,
    ) -> None:
        # Read from environment variable if connection_string is empty
        self._connection_string = config.connection_string
        if not self._connection_string:
            self._connection_string = os.environ.get("GX_TEST_GENERIC_SQL_CONNECTION_STRING", "")
        if not self._connection_string:
            raise ValueError(
                "GenericSQLBatchTestSetup requires a connection string. "
                "Either pass connection_string to GenericSQLDatasourceTestConfig "
                "or set GX_TEST_GENERIC_SQL_CONNECTION_STRING environment variable."
            )
        super().__init__(
            config=config,
            data=data,
            extra_data=extra_data,
            table_name=table_name,
            engine_manager=engine_manager,
            context=context,
        )

    @override
    def build_connection_string(self, schema: str | None = None) -> str:
        return self._connection_string

    @property
    @override
    def use_schema(self) -> bool:
        return False

    @override
    def make_asset(self) -> TableAsset:
        return self.context.data_sources.add_sql(
            name=self._random_resource_name(),
            connection_string=self.build_connection_string(),
        ).add_table_asset(
            name=self._random_resource_name(),
            table_name=self.table_name,
        )

    @property
    @override
    def inferrable_types_lookup(self) -> InferrableTypesLookup:
        # databricks requires a length for VARCHAR
        overrides: InferrableTypesLookup = {
            str: sqltypes.VARCHAR(255),
        }
        return super().inferrable_types_lookup | overrides
