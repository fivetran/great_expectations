import pathlib
from typing import Mapping, Optional

import pandas as pd
import pytest

from great_expectations.compatibility.typing_extensions import override
from great_expectations.data_context import AbstractDataContext
from great_expectations.datasource.fluent.sql_datasource import TableAsset
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)
from tests.integration.test_utils.data_source_config.sql import SQLBatchTestSetup


class SqliteDatasourceTestConfig(DataSourceTestConfig):
    @property
    @override
    def label(self) -> str:
        return "sqlite"

    @property
    @override
    def pytest_mark(self) -> pytest.MarkDecorator:
        return pytest.mark.sqlite

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
    ) -> BatchTestSetup:
        tmp_path = request.getfixturevalue("tmp_path")
        assert isinstance(tmp_path, pathlib.Path)

        return SqliteBatchTestSetup(
            data=data,
            config=self,
            base_dir=tmp_path,
            extra_data=extra_data,
            table_name=self.table_name,
            context=context,
        )


class SqliteBatchTestSetup(SQLBatchTestSetup[SqliteDatasourceTestConfig]):
    def __init__(
        self,
        data: pd.DataFrame,
        config: SqliteDatasourceTestConfig,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
        base_dir: pathlib.Path,
        table_name: Optional[str] = None,
    ) -> None:
        self._base_dir = base_dir
        super().__init__(
            config=config, data=data, extra_data=extra_data, table_name=table_name, context=context
        )

    @property
    @override
    def connection_string(self) -> str:
        return f"sqlite:///{self.db_file_path}"

    @property
    @override
    def use_schema(self) -> bool:
        return False

    @property
    def db_file_path(self) -> pathlib.Path:
        return self._base_dir / "database.db"

    @override
    def make_asset(self) -> TableAsset:
        return self.context.data_sources.add_sqlite(
            name=self._random_resource_name(),
            connection_string=self.connection_string,
        ).add_table_asset(name=self._random_resource_name(), table_name=self.table_name)
