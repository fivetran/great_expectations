from random import randint
from typing import TYPE_CHECKING, Dict, List, TypeVar, Union

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

if TYPE_CHECKING:
    from great_expectations.compatibility.snowflake import SnowflakeType

_SnowflakeType = TypeVar("_SnowflakeType")


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
        self, data: pd.DataFrame, request: pytest.FixtureRequest
    ) -> BatchTestSetup:
        return SnowflakeBatchTestSetup(
            data=data,
            config=self,
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
    ) -> None:
        self.table_name = f"snowflake_expectation_test_table_{randint(0, 1000000)}"
        self.snowflake_connection_config = SnowflakeConnectionConfig()  # type: ignore[call-arg]  # retrieves env vars
        self.engine = create_engine(url=self.snowflake_connection_config.connection_string)
        self.metadata = MetaData()
        self.table: Union[Table, None] = None
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
        column_types: Dict[str, SnowflakeType] = self.get_column_types()
        columns: List[Column] = [
            Column(name, column_type) for name, column_type in column_types.items()
        ]
        self.table = Table(
            self.table_name,
            self.metadata,
            *columns,
            schema=self.snowflake_connection_config.SNOWFLAKE_SCHEMA,
        )
        self.metadata.create_all(self.engine)
        with self.engine.connect() as conn:
            # pd.DataFrame(...).to_dict("index") returns a dictionary where the keys are the row
            # index and the values are a dict of column names mapped to column values.
            # Then we pass that list of dicts in as parameters to our insert statement.
            #   INSERT INTO test_table (my_int_column, my_str_column) VALUES (?, ?)
            #   [...] [('1', 'foo'), ('2', 'bar')]
            conn.execute(insert(self.table), list(self.data.to_dict("index").values()))
            conn.commit()

    @override
    def teardown(self) -> None:
        if self.table is not None:
            self.table.drop(self.engine)

    def get_column_types(self) -> Dict[str, _SnowflakeType]:
        if self.config.column_types is None:
            raise NotImplementedError("Column inference not implemented")
        else:
            return self.config.column_types
