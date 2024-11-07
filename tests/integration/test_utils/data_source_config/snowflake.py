from typing import Mapping, Union

import pandas as pd
import pytest

from great_expectations.compatibility.pydantic import BaseSettings
from great_expectations.compatibility.typing_extensions import override
from great_expectations.datasource.fluent.interfaces import Batch
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
    ) -> BatchTestSetup:
        return SnowflakeBatchTestSetup(
            data=data,
            config=self,
            extra_data=extra_data,
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
    SNOWFLAKE_SCHEMA: str
    SNOWFLAKE_WAREHOUSE: str
    SNOWFLAKE_ROLE: str = "PUBLIC"

    @property
    def connection_string(self) -> str:
        return (
            f"snowflake://{self.SNOWFLAKE_USER}:{self.SNOWFLAKE_PW}"
            f"@{self.SNOWFLAKE_ACCOUNT}/{self.SNOWFLAKE_DATABASE}/{self.SNOWFLAKE_SCHEMA}"
            f"?warehouse={self.SNOWFLAKE_WAREHOUSE}&role={self.SNOWFLAKE_ROLE}"
        )


class SnowflakeBatchTestSetup(SQLBatchTestSetup[SnowflakeDatasourceTestConfig]):
    @override
    @property
    def connection_string(self) -> str:
        return self.snowflake_connection_config.connection_string

    @override
    @property
    def schema(self) -> Union[str, None]:
        return self.snowflake_connection_config.SNOWFLAKE_SCHEMA

    def __init__(
        self,
        config: SnowflakeDatasourceTestConfig,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
    ) -> None:
        self.snowflake_connection_config = SnowflakeConnectionConfig()  # type: ignore[call-arg]  # retrieves env vars
        super().__init__(config=config, data=data, extra_data=extra_data)

    @override
    def make_batch(self) -> Batch:
        name = self._random_resource_name()
        return (
            self.context.data_sources.add_snowflake(
                name=name,
                account=self.snowflake_connection_config.SNOWFLAKE_ACCOUNT,
                user=self.snowflake_connection_config.SNOWFLAKE_USER,
                password=self.snowflake_connection_config.SNOWFLAKE_PW,
                database=self.snowflake_connection_config.SNOWFLAKE_DATABASE,
                schema=self.snowflake_connection_config.SNOWFLAKE_SCHEMA,
                warehouse=self.snowflake_connection_config.SNOWFLAKE_WAREHOUSE,
                role=self.snowflake_connection_config.SNOWFLAKE_ROLE,
            )
            .add_table_asset(
                name=name,
                table_name=self.table_name,
            )
            .add_batch_definition_whole_table(name=name)
            .get_batch()
        )
