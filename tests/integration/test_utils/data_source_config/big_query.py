from functools import cached_property
from typing import Mapping

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


class BigQueryDatasourceTestConfig(DataSourceTestConfig):
    @property
    @override
    def label(self) -> str:
        return "big-query"

    @property
    @override
    def pytest_mark(self) -> pytest.MarkDecorator:
        return pytest.mark.bigquery

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
    ) -> BatchTestSetup:
        return BigQueryBatchTestSetup(
            data=data,
            config=self,
            extra_data=extra_data,
        )


class BigQueryConnectionConfig(BaseSettings):
    GE_TEST_GCP_PROJECT: str
    GE_TEST_BIGQUERY_DATASET: str
    GOOGLE_APPLICATION_CREDENTIALS: str

    @property
    def connection_string(self) -> str:
        return f"bigquery://{self.GE_TEST_GCP_PROJECT}/{self.GE_TEST_BIGQUERY_DATASET}?credentials_path={self.GOOGLE_APPLICATION_CREDENTIALS}"


class BigQueryBatchTestSetup(SQLBatchTestSetup[BigQueryDatasourceTestConfig]):
    @property
    @override
    def connection_string(self) -> str:
        return self.big_query_connection_config.connection_string

    @property
    @override
    def use_schema(self) -> bool:
        return False

    @override
    def make_batch(self) -> Batch:
        name = self._random_resource_name()
        return (
            self.context.data_sources.add_sql(name=name, connection_string=self.connection_string)
            .add_table_asset(
                name=name,
                table_name=self.table_name,
                schema_name=self.schema,
            )
            .add_batch_definition_whole_table(name=name)
            .get_batch()
        )

    @cached_property
    def big_query_connection_config(self) -> BigQueryConnectionConfig:
        return BigQueryConnectionConfig()  # type: ignore[call-arg]  # retrieves env vars
