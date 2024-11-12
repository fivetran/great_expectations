from typing import Dict, Mapping, Type

import pandas as pd
import pytest

from great_expectations.compatibility.sqlalchemy import TypeEngine, sqltypes
from great_expectations.compatibility.typing_extensions import override
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)
from tests.integration.test_utils.data_source_config.sql import SQLBatchTestSetup


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
    ) -> BatchTestSetup:
        return DatabricksBatchTestSetup(
            data=data,
            config=self,
            extra_data=extra_data,
        )


class DatabricksBatchTestSetup(SQLBatchTestSetup[DatabricksDatasourceTestConfig]):
    @property
    @override
    def connection_string(self) -> str:
        return (
            "databricks://token:"
            "${DATABRICKS_TOKEN}@${DATABRICKS_HOST}:443"
            "?http_path=${DATABRICKS_HTTP_PATH}&catalog=ci&schema=" + self.schema
        )

    @property
    @override
    def schema(self) -> str:
        return "py310_i01ec4622764c4ab8b44f1ce35e713be9"

    @property
    @override
    def inferrable_types_lookup(self) -> Dict[Type, TypeEngine]:
        overrides = {
            str: sqltypes.VARCHAR(255),  # mysql requires a length for VARCHAR
        }
        return super().inferrable_types_lookup | overrides

    @override
    def make_batch(self) -> Batch:
        name = self._random_resource_name()
        return (
            self.context.data_sources.add_databricks_sql(
                name=name,
                connection_string=self.connection_string,
            )
            .add_table_asset(
                name=name,
                table_name=self.table_name,
                schema_name=self.schema,
            )
            .add_batch_definition_whole_table(name=name)
            .get_batch()
        )
