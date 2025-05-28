from typing import Mapping, Optional

import pandas as pd
import pytest

from great_expectations.compatibility.pydantic import BaseSettings
from great_expectations.compatibility.typing_extensions import override
from great_expectations.data_context import AbstractDataContext
from great_expectations.datasource.fluent.sql_datasource import TableAsset
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)
from tests.integration.test_utils.data_source_config.sql import SQLBatchTestSetup


class SnowflakeDatasourceTestConfig(DataSourceTestConfig):
    @property
    @override
    def label(self) -> str:
        return "snowflake"

    @property
    @override
    def pytest_mark(self) -> pytest.MarkDecorator:
        return pytest.mark.snowflake

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
    ) -> BatchTestSetup:
        return SnowflakeBatchTestSetup(
            data=data,
            config=self,
            extra_data=extra_data,
            table_name=self.table_name,
            context=context,
        )


class SnowflakeConnectionConfig(BaseSettings):
    """This class retrieves these values from the environment.
    If you're testing locally, you can use your Snowflake creds
    and test against your own Snowflake account.
    """

    SNOWFLAKE_USER: str
    SNOWFLAKE_PW: str
    SNOWFLAKE_ACCOUNT: str
    SNOWFLAKE_DATABASE: str
    SNOWFLAKE_WAREHOUSE: str
    SNOWFLAKE_ROLE: str

    @property
    def connection_string(self) -> str:
        # Note: we don't specify the schema here because it will be created dynamically, and we pass
        # it into the `data_sources.add_snowflake` call.
        return (
            f"snowflake://{self.SNOWFLAKE_USER}:{self.SNOWFLAKE_PW}"
            f"@{self.SNOWFLAKE_ACCOUNT}/{self.SNOWFLAKE_DATABASE}"
            f"?warehouse={self.SNOWFLAKE_WAREHOUSE}&role={self.SNOWFLAKE_ROLE}"
        )


class SnowflakeBatchTestSetup(SQLBatchTestSetup[SnowflakeDatasourceTestConfig]):
    @property
    @override
    def connection_string(self) -> str:
        return self.snowflake_connection_config.connection_string

    @property
    @override
    def use_schema(self) -> bool:
        return True

    def __init__(
        self,
        config: SnowflakeDatasourceTestConfig,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
        table_name: Optional[str] = None,
    ) -> None:
        self.snowflake_connection_config = SnowflakeConnectionConfig()  # type: ignore[call-arg]  # retrieves env vars
        super().__init__(
            config=config, data=data, extra_data=extra_data, table_name=table_name, context=context
        )

    @override
    def make_asset(self) -> TableAsset:
        schema = self.schema
        assert schema
        return self.context.data_sources.add_snowflake(
            name=self._random_resource_name(),
            account=self.snowflake_connection_config.SNOWFLAKE_ACCOUNT,
            user=self.snowflake_connection_config.SNOWFLAKE_USER,
            password=self.snowflake_connection_config.SNOWFLAKE_PW,
            database=self.snowflake_connection_config.SNOWFLAKE_DATABASE,
            schema=schema,
            warehouse=self.snowflake_connection_config.SNOWFLAKE_WAREHOUSE,
            role=self.snowflake_connection_config.SNOWFLAKE_ROLE,
        ).add_table_asset(
            name=self._random_resource_name(),
            table_name=self.table_name,
        )
