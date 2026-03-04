from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Mapping, Optional

import pytest

from great_expectations.compatibility.pydantic import BaseSettings
from great_expectations.compatibility.sqlalchemy import sqltypes
from great_expectations.compatibility.typing_extensions import override
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


class DatabricksDatasourceTestConfig(DataSourceTestConfig):
    @property
    @override
    def label(self) -> str:
        return "databricks"

    @property
    @override
    def pytest_mark(self) -> pytest.MarkDecorator:
        return pytest.mark.databricks

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
        engine_manager: Optional[SessionSQLEngineManager] = None,
    ) -> BatchTestSetup:
        return DatabricksBatchTestSetup(
            data=data,
            config=self,
            extra_data=extra_data,
            table_name=self.table_name,
            context=context,
            engine_manager=engine_manager,
        )


class DatabricksBatchTestSetup(SQLBatchTestSetup[DatabricksDatasourceTestConfig]):
    @override
    def build_connection_string(self, schema: str | None = None) -> str:
        return self._databrics_connection_config.build_connection_string(schema=schema)

    @property
    @override
    def use_schema(self) -> bool:
        return True

    @property
    @override
    def inferrable_types_lookup(self) -> InferrableTypesLookup:
        # databricks requires a length for VARCHAR
        overrides: InferrableTypesLookup = {
            str: sqltypes.VARCHAR(255),
        }
        return super().inferrable_types_lookup | overrides

    @cached_property
    def _databrics_connection_config(self) -> DatabricksConnectionConfig:
        return DatabricksConnectionConfig()  # type: ignore[call-arg]  # retrieves env vars

    @override
    def make_asset(self) -> TableAsset:
        assert self.schema
        return self.context.data_sources.add_databricks_sql(
            name=self._random_resource_name(),
            connection_string=self.build_connection_string(schema=self.schema),
        ).add_table_asset(
            name=self._random_resource_name(),
            table_name=self.table_name,
        )


class DatabricksConnectionConfig(BaseSettings):
    databricks_token: str
    databricks_host: str
    databricks_http_path: str

    def build_connection_string(self, schema: str | None = None) -> str:
        base = (
            "databricks://token:"
            f"{self.databricks_token}@{self.databricks_host}:443"
            f"?http_path={self.databricks_http_path}&catalog=ci"
        )
        if schema:
            return f"{base}&schema={schema}"
        return base
