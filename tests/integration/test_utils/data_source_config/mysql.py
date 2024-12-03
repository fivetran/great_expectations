from typing import Dict, Mapping, Type

import pandas as pd
import pytest

from great_expectations.compatibility.sqlalchemy import TypeEngine, sqltypes
from great_expectations.compatibility.typing_extensions import override
from great_expectations.datasource.fluent.sql_datasource import TableAsset
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)
from tests.integration.test_utils.data_source_config.databricks import cached_property
from tests.integration.test_utils.data_source_config.sql import SQLBatchTestSetup


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
    ) -> BatchTestSetup:
        return MySQLBatchTestSetup(
            data=data,
            config=self,
            extra_data=extra_data,
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
    def inferrable_types_lookup(self) -> Dict[Type, TypeEngine]:
        overrides = {
            str: sqltypes.VARCHAR(255),  # mysql requires a length for VARCHAR
        }
        return super().inferrable_types_lookup | overrides

    @cached_property
    @override
    def asset(self) -> TableAsset:
        return self.context.data_sources.add_sql(
            name=self._random_resource_name(), connection_string=self.connection_string
        ).add_table_asset(
            name=self._random_resource_name(),
            table_name=self.table_name,
            schema_name=self.schema,
        )
