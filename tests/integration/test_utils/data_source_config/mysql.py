from typing import Mapping

import pandas as pd
import pytest

from great_expectations.compatibility.sqlalchemy import sqltypes
from great_expectations.compatibility.typing_extensions import override
from great_expectations.data_context import AbstractDataContext
from great_expectations.datasource.fluent.sql_datasource import TableAsset
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)
from tests.integration.test_utils.data_source_config.sql import (
    InferrableTypesLookup,
    SQLBatchTestSetup,
)


class MySQLDatasourceTestConfig(DataSourceTestConfig):
    @property
    @override
    def label(self) -> str:
        return "mysql"

    @property
    @override
    def pytest_mark(self) -> pytest.MarkDecorator:
        return pytest.mark.mysql

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
    ) -> BatchTestSetup:
        return MySQLBatchTestSetup(
            data=data,
            config=self,
            extra_data=extra_data,
            table_name=self.table_name,
            context=context,
        )


class MySQLBatchTestSetup(SQLBatchTestSetup[MySQLDatasourceTestConfig]):
    @property
    @override
    def connection_string(self) -> str:
        return "mysql+pymysql://root@localhost/test_ci"

    @property
    @override
    def use_schema(self) -> bool:
        return False

    @property
    @override
    def inferrable_types_lookup(self) -> InferrableTypesLookup:
        # mysql requires a length for VARCHAR
        overrides: InferrableTypesLookup = {
            str: sqltypes.VARCHAR(255),
        }
        return super().inferrable_types_lookup | overrides

    @override
    def make_asset(self) -> TableAsset:
        return self.context.data_sources.add_sql(
            name=self._random_resource_name(), connection_string=self.connection_string
        ).add_table_asset(
            name=self._random_resource_name(),
            table_name=self.table_name,
            schema_name=self.schema,
        )
