from typing import Mapping, Optional

import pandas as pd
import pytest

from great_expectations.compatibility.typing_extensions import override
from great_expectations.data_context import AbstractDataContext
from great_expectations.datasource.fluent.sql_datasource import TableAsset
from great_expectations.datasource.fluent.sql_server_datasource import (
    SQLServerAuthConnectionDetails,
)
from tests.integration.sql_session_manager import SessionSQLEngineManager
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)
from tests.integration.test_utils.data_source_config.sql import SQLBatchTestSetup
from tests.test_utils import get_default_mssql_url


class MSSQLDatasourceTestConfig(DataSourceTestConfig):
    @property
    @override
    def label(self) -> str:
        return "mssql"

    @property
    @override
    def pytest_mark(self) -> pytest.MarkDecorator:
        return pytest.mark.mssql

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
        engine_manager: Optional[SessionSQLEngineManager] = None,
    ) -> BatchTestSetup:
        return MSSQLBatchTestSetup(
            data=data,
            config=self,
            extra_data=extra_data,
            table_name=self.table_name,
            context=context,
            engine_manager=engine_manager,
        )


class MSSQLBatchTestSetup(SQLBatchTestSetup[MSSQLDatasourceTestConfig]):
    @property
    @override
    def connection_string(self) -> str:
        return get_default_mssql_url()

    @property
    @override
    def use_schema(self) -> bool:
        return True

    @override
    def make_asset(self) -> TableAsset:
        connection_details = SQLServerAuthConnectionDetails(
            host="127.0.0.1",
            port=1433,
            database="test_ci",
            schema="dbo",
            username="sa",
            password="ReallyStrongPwd1234%^&*",
            driver="ODBC Driver 18 for SQL Server",
            encrypt="Optional",
        )
        return self.context.data_sources.add_sql_server(
            name=self._random_resource_name(),
            connection_string=connection_details,
        ).add_table_asset(
            name=self._random_resource_name(),
            table_name=self.table_name,
            schema_name=self.schema,
        )
