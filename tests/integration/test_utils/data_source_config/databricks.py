from __future__ import annotations

import datetime
import logging
from functools import cached_property
from typing import TYPE_CHECKING, Mapping, Optional

import numpy as np
import pytest

from great_expectations.compatibility.pydantic import BaseSettings
from great_expectations.compatibility.sqlalchemy import TextClause, insert, sqltypes
from great_expectations.compatibility.typing_extensions import override
from great_expectations.data_context import AbstractDataContext
from great_expectations.datasource.fluent.sql_datasource import TableAsset
from tests.integration.sql_session_manager import SessionSQLEngineManager
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)
from tests.integration.test_utils.data_source_config.sql import (
    InferrableTypesLookup,
    SQLBatchTestSetup,
)

if TYPE_CHECKING:
    import pandas as pd


class DatabricksDatasourceTestConfig(DataSourceTestConfig):
    @property
    @override
    def label(self) -> str:
        return "databricks"

    @property
    @override
    def pytest_mark(self) -> pytest.MarkDecorator:
        return pytest.mark.databricks

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
        engine_manager: Optional[SessionSQLEngineManager] = None,
    ) -> BatchTestSetup:
        return DatabricksBatchTestSetup(
            data=data,
            config=self,
            extra_data=extra_data,
            table_name=self.table_name,
            context=context,
            engine_manager=engine_manager,
        )


class DatabricksBatchTestSetup(SQLBatchTestSetup[DatabricksDatasourceTestConfig]):
    @property
    @override
    def connection_string(self) -> str:
        assert self.schema
        return self._databrics_connection_config.connection_string(self.schema)

    @property
    @override
    def use_schema(self) -> bool:
        return True

    @property
    @override
    def inferrable_types_lookup(self) -> InferrableTypesLookup:
        # databricks requires a length for VARCHAR
        overrides: InferrableTypesLookup = {
            str: sqltypes.VARCHAR(255),
        }
        return super().inferrable_types_lookup | overrides

    @cached_property
    def _databrics_connection_config(self) -> DatabricksConnectionConfig:
        return DatabricksConnectionConfig()  # type: ignore[call-arg]  # retrieves env vars

    @override
    def setup(self) -> None:
        """Override setup to add timestamp metadata for Databricks schemas."""
        logger = logging.getLogger(__name__)
        engine, cleanup = self._get_engine()

        with engine.connect() as conn, conn.begin():
            # create schema if needed - with timestamp metadata for Databricks
            if self.schema:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"CREATING SCHEMA {self.schema} with timestamp metadata")

                # Create schema with custom properties including timestamp
                conn.execute(
                    TextClause(
                        f"""
                    CREATE SCHEMA IF NOT EXISTS {self.schema}
                    WITH PROPERTIES (
                        'created_timestamp' = '{current_time}'
                    )
                    """
                    )
                )

            # create tables
            all_table_data = self._ensure_all_table_data_created()
            self.metadata.create_all(engine)

            # insert data
            for table_data in all_table_data:
                # pd.DataFrame(...).to_dict("index") returns a dictionary where the keys are the row
                # index and the values are a dict of column names mapped to column values.
                # Then we pass that list of dicts in as parameters to our insert statement.
                #   INSERT INTO test_table (my_int_column, my_str_column) VALUES (?, ?)
                #   [...] [('1', 'foo'), ('2', 'bar')]
                df = table_data.df.replace(np.nan, None)
                values = list(df.to_dict("index").values())
                conn.execute(insert(table_data.table), values)
        cleanup()

    @override
    def make_asset(self) -> TableAsset:
        return self.context.data_sources.add_databricks_sql(
            name=self._random_resource_name(),
            connection_string=self.connection_string,
        ).add_table_asset(
            name=self._random_resource_name(),
            table_name=self.table_name,
            schema_name=self.schema,
        )


class DatabricksConnectionConfig(BaseSettings):
    databricks_token: str
    databricks_host: str
    databricks_http_path: str

    def connection_string(self, schema: str) -> str:
        return (
            "databricks://token:"
            f"{self.databricks_token}@{self.databricks_host}:443"
            f"?http_path={self.databricks_http_path}&catalog=ci&schema={schema}"
        )
