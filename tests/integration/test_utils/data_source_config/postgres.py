from typing import Mapping

import pandas as pd
import pytest

from great_expectations.compatibility.typing_extensions import override
from great_expectations.data_context import AbstractDataContext
from great_expectations.datasource.fluent.sql_datasource import TableAsset
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)
from tests.integration.test_utils.data_source_config.sql import SQLBatchTestSetup


class PostgreSQLDatasourceTestConfig(DataSourceTestConfig):
    @property
    @override
    def label(self) -> str:
        return "postgresql"

    @property
    @override
    def pytest_mark(self) -> pytest.MarkDecorator:
        return pytest.mark.postgresql

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
    ) -> BatchTestSetup:
        return PostgresBatchTestSetup(
            data=data,
            config=self,
            extra_data=extra_data,
            table_name=self.table_name,
            context=context,
        )


class PostgresBatchTestSetup(SQLBatchTestSetup[PostgreSQLDatasourceTestConfig]):
    @property
    @override
    def connection_string(self) -> str:
        return "postgresql+psycopg2://postgres@localhost:5432/test_ci"

    @property
    @override
    def use_schema(self) -> bool:
        return False

    @override
    def make_asset(self) -> TableAsset:
        return self.context.data_sources.add_postgres(
            name=self._random_resource_name(), connection_string=self.connection_string
        ).add_table_asset(
            name=self._random_resource_name(),
            table_name=self.table_name,
            schema_name=self.schema,
        )
