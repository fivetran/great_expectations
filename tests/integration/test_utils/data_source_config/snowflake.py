from random import randint
from typing import Any, Mapping, Union

import pandas as pd
import pytest

from great_expectations.compatibility.pydantic import BaseSettings
from great_expectations.compatibility.sqlalchemy import (
    Column,
    MetaData,
    Table,
    create_engine,
    insert,
)
from great_expectations.compatibility.typing_extensions import override
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)


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


class SnowflakeBatchTestSetup(BatchTestSetup[SnowflakeDatasourceTestConfig]):
    def __init__(
        self,
        config: SnowflakeDatasourceTestConfig,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
    ) -> None:
        self.table_name = f"snowflake_expectation_test_table_{randint(0, 1000000)}"
        self.snowflake_connection_config = SnowflakeConnectionConfig()  # type: ignore[call-arg]  # retrieves env vars
        self.engine = create_engine(url=self.snowflake_connection_config.connection_string)
        self.metadata = MetaData()
        self.tables: Union[list[Table], None] = None
        self.extra_data = extra_data
        super().__init__(config=config, data=data)

    @override
    def make_batch(self) -> Batch:
        name = self._random_resource_name()
        return (
            self._context.data_sources.add_snowflake(
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

    @override
    def setup(self) -> None:
        main_table = self._create_table(name=self.table_name, columns=self.get_column_types())
        extra_tables = {
            table_name: self._create_table(
                name=table_name,
                columns=self.get_extra_column_types(table_name),
            )
            for table_name in self.extra_data
        }
        self.tables = [main_table, *extra_tables.values()]

        self.metadata.create_all(self.engine)
        with self.engine.connect() as conn:
            # pd.DataFrame(...).to_dict("index") returns a dictionary where the keys are the row
            # index and the values are a dict of column names mapped to column values.
            # Then we pass that list of dicts in as parameters to our insert statement.
            #   INSERT INTO test_table (my_int_column, my_str_column) VALUES (?, ?)
            #   [...] [('1', 'foo'), ('2', 'bar')]
            with conn.begin():
                conn.execute(insert(main_table), list(self.data.to_dict("index").values()))
                for table_name, table_data in self.extra_data.items():
                    conn.execute(
                        insert(extra_tables[table_name]),
                        list(table_data.to_dict("index").values()),
                    )

    @override
    def teardown(self) -> None:
        if self.tables:
            for table in self.tables:
                table.drop(self.engine)

    def _create_table(self, name: str, columns: Mapping[str, Any]) -> Table:
        column_list: list[Column] = [
            Column(col_name, col_type) for col_name, col_type in columns.items()
        ]
        return Table(
            name,
            self.metadata,
            *column_list,
            schema=self.snowflake_connection_config.SNOWFLAKE_SCHEMA,
        )

    def get_column_types(self) -> Mapping[str, Any]:
        if self.config.column_types is None:
            return {}
        return self.config.column_types

    def get_extra_column_types(self, table_name: str) -> Mapping[str, Any]:
        extra_assets = self.config.extra_assets
        if not extra_assets:
            return {}
        else:
            return extra_assets[table_name]
