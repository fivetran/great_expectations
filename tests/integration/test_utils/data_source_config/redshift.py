from functools import cached_property
from typing import Mapping

import pandas as pd
import pytest

from great_expectations.compatibility.pydantic import BaseSettings
from great_expectations.compatibility.typing_extensions import override
from great_expectations.datasource.fluent.sql_datasource import TableAsset
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)
from tests.integration.test_utils.data_source_config.sql import SQLBatchTestSetup


class RedshiftDatasourceTestConfig(DataSourceTestConfig):
    @property
    @override
    def label(self) -> str:
        return "redshift"

    @property
    @override
    def pytest_mark(self) -> pytest.MarkDecorator:
        return pytest.mark.redshift

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
    ) -> BatchTestSetup:
        return RedshiftBatchTestSetup(
            data=data,
            config=self,
            extra_data=extra_data,
            table_name=self.table_name,
        )


class RedshiftBatchTestSetup(SQLBatchTestSetup[RedshiftDatasourceTestConfig]):
    @property
    @override
    def connection_string(self) -> str:
        return self.redshift_connection_config.connection_string

    @property
    @override
    def use_schema(self) -> bool:
        return False

    @override
    def make_asset(self) -> TableAsset:
        return self.context.data_sources.add_redshift(
            name=self._random_resource_name(), connection_string=self.connection_string
        ).add_table_asset(
            name=self._random_resource_name(),
            table_name=self.table_name,
            schema_name=self.schema,
        )

    @cached_property
    def redshift_connection_config(self) -> RedshiftDatasourceTestConfig:
        return RedshiftConnectionConfig()


class RedshiftConnectionConfig(BaseSettings):
    # BaseSettings will retrieve this environment variable
    REDSHIFT_DATABASE: str
    REDSHIFT_HOST: str
    REDSHIFT_PASSWORD: str
    REDSHIFT_PORT: int
    REDSHIFT_USERNAME: str
    REDSHIFT_SSLMODE: str

    @property
    def connection_string(self) -> str:
        return (
            f"redshift+psycopg2://{self.REDSHIFT_USERNAME}:{self.REDSHIFT_PASSWORD}@"
            f"{self.REDSHIFT_HOST}:{self.REDSHIFT_PORT}/{self.REDSHIFT_DATABASE}?"
            f"sslmode={self.REDSHIFT_SSLMODE}"
        )
