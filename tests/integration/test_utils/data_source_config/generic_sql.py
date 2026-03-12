from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping, Optional

import pytest

from great_expectations.compatibility.typing_extensions import override
from great_expectations.data_context import AbstractDataContext
from tests.integration.sql_session_manager import SessionSQLEngineManager
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)
from tests.integration.test_utils.data_source_config.sql import SQLBatchTestSetup

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
        return pytest.mark.sql

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
        engine_manager: Optional[SessionSQLEngineManager] = None,
    ) -> BatchTestSetup:
        if not self.connection_string:
            raise ValueError(
                "GenericSQLDatasourceTestConfig requires a non-empty connection_string."
            )
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
    """

    @override
    def build_connection_string(self, schema: str | None = None) -> str:
        return self.config.connection_string

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
