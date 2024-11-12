from typing import Mapping

import pandas as pd
import pytest

from great_expectations.compatibility.typing_extensions import override
from great_expectations.datasource.fluent.interfaces import Batch
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
    ) -> BatchTestSetup:
        return PostgresBatchTestSetup(
            data=data,
            config=self,
            extra_data=extra_data,
        )


class PostgresBatchTestSetup(SQLBatchTestSetup[PostgreSQLDatasourceTestConfig]):
    @override
    @property
    def connection_string(self) -> str:
        return "postgresql+psycopg2://postgres@localhost:5432/test_ci"

    @property
    @override
    def use_schema(self) -> bool:
        return False

    @override
    def make_batch(self) -> Batch:
        name = self._random_resource_name()
        return (
            self.context.data_sources.add_postgres(
                name=name, connection_string=self.connection_string
            )
            .add_table_asset(
                name=name,
                table_name=self.table_name,
                schema_name=self.schema,
            )
            .add_batch_definition_whole_table(name=name)
            .get_batch()
        )
