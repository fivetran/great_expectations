from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Mapping

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

if TYPE_CHECKING:
    import pandas as pd


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
        context: AbstractDataContext,
    ) -> BatchTestSetup:
        return BigQueryBatchTestSetup(
            data=data,
            config=self,
            extra_data=extra_data,
            table_name=self.table_name,
            context=context,
        )


class BigQueryBatchTestSetup(SQLBatchTestSetup[BigQueryDatasourceTestConfig]):
    @property
    @override
    def connection_string(self) -> str:
        return self.big_query_connection_config.connection_string

    @property
    @override
    def use_schema(self) -> bool:
        # BigQuery calls its schemas "datasets". Their docs show that the sql way of defining a
        # dataset is to create a schema: https://cloud.google.com/bigquery/docs/datasets#sql
        return True

    @override
    def make_asset(self) -> TableAsset:
        return self.context.data_sources.add_sql(
            name=self._random_resource_name(), connection_string=self.connection_string
        ).add_table_asset(
            name=self._random_resource_name(),
            table_name=self.table_name,
            schema_name=self.schema,
        )

    @cached_property
    def big_query_connection_config(self) -> BigQueryConnectionConfig:
        return BigQueryConnectionConfig()  # type: ignore[call-arg]  # retrieves env vars


class BigQueryConnectionConfig(BaseSettings):
    """Environment variables for BigQuery connection.
    These are injected in via CI, but when running locally, you may use your own credentials.
    GOOGLE_APPLICATION_CREDENTIALS must be kept secret
    """

    GE_TEST_GCP_PROJECT: str
    GE_TEST_BIGQUERY_DATASET: str
    GOOGLE_APPLICATION_CREDENTIALS: str

    @property
    def connection_string(self) -> str:
        return f"bigquery://{self.GE_TEST_GCP_PROJECT}/{self.GE_TEST_BIGQUERY_DATASET}?credentials_path={self.GOOGLE_APPLICATION_CREDENTIALS}"
